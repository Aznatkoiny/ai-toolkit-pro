# Catalog update log

## 2026-09-07

* **Weekly expedition landed**: weekly-2026-09-07 — 4 draft concepts under [/modern/](/modern/)
  ([silent training defects](/modern/silent-training-defects.md),
  [upgrade default re-derivation](/modern/upgrade-default-rederivation.md),
  [long-context SFT memory ladder](/modern/long-context-sft-memory-ladder.md),
  [retrieval eval and document length](/modern/retrieval-eval-document-length.md)) from 15 primary
  artifacts — commits, source files at pinned tags, and one blog post read from its GitHub source
  repository — all dated 2026-08-24 to 2026-09-04. Two of the four are class-induction concepts:
  several independent projects each supply one instance, and the general rule is the expedition's,
  not any source's.
* **Skeptic pass changed the output substantially.** One central claim was refuted outright and
  withdrawn: an earlier draft held that vLLM's `--performance-mode throughput` newly doubles the
  batch-size defaults and so compounds with the new ≥160 GiB tier — the doubling block is
  byte-identical at v0.27.0 and v0.28.0, so the release's only batch-sizing change is the tier
  itself. A second unsupported claim (that the PyTorch nccl2 default had been landed, reverted and
  re-landed) was cut for having no basis in the cited commit. Both withdrawals are recorded inside
  the affected concept's footnotes. Further corrections: a model-family list was re-attributed to
  the source that actually contains it; one instance in the silent-defects concept was swapped for a
  better-evidenced defect in the same commit (calibration sampling that ignored its own `seed`
  argument, 4.7 PPL spread); rung 1–3 measurements were re-attributed from Qwen3-8B to Qwen3-4B; and
  unevidenced author affiliations were dropped.
* **Both class-induction concepts were demoted from `modern-consensus` to `frontier`** during the
  skeptic pass. The catalog defines `modern-consensus` as multiple independent sources agreeing on a
  claim; these sources each attest a different instance and agree on nothing, so the tier did not
  fit. Recorded here because the demotion, not the evidence, is what changed.
* **A release-containment check was added and it changed the advice.** None of the five fixes behind
  [silent training defects](/modern/silent-training-defects.md) is in any tagged release as of
  2026-09-07, and the accelerate refusal that
  [the memory ladder](/modern/long-context-sft-memory-ladder.md) presents as a safety gate is absent
  from every accelerate release including the versions that guide itself requires.
* **Conflicts flagged, not resolved**: three of the four drafts record a conflict with the stable
  [scope boundary](/foundations/scope-boundary.md) — two against its fine-tuning exclusion, one
  against its statement that inference deployment remains uncovered. One internal contradiction in a
  cited source is flagged (SGLang tells users to unset an environment variable that another file at
  the same tag still requires). [Scope boundary](/foundations/scope-boundary.md) draft-coverage
  section updated.
* **Sweep coverage was partial, in the same way as 2026-08-17 and for the same reason.** The
  session's network egress policy blocked `arxiv.org`, `huggingface.co`, `pytorch.org`, every lab
  engineering blog, `openreview.net` and `*.github.io` outright. Reachable classes were GitHub
  (repository history, source files at pinned refs, and blog posts whose markdown lives in a GitHub
  repository) and web search, which returns titles and snippets that cannot be opened to verify.
  Consequences worth recording: **no arXiv paper was read this week**, and no benchmark number from
  any release-note body could be quoted verbatim, so all of them were dropped rather than softened —
  which is why [upgrade default re-derivation](/modern/upgrade-default-rederivation.md) carries no
  performance figures. Web search asserted several frontier-lab model releases in the window; not
  one could be corroborated from a reachable artifact, and they are recorded as unverified rumor
  rather than as events. The commissioned quant-finance domain produced nothing: `microsoft/qlib`
  has no commit in the window.

## 2026-08-17

* **Weekly expedition landed**: weekly-2026-08-17 — 3 draft concepts under
  [/modern/](/modern/) (published-result reproducibility, speculative-decoding
  concurrency dependence, open-weight model-selection signals) from 3 primary
  sources dated 2026-08-13/14/16 plus one repository-tag check. Skeptic pass
  corrected two overstatements (an organizer self-characterization stated as
  fact; a checkpoint-specific KV-dtype requirement generalized too far) and
  recorded one conflict with the stable
  [scope boundary](/foundations/scope-boundary.md) inside the affected draft.
  Two internal contradictions in cited sources are flagged, not resolved.
  [Scope boundary](/foundations/scope-boundary.md) draft-coverage section
  updated.
* **Sweep coverage was partial**: the session's network egress policy blocked
  `arxiv.org` and `huggingface.co` outright, so the arXiv and Hugging Face
  model-card/daily-papers source classes named in the weekly playbook could not
  be swept. Findings come from the reachable classes only — lab engineering
  blogs whose sources live in GitHub repositories, and load-bearing repository
  history. Recorded here so the gap is not mistaken for a quiet week.

## 2026-08-03

* **Expedition landed**: qlib-2026-08-03 — 6 draft concepts (4 under
  [/domains/quant-finance/](/domains/quant-finance/), 2 under
  [/modern/](/modern/)) from 71 sourced claims by 3 scouts; all 6 revised
  by adversarial skeptics (misquotes, overstated claims, and stale source
  metadata corrected against live sources); 10 draft eval-task specs saved
  to docs/plans for suite v2. Lead curation: one concept retyped away from
  Task Pairing (reserved for ch6 rows);
  [scope boundary](/foundations/scope-boundary.md) revised to record draft
  coverage.

* **Initialization**: Seeded 15 foundation concepts from the
  suite-validated dl-model-advisor v1 content (4 Task Pairings, 5 Decision
  Rules, 5 Architecture Patterns, 1 Scope Boundary). All
  machine-confirmed by process:forge-eval-capability-v1 (bare 0/20 →
  plugin 20/20, 2026-08-02); human review pending — see
  [index](/index.md).
* **Commissioned**: expedition #1 — quant-finance module distilled from
  [microsoft/qlib](https://github.com/microsoft/qlib).
