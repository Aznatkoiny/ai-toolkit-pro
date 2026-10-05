# Catalog update log

## 2026-10-05

* **Weekly expedition landed**: weekly-2026-10-05 — 4 draft concepts under
  [/modern/](/modern/) (tool error text and agent recovery, cross-stream buffer
  lifetime, disaggregated serving and goodput, decision models for typed
  choice) from 4 primary sources dated 2026-09-28/29/30 and 2026-10-02/03, all
  re-fetched and re-read during the skeptic pass. Three areas are newly covered
  at draft tier: agent/tool-harness reliability, CUDA stream memory management,
  and non-generative classification. [Scope boundary](/foundations/scope-boundary.md)
  draft-coverage section updated.
* **Skeptic pass dropped the week's headline causal claim.** The tool-error-text
  source is titled "MCP Error Messages Written for Developers Hurt the Most
  Capable Agents Most", but its own released per-model data gives overall
  cause-only recovery rates of 0.597–0.647 across the five models tested, in
  which the highest and lowest both belong to mid-penalty models — so the
  0.181–0.694 penalty spread does not track any capability ordering derivable
  from the artifact. The draft keeps the robust result (the penalty is large,
  real and model-dependent) and records the capability framing as the authors'
  unverified interpretation. Two further overstatements were corrected before
  drafting: the decision-model probabilities are **not** calibrated (the source
  says so explicitly), and the disaggregated-serving TTFT regression was
  measured on a fabric that fails the post's own pre-flight gate.
* **Three candidate findings were rejected for duplication, and that is now a
  pattern worth a human decision.** 25 draft concepts sit unmerged across PRs
  #1 and #3–#8; only the 2026-08-17 expedition has ever been merged. Roughly 15
  of those 25 restate three meta-lessons — "a published number is unreliable",
  "an upgrade silently changes defaults", and "it did not crash so you think it
  worked". This week's release sweep (transformers v5.18.0's device-chosen flash
  kernel, vLLM v0.31.0's removals, the PEFT/transformers version coupling) landed
  squarely in those clusters and was dropped rather than written up. The
  selection bar used is in the PR body.
* **One in-flight draft is now contradicted by upstream.** vLLM v0.31.0
  (2026-10-02) removed online quantization from `--quantization fp8`, which
  bears directly on the unmerged draft `vllm-online-quantization` on PR #1. Not
  edited here — it is not on this branch, and amending another expedition's
  unmerged draft is outside this expedition's scope.
* **Sweep coverage was partial, and the gaps are the same ones as 2026-08-17
  plus two more.** The network egress policy again blocked `arxiv.org` and
  `huggingface.co` outright, and also every lab engineering blog on its own
  domain (`blog.vllm.ai`, `pytorch.org`, `keras.io`, `openai.com`, `ai.meta.com`,
  Google/DeepMind). `WebFetch` is subject to the same policy; `WebSearch`
  resolves server-side and was used for discovery only, never as evidence. The
  sweep therefore ran entirely on `git` and `raw.githubusercontent.com` against
  public repositories — which does reach the vLLM, Hugging Face and PyTorch blog
  *sources*, plus release history. Two consequences to record: (a) the
  `pytorch.org/blog` markdown is no longer in `pytorch/pytorch.github.io` and
  could not be located in any reachable repository, so two in-window PyTorch
  posts (a TLX jagged-flash-attention result and a Helion vLLM linear backend)
  were seen in search results but deliberately not written up; (b) **no
  open-weight licence could be verified at all**, because model cards live only
  on the blocked host — which directly limits the catalog's
  [open-weight model-selection signals](/modern/open-weight-model-selection-signals.md)
  draft and is flagged inside the decision-models draft as its blocking item.
* **Quiet in the places that are usually load-bearing**: `keras-team/keras` (no
  release since v3.12.4, 2026-07-29), `huggingface/accelerate` (nothing since
  v1.15.0), and `microsoft/qlib` — dormant, zero commits in the window, last
  release still v0.9.7 of 2025-08-15.

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
