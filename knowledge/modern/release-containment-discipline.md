---
type: Decision Rule
title: "Merged is not shipped: establish release containment by ancestry, not by date"
description: >
  A change's merge date tells you nothing about which installable version contains it, because
  release branches are cut early and take selective cherry-picks, and published tags can lag a
  project's own known-broken dependency set by months. Before you plan around a feature or a fix,
  check that the commit is an ancestor of the tag you will actually install.
tags: [dependencies, release-engineering, versioning, migration, supply-chain, reproducibility]
# skeptic 2026-09-21: downgraded from modern-consensus. No cited source STATES this rule —
# all five are primary artifacts from which one observer induced it — and the instances are
# not independent (2x vLLM, 2x Hugging Face, and the TRL post itself runs transformers + vLLM).
tier: frontier
applies_to:
  - reading a blog post, release note, or paper that says a feature "landed" or "is available"
  - pinning a dependency version for a training or serving stack
  - deciding whether an upstream fix reaches you by upgrading, or requires a source install
status: draft
stale_after: 2027-03-21
generated:
  by: expedition/weekly-2026-09-21
  at: 2026-09-21T00:00:00Z
sources:
  - id: vllm-tags
    resource: https://github.com/vllm-project/vllm/releases/tag/v0.30.0rc2
    title: "vllm-project/vllm tag v0.30.0rc2 (release-candidate line for v0.30.0)"
    author: vLLM contributors
    last_modified: 2026-09-18
  - id: vllm-humming
    resource: https://github.com/vllm-project/vllm/commit/7d99c2c4fd61cdeebd29cc7b60584bad10d1ef99
    title: "vllm commit 7d99c2c — [Feature][Humming] Humming feature integration (#56685)"
    author: vLLM contributors
    last_modified: 2026-09-20
  - id: qlib-deps
    resource: https://github.com/microsoft/qlib/commit/f431588906e776123332a32bbf82b5f828006fda
    title: "microsoft/qlib commit f431588 — ci: fix dependency compatibility failures (#2308)"
    author: qlib contributors
    last_modified: 2026-09-16
  - id: tf-mask
    resource: https://github.com/huggingface/transformers/commit/d65fdc5f99b0c23f268c0d2cbe120b2375cc344a
    title: "transformers commit d65fdc5 — [generate] Drop attention mask early without padding (#48814)"
    author: Hugging Face contributors
    last_modified: 2026-09-15
  - id: trl-asyncgrpo
    resource: https://github.com/huggingface/blog/blob/375ec0565204b6acc51675afe10571e4c9688bfd/asyncgrpo-lora-hfjobs.md
    title: "Scaling Async GRPO with LoRA on HF Jobs (source of huggingface.co/blog/asyncgrpo-lora-hfjobs)"
    author: Hugging Face
    last_modified: 2026-09-14
  - id: pypi-pyqlib
    resource: https://pypi.org/pypi/pyqlib/json
    title: "PyPI JSON metadata for pyqlib (latest version and requires_dist)"
    author: PyPI / qlib maintainers
    last_modified: 2025-08-15
---

# Rule

**Never infer "I can install this" from "this was merged". Establish containment against the exact
tag you will install, with an ancestry check (`git merge-base --is-ancestor <sha> <tag>`, or
`git tag --contains <sha>`), and record the answer next to the version you pin.** Merge date and
release membership are independent facts, and in the week of 2026-09-14 the gap between them bit
four separate projects across three organizations (vLLM, Hugging Face, Microsoft) inside a single
week.

**Release branches are cut early and then diverge, so "merged after the cut" means "not in that
release".** vLLM's `v0.30.0` line was branched at commit `f2aad6aa` (2026-09-15) and is not an
ancestor of `main`; the branch takes selective cherry-picks rather than tracking `main`.[^vllm-tags]
**Commits on `main` that are not ancestors of `f2aad6aa`** — among them the Humming
quantization-kernel integration (#56685, 2026-09-20) — are therefore in no tag at all, and reach
users only via a later release or an explicit cherry-pick.[^vllm-humming][^vllm-tags] **The boundary
is an ancestry relation, not a date:** commits merged later on 2026-09-15, after the 20:36 UTC cut,
are excluded too. **As of 2026-09-21 no stable `v0.30.0` exists:
the newest stable tag is `v0.29.0` and the `v0.30.0` line is `rc1`/`rc2` only.**[^vllm-tags] A
reader who saw "#56685 merged" and planned a deployment on "the next vLLM release" would be wrong
twice over.

**A project's published release can lag its own known-broken dependency set indefinitely.** qlib's
`main` now caps two dependencies with reasons given verbatim in `pyproject.toml`: `"mlflow<3.13"`
under the comment *"Qlib's filesystem tracking backend is disabled by default in MLflow 3.13"*, and
`"filelock>=3.16.0,<3.30"` under *"filelock 3.30 rejects forks while another thread changes lock
descriptor ownership"*.[^qlib-deps] Those caps are on `main` only. The newest qlib tag is `v0.9.7`,
which predates the caps by over a year.[^qlib-deps] **PyPI's newest `pyqlib` is also 0.9.7, uploaded
2025-08-15, declaring `requires_dist` of `mlflow` and `filelock>=3.16.0` with no upper
bound**[^pypi-pyqlib] — so a fresh install today gets the *old*, uncapped constraints and may
silently resolve to a dependency the project itself has already declared incompatible. **Note that
the tag listing alone would not have established this**: a git tag and a published distribution are
independent facts, which is this concept's own thesis applied to itself. **The dependency resolves
without complaint at install time and the breakage surfaces later, at first use** — here as a raised
`MlflowException` rather than silent corruption. See
[qlib dependency pinning](/domains/quant-finance/qlib-dependency-pinning.md) for the qlib-specific
gate and its three remedies.

**Breaking changes are visible on `main` before any release carries them — which is your migration
window, not your upgrade signal.** `transformers` merged a change on 2026-09-15 that sets
`model_kwargs["attention_mask"]` to `None` for decoder-only models whose forward accepts a mask,
when that mask is all ones — i.e. for unpadded input.[^tf-mask] At the time of writing it is
contained in no tag; the newest is `v5.17.0` (commit `856157a2`).[^tf-mask] **This is the weakest
of the instances here and is labeled as such: `v5.17.0` was cut on 2026-09-09, before the commit
merged, so the gap is merely "newer than the last tag" rather than exclusion from a release branch
that was cut and then kept moving.** **Read that as time to audit, not as permission to relax:** the
change is queued, and the correct response is to make downstream code `None`-safe before the
upgrade rather than after it.

**Treat a version number in prose as a claim to check, not a fact.** Hugging Face's own async-GRPO
post states its LoRA path *"ships with TRL v1.14"*, and its references say PR #7017 was *"released
in TRL v1.14"*.[^trl-asyncgrpo] As of 2026-09-21 no `v1.14` tag exists in `huggingface/trl` and
PyPI's newest `trl` is `1.13.0`.[^trl-asyncgrpo] **The post is candid that the numbers came from a
branch — it states *"We ran the PR branch at the time"* — so the defect is narrow and specific: the
version number, not the methodology.**[^trl-asyncgrpo] **A version named in prose is the version the
author expected to cut, and a cut can slip after publication. Check the tag, not the sentence.**

**Practical procedure.** For every upstream change you depend on, record three fields rather than
one: the commit SHA, the first tag that contains it (or `none`), and whether that tag is stable or
a release candidate. A dependency pinned to a stable tag whose fix lives only on `main` is a
decision to make deliberately — vendor the patch, install from source at a pinned SHA, or accept
the bug — not a state to discover in production. This extends the evidence discipline in
[published-result reproducibility](published-result-reproducibility.md) from *results* to
*availability*: both are claims that decay between publication and your environment.

# Open questions

- The five instances here were all found in a single 7-day window, which argues the pattern is
  common but does not measure how common. No source quantifies how often release-branch cherry-picks
  do eventually pick up a post-cut commit, so "not in the rc" is not proof of "not in the release".
- **The five instances are not five independent observations.** Two are vLLM, two are Hugging Face
  (`transformers`, `trl`), and the TRL post itself runs on `transformers` and vLLM. They are one
  interlocking stack observed once, not a survey — which is why the tier is `frontier`. **No cited
  source states this rule**; all five are primary artifacts from which this expedition induced it.
  A reader should weight it as one observer's generalization, not as corroborated practice.
- Release-engineering conventions differ per project (vLLM cuts an rc branch; qlib tags rarely;
  `transformers` tags frequently). This concept gives a procedure, not a per-project model, and does
  not establish which convention a given project follows.
- Whether the qlib `main` caps are correct — i.e. whether MLflow 3.13 in fact disables that backend
  by default — is **not** established here. The claim is quoted from qlib's own comment; MLflow's
  release notes were not reachable in this expedition's network environment. See the qlib concept's
  open questions.

[^vllm-tags]: vllm-project/vllm tags (source id: vllm-tags). Verified by `git ls-remote --tags` on 2026-09-21: `v0.29.0` → `98dff2a8` is the newest stable tag, and the `v0.30.0` line exists only as `v0.30.0rc1` (`a00a3544`) and `v0.30.0rc2` (`fa6ff060`), with no stable `v0.30.0`. The branch-point commit `f2aad6aa` (2026-09-15 20:36:51 +0000) and the non-ancestry of `v0.30.0rc2` with respect to `origin/main` were established by `git merge-base` on a clone during this expedition's sweep and independently re-derived by the skeptic pass on 2026-09-21. The cherry-pick characterization rests on `git rev-list --count origin/main..fa6ff060` = 9 against 275 the other way, with the nine rc-only commits landing in two identically-timestamped batches (2026-09-17, 2026-09-18) — consistent with cherry-pick batches rather than merges from `main`. Note `v0.29.1rc0` (2026-09-12) also exists; it is a release candidate, so `v0.29.0` remains the newest *stable* tag.
[^vllm-humming]: vllm-project/vllm commit 7d99c2c, "[Feature][Humming] Humming feature integration (#56685)", 2026-09-20 (source id: vllm-humming). `git tag --contains` returned empty during the sweep and on skeptic re-check, 2026-09-21. The diff spans MoE kernels and `kernels/linear/mixed_precision/`, `mxfp4/` and `mxfp6/`, so it is a quantization-kernel-backend integration rather than an MoE-only change.
[^qlib-deps]: microsoft/qlib commit f431588, "ci: fix dependency compatibility failures (#2308)", 2026-09-16 (source id: qlib-deps). The two pins and their comments were read verbatim from `pyproject.toml` at that SHA on 2026-09-21. `v0.9.7` (`da920b7f`) confirmed as the newest tag by `git ls-remote --tags` on 2026-09-21.
[^pypi-pyqlib]: PyPI JSON metadata for `pyqlib` (source id: pypi-pyqlib), read 2026-09-21. `info.version` is `0.9.7`; `info.requires_dist` contains `mlflow` and `filelock>=3.16.0`, both without an upper bound; the 0.9.7 files were uploaded 2025-08-15. Cited as a source separate from the git tag listing precisely because tag state does not establish distribution state.
[^tf-mask]: huggingface/transformers commit d65fdc5, "[generate] Drop attention mask early without padding (#48814)", 2026-09-15 (source id: tf-mask). The code block setting `model_kwargs["attention_mask"] = None` is in `src/transformers/generation/utils.py` at that SHA, guarded by a three-way condition — `not self.config.is_encoder_decoder and accepts_attention_mask and (model_kwargs["attention_mask"] == 1).all()` — so encoder-decoder models and models whose forward does not accept a mask are excluded. `v5.17.0` (peeled commit `856157a2`) confirmed as the newest tag by `git ls-remote --tags` on 2026-09-21; containment checked by `git tag --contains` during the sweep, which returned empty.
[^trl-asyncgrpo]: Hugging Face blog, "Scaling Async GRPO with LoRA on HF Jobs" (source id: trl-asyncgrpo), read at repo commit 375ec056, dated 2026-09-14. The "ships with TRL v1.14", "released in TRL v1.14", and "We ran the PR branch at the time" phrasings are all the post's, verified verbatim at that commit by the skeptic pass on 2026-09-21. Absence of a `v1.14` tag confirmed by `git ls-remote --tags https://github.com/huggingface/trl.git` during the sweep; newest tag `v1.13.0`. PyPI's newest `trl` confirmed as `1.13.0` on 2026-09-21.
