# Catalog update log

## 2026-08-24

* **Weekly expedition landed**: weekly-2026-08-24 — 4 draft concepts under
  [/modern/](/modern/) (speculative drafting method selection, train-inference
  numerical mismatch, benchmark-optimization probes, late-interaction retrieval
  tradeoff) from 4 primary sources dated 2026-08-18/19/21/23, plus one release-notes
  corroboration. All four are `tier: frontier`: each rests on a single source, and
  every one of those sources is authored by a party with an interest in its result
  (AMD/Embedded LLM, the SkyRL authors, Hume AI, LightOn). Recorded in each draft.
* **Skeptic pass corrected one material error and flagged four unresolved conflicts.**
  The late-interaction draft originally asserted that its source published no
  head-to-head quality comparison; re-reading the source found a controlled
  LateOn-vs-DenseOn ablation over 13 NanoBEIR datasets, and the concept was rewritten
  around it — the mean gain (~1 NDCG@10 point) and, more usefully, the +6.8pp/−6.2pp
  per-dataset spread. Flagged and left unresolved: (1) the AMD post benchmarks DSpark
  while reporting a vLLM version that predates DSpark's landing; (2) that post's Main
  observations and Summary disagree on the gemma-4-26B-A4B-it Gemma 4 MTP maximum
  (2.74×/2.62× vs 2.83×); (3) the quoted token-pooling retention exceeds 100% without
  explanation; (4) the RL draft's corroborating third-party evidence (VeXact, Fireworks)
  is cited second-hand and was unreachable from this session.
* **One conflict with a stable concept recorded, not resolved**: the train-inference
  mismatch draft sits inside the reinforcement-learning area that the stable
  [scope boundary](/foundations/scope-boundary.md) lists as uncovered. The draft covers
  only the numerical integrity of an RL stack; RL methodology stays OUT-OF-SCOPE. The
  benchmark-optimization draft adds a precondition to the stable
  [evaluation protocol by size](/foundations/evaluation-protocol-by-size.md) — split
  strategy governs generalization only for data the model has not seen — which is an
  extension rather than a contradiction.
* **Sweep coverage was partial again, in the same way as 2026-08-17**: the session's
  network egress policy blocked `arxiv.org`, `huggingface.co`, `blog.vllm.ai`,
  `pytorch.org`, and every lab engineering blog probed, for both `curl` and the fetch
  tool. Reachable classes were `github.com` / `raw.githubusercontent.com` (which carry
  the vLLM and Hugging Face blog sources, and repository release notes) and web search
  for discovery only. The arXiv and Hugging Face model-card / daily-papers source
  classes named in the weekly playbook therefore went unswept for the second week
  running. Recorded so the gap is not mistaken for a quiet week — and noted as a
  standing constraint worth fixing at the environment level rather than re-discovering
  weekly.
* **Retrieval / embeddings is a newly opened area**; inference serving and evaluation
  methodology gained a second draft each. [Scope boundary](/foundations/scope-boundary.md)
  draft-coverage section updated.

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
