---
type: Decision Rule
title: "Pin qlib's dependencies yourself: the released package predates its own compatibility fixes"
description: >
  qlib's main branch caps mlflow below 3.13 and filelock below 3.30, but those caps are in no
  release and PyPI's pyqlib still declares them uncapped, so a fresh environment fails at the first
  qrun with an MLflow file-store exception. Choose deliberately between pinning the cap, setting
  MLFLOW_ALLOW_FILE_STORE=true, and migrating to a SQL tracking backend.
tags: [quant-finance, qlib, dependencies, mlflow, experiment-tracking, reproducibility, packaging]
tier: frontier
applies_to:
  - standing up a new qlib environment for backtesting or factor research
  - diagnosing an MLflow file-store exception raised from a qlib workflow
  - deciding whether to depend on released qlib or a pinned source commit
status: draft
# stale_after is +3 months rather than the default +6: the whole concept is a statement about a
# version gap that a single qlib release would close.
stale_after: 2026-12-21
generated:
  by: expedition/weekly-2026-09-21
  at: 2026-09-21T00:00:00Z
sources:
  - id: qlib-deps
    resource: https://github.com/microsoft/qlib/commit/f431588906e776123332a32bbf82b5f828006fda
    title: "microsoft/qlib commit f431588 — ci: fix dependency compatibility failures (#2308)"
    author: qlib contributors
    last_modified: 2026-09-16
  - id: qlib-ci-sha
    resource: https://github.com/microsoft/qlib/commit/be725493eb1a6bbb42bf11b37aa7669f59610ff1
    title: "microsoft/qlib commit be72549 — ci: pin GitHub Actions to full-length commit SHAs (#2318)"
    author: qlib contributors (Dan Fiedler)
    last_modified: 2026-09-16
  - id: pypi-pyqlib
    resource: https://pypi.org/pypi/pyqlib/json
    title: "PyPI JSON metadata for pyqlib (latest version and requires_dist)"
    author: PyPI / qlib maintainers
    last_modified: 2025-08-15
  - id: mlflow-3130
    resource: https://raw.githubusercontent.com/mlflow/mlflow/master/CHANGELOG.md
    title: "MLflow CHANGELOG, section 3.13.0 — Breaking Changes (#22773)"
    author: MLflow maintainers
    last_modified: 2026-05-29
  - id: mlflow-filestore
    resource: https://github.com/mlflow/mlflow/blob/v3.13.0/mlflow/store/tracking/file_store.py
    title: "mlflow FileStore.__init__ at tag v3.13.0 — MLFLOW_ALLOW_FILE_STORE guard"
    author: MLflow maintainers
    last_modified: 2026-05-29
---

# Rule

**When you create a qlib environment, decide explicitly how you will handle MLflow's file-store
removal rather than letting `pip` choose for you.** qlib's `main` caps two dependencies, with the
reasons stated verbatim in `pyproject.toml`: *"Qlib's filesystem tracking backend is disabled by
default in MLflow 3.13"* above `"mlflow<3.13"`, and *"filelock 3.30 rejects forks while another
thread changes lock descriptor ownership"* above `"filelock>=3.16.0,<3.30"`.[^qlib-deps]

**Those caps are on `main` only and reach no installable release.** The newest qlib tag is `v0.9.7`
(2025-08-15), which predates the caps by over a year.[^qlib-deps] **PyPI's newest `pyqlib` is also
0.9.7, uploaded 2025-08-15, declaring `requires_dist` of `mlflow` and `filelock>=3.16.0` with no
upper bound.**[^pypi-pyqlib] Per
[release-containment discipline](/modern/release-containment-discipline.md), a fix visible on
`main` is not a fix you have.

**The failure is loud, immediate, and has three remedies — pinning is only one of them.** MLflow
3.13.0 (2026-05-29) made this a breaking change: *"Pointing the tracking or model registry store at
a local file-system path now raises an error by default; set `MLFLOW_ALLOW_FILE_STORE=true` to keep
using a file-based store."*[^mlflow-3130] `FileStore.__init__` raises `MlflowException` unless that
variable is set, and the message names the fix — the backend *"is in maintenance mode"*, callers
should *"migrate to a database backend (e.g., 'sqlite:///mlflow.db')"*, and *"The `mlflow
migrate-filestore` tool migrates your existing data losslessly."*[^mlflow-filestore] **qlib takes
exactly this path**: its default `exp_manager` URI is `"file:" + str(Path(os.getcwd()).resolve() /
"mlruns")`.[^qlib-deps] So a fresh `pip install pyqlib` against current MLflow fails at the first
`qrun`, with a traceback that explains itself. Choose deliberately:

1. **Cap `mlflow<3.13`** — freezes today's behavior, and freezes you out of MLflow indefinitely.
2. **Set `MLFLOW_ALLOW_FILE_STORE=true`** — keeps the file store on current MLflow, one variable,
   no pin.[^mlflow-3130]
3. **Run `mlflow migrate-filestore` and move to a SQL backend** — the only option that is not a
   dead end, and the one MLflow itself recommends.[^mlflow-filestore]

**This matters for the catalog's qlib guidance specifically.** The
[qrun workflow](qlib-qrun-workflow.md) depends on the experiment-tracking layer, and the
[leakage and evaluation discipline](leakage-and-evaluation.md) concept's requirement to report
across multiple runs depends on those records existing. **Because the failure raises rather than
passing silently, this is a setup-time decision and not a silent-corruption risk** — you will know
immediately, and the cost of getting it wrong is a blocked run, not a misleading backtest.

**Also cap `filelock<3.30` if you fork workers.** qlib's CI constraints file gives a fuller
rationale than `pyproject.toml` does — *"New fork-safety checks race with the threaded DataQueue
producer"*.[^qlib-deps] This expedition did not reproduce that race; see open questions.

**The same commit adds or tightens six further constraints.** Beyond the two above:
`"osqp==1.0.5; sys_platform == 'win32' and python_version == '3.8'"`,
`"fastjsonschema<2.22; python_version < '3.10'"` (*"fastjsonschema 2.22 uses Python 3.10 type
syntax without declaring the requirement"*), `"tomli; python_version < '3.11'"` under `dev`,
`"black<26.1"` under lint, `"lxml<6.1.3"` under test (*"Avoid source builds requiring external
libxml2 headers on Windows"*), and — the most user-facing of them — `"plotly<7"` under the
`analysis` extra, because *"Qlib still imports figure_factory.create_distplot, removed in Plotly
7."*[^qlib-deps] **That last one is a genuine `ImportError` in qlib's analysis extra**, and it is
subject to the same release gap as the MLflow cap.

**Treat upstream qlib as low-cadence and plan accordingly.** Both commits in the 2026-09-14..21
window are CI and packaging work — the dependency caps above and *"ci: pin GitHub Actions to
full-length commit SHAs (#2318)"* — with no functional change.[^qlib-deps][^qlib-ci-sha] **For a
production dependency, budget for vendoring or forking rather than waiting on an upstream release**;
the observed gap between a compatibility fix landing and a tag carrying it is, on this evidence,
open ended.

# Open questions

- **The filelock claim is qlib's, not reproduced here.** That filelock 3.30's fork-safety checks
  race with qlib's threaded `DataQueue` producer is stated in qlib's own CI constraints file; this
  expedition did not construct the race or confirm the failure mode.
- No source establishes when, or whether, a qlib release will carry these caps. The short
  `stale_after` reflects that a single new tag would resolve most of this concept.
- Two commits in one week is a thin basis for the maintenance-cadence claim. It is consistent with
  the last functional commit observed before them (2026-07-23, `feat(config): add explicit
  validation for required configuration fields`), but this expedition did not audit the full commit
  history, and low activity is not the same as abandonment.
- Whether qlib's RL execution paradigm or its other optional extras carry further unpinned
  incompatibilities was not checked beyond the `pyproject.toml` read above.

# Skeptic note — a corrected diagnosis

An earlier version of this draft asserted that the MLflow cap protected against *silent* loss of
experiment records, and excused not checking MLflow directly on the grounds that its release notes
were unreachable in this expedition's network environment. **Both were wrong.** MLflow's changelog
is reachable at `raw.githubusercontent.com`, and it documents a raised error rather than a silent
disable. The action (pin deliberately) survived; the diagnosis, the urgency framing, and a
now-deleted debugging tip about "unexpectedly empty experiment directories" did not. Recorded here
because the original error — inferring a failure mode from the phrase "disabled by default" instead
of reading the source — is the kind this catalog exists to catch.

[^qlib-deps]: microsoft/qlib commit f431588, "ci: fix dependency compatibility failures (#2308)", 2026-09-16 (source id: qlib-deps). All eight pins and their comments were read verbatim from `pyproject.toml` at that SHA on 2026-09-21; the `DataQueue` rationale is from `.github/ci/constraints.txt` added by the same commit. The default tracking URI `"file:" + str(Path(os.getcwd()).resolve() / "mlruns")` is at `qlib/config.py:35` at that SHA. `v0.9.7` (`da920b7f`) confirmed as the newest tag and non-containment of f431588 checked with `git merge-base --is-ancestor` during the sweep and re-checked in the skeptic pass.
[^qlib-ci-sha]: microsoft/qlib commit be725493eb1a6bbb42bf11b37aa7669f59610ff1, "ci: pin GitHub Actions to full-length commit SHAs (#2318)", 2026-09-16 (source id: qlib-ci-sha). Cited only as the second of the two commits observed in the window; its own content carries no qlib-user consequence.
[^pypi-pyqlib]: PyPI JSON metadata for `pyqlib` (source id: pypi-pyqlib), read 2026-09-21. `info.version` is `0.9.7`, uploaded 2025-08-15T09:51:02; `info.requires_dist` contains `mlflow` and `filelock>=3.16.0`, both without an upper bound. Cited separately from the git tag listing because tag state does not establish distribution state.
[^mlflow-3130]: MLflow `CHANGELOG.md`, section `## 3.13.0 (2026-05-29)`, Breaking Changes (source id: mlflow-3130), read 2026-09-21. The quoted sentence and the `MLFLOW_ALLOW_FILE_STORE=true` opt-out are attributed there to #22773.
[^mlflow-filestore]: mlflow `mlflow/store/tracking/file_store.py` at tag `v3.13.0` (source id: mlflow-filestore), read 2026-09-21. `FileStore.__init__` raises `MlflowException` when `MLFLOW_ALLOW_FILE_STORE.get()` is false; the quoted phrases are from that exception message.
