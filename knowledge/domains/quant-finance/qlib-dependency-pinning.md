---
type: Decision Rule
title: "Pin qlib's dependencies yourself: the released package predates its own compatibility fixes"
description: >
  qlib's main branch caps mlflow below 3.13 and filelock below 3.30 because both break qlib's
  experiment tracking and forking. Those caps are in no release, and pip install pyqlib resolves to
  a tag that predates them, so a fresh environment can silently stop recording experiments. Pin the
  caps yourself or install from a pinned source commit.
tags: [quant-finance, qlib, dependencies, mlflow, experiment-tracking, reproducibility, packaging]
tier: frontier
applies_to:
  - standing up a new qlib environment for backtesting or factor research
  - debugging missing or empty qlib experiment records
  - deciding whether to depend on released qlib or a pinned source commit
status: draft
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
    resource: https://github.com/microsoft/qlib/commit/be72549
    title: "microsoft/qlib commit be72549 — ci: pin GitHub Actions to full-length commit SHAs (#2318)"
    author: qlib contributors
    last_modified: 2026-09-16
---

# Rule

**When you create a qlib environment, add `mlflow<3.13` and `filelock>=3.16.0,<3.30` to your own
constraints rather than relying on what `pip install pyqlib` resolves.** qlib's `main` now carries
both caps, with the reasons stated verbatim in `pyproject.toml`: *"Qlib's filesystem tracking
backend is disabled by default in MLflow 3.13"* above `"mlflow<3.13"`, and *"filelock 3.30 rejects
forks while another thread changes lock descriptor ownership"* above
`"filelock>=3.16.0,<3.30"`.[^qlib-deps]

**Those caps are on `main` only and reach no installable release.** The newest qlib tag is `v0.9.7`,
dated 2025-08-15 — more than thirteen months before the caps were written — and it is what
`pip install pyqlib` resolves to.[^qlib-deps] Per
[release-containment discipline](/modern/release-containment-discipline.md), a fix visible on
`main` is not a fix you have.

**The failure mode is silent, which is why this is a setup-time rule and not a debugging tip.** A
disabled tracking backend does not raise at import or at `qrun` invocation; the run proceeds and the
experiment record is simply not persisted. **For the
[qrun workflow](qlib-qrun-workflow.md) this is the worst possible failure: the backtest still
produces numbers, but the provenance that makes them comparable across runs is gone** — and the
[leakage and evaluation discipline](leakage-and-evaluation.md) concept's requirement to report
across multiple runs depends on exactly that record. **If you have qlib experiment directories that
are unexpectedly empty, check your installed MLflow version before looking anywhere else.**

**The same commit adds three further environment constraints** worth copying into a reproducible
setup: `"osqp==1.0.5; sys_platform == 'win32' and python_version == '3.8'"`,
`"fastjsonschema<2.22; python_version < '3.10'"` — under the comment *"fastjsonschema 2.22 uses
Python 3.10 type syntax without declaring the requirement"* — and `"tomli; python_version <
'3.11'"` under `dev`.[^qlib-deps]

**Treat upstream qlib as low-cadence and plan accordingly.** Both commits in the 2026-09-14..21
window are CI and packaging work — the dependency caps above and *"ci: pin GitHub Actions to
full-length commit SHAs (#2318)"* — with no functional change.[^qlib-deps][^qlib-ci-sha] **For a
production dependency, budget for vendoring or forking rather than waiting on an upstream release**;
the observed gap between a compatibility fix landing and a tag carrying it is, on this evidence, open
ended.

# Open questions

- **The root cause is quoted from qlib, not verified against MLflow.** That MLflow 3.13 disables the
  filesystem tracking backend by default is qlib's own comment; MLflow's release notes were not
  reachable in this expedition's network environment. The precise symptom — silently unrecorded runs
  versus an error — is **inferred** from the phrase "disabled by default" and is not stated by any
  source read here. Verify against MLflow directly before relying on the symptom description.
- No source establishes when, or whether, a qlib release will carry these caps. The short
  `stale_after` reflects that a single new tag would resolve the whole concept.
- Two commits in one week is a thin basis for the maintenance-cadence claim. It is consistent with
  the last functional commit observed before them (2026-07-23), but this expedition did not audit
  the full commit history, and low activity is not the same as abandonment.
- Whether qlib's RL execution paradigm or its other optional extras carry further unpinned
  incompatibilities was not checked.

[^qlib-deps]: microsoft/qlib commit f431588, "ci: fix dependency compatibility failures (#2308)", 2026-09-16 (source id: qlib-deps). All five pins and their comments were read verbatim from `pyproject.toml` at that SHA on 2026-09-21. `v0.9.7` (`da920b7f`) confirmed as the newest tag, and its 2025-08-15 date established during this expedition's sweep; non-containment of f431588 in `v0.9.7` was checked with `git merge-base --is-ancestor` during the sweep.
[^qlib-ci-sha]: microsoft/qlib commit be72549, "ci: pin GitHub Actions to full-length commit SHAs (#2318)", 2026-09-16 (source id: qlib-ci-sha). Cited only as the second of the two commits observed in the window; its own content (supply-chain pinning of Actions) carries no qlib-user consequence.
