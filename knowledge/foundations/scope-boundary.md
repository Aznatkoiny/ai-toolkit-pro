---
type: Scope Boundary
title: "Coverage boundary of the current catalog"
description: "What the catalog knowingly does not cover; drives the advisor's OUT-OF-SCOPE behavior."
tags: [scope, honesty]
tier: book-canon
sources:
  - id: dlwp2e-ch14
    resource: "../deep-learning-with-python/Deep_Learning_with_Python_Second_Editio (1).epub#OEBPS/Text/14.htm"
    title: "Deep Learning with Python 2E, chapter 14"
    author: F. Chollet
    last_modified: 2021-10-03
generated: {by: dl-model-advisor-pipeline/claude-fable-5, at: 2026-08-03T00:00:00Z}
verified:
  - {by: process:forge-eval-capability-v1, at: 2026-08-02T23:00:00Z}
status: stable
stale_after: 2026-12-01
---

# Boundary

Not covered by any stable concept as of 2026-08-03 (requests get the
canonical OUT-OF-SCOPE response, with any adjacent material explicitly
labeled as background):

- LLM / foundation-model fine-tuning (LoRA, PEFT, instruction tuning)
- Diffusion models and modern text-to-image systems
- Reinforcement learning (qlib's RL execution paradigm is MENTIONED in
  draft coverage below, but RL methodology itself remains uncovered)
- Graph neural networks
- Recommender systems / collaborative filtering

# Draft coverage (expedition qlib-2026-08-03 — unverified tier)

Quantitative-finance ML now has DRAFT concepts under
[/domains/quant-finance/](/domains/quant-finance/) and
[/modern/](/modern/): alpha-forecasting routing, leakage and evaluation
discipline, qlib model selection, the qrun workflow pattern, time-series
foundation models, and LLM-automated factor research. The advisor may use
them WITH THEIR TIER STATED (`Evidence: unverified`); confident, unhedged
guidance still requires promotion to stable.

# Draft coverage (expedition weekly-2026-08-17 — unverified tier)

Three further areas gained DRAFT concepts under [/modern/](/modern/), usable
only WITH THEIR TIER STATED (`Evidence: unverified`):

- **Evidence discipline for external literature** — how much weight a published
  benchmark claim may carry before it is reproduced
  ([published-result reproducibility](/modern/published-result-reproducibility.md)).
- **Inference serving / speculative decoding** — previously uncovered
  entirely; now one draft on the concurrency dependence of draft-length tuning
  ([speculative-decoding concurrency](/modern/speculative-decoding-concurrency.md)).
  Inference deployment more broadly remains uncovered.
- **Open-weight base-model selection and licensing**
  ([open-weight model-selection signals](/modern/open-weight-model-selection-signals.md)).
  This draft touches the LLM/foundation-model area listed as uncovered above.
  **The boundary above still governs:** fine-tuning *methodology* (LoRA, PEFT,
  instruction tuning) remains an OUT-OF-SCOPE response. The draft covers only
  the selection-and-licensing decision preceding that work, and the conflict is
  recorded inside the draft rather than resolved here.

# Draft coverage (expedition weekly-2026-09-07 — unverified tier)

Four further areas gained DRAFT concepts under [/modern/](/modern/), usable only WITH THEIR TIER
STATED (`Evidence: unverified`):

- **Verification discipline for your own training runs** — the class of stack defects that raise
  nothing and leave a normal-looking loss curve, and how to audit for them
  ([silent training defects](/modern/silent-training-defects.md)). Several of its instances sit
  inside the LLM fine-tuning area listed as uncovered above; **the boundary still governs** and
  fine-tuning *methodology* remains an OUT-OF-SCOPE response. The conflict is recorded inside the
  draft.
- **Inference-engine upgrade and default management**
  ([upgrade default re-derivation](/modern/upgrade-default-rederivation.md)). This narrows the
  sentence above stating that inference deployment remains uncovered: upgrade discipline now has a
  draft. Capacity planning, kernel selection and engine choice remain uncovered.
- **Long-context supervised fine-tuning on one node**
  ([long-context SFT memory ladder](/modern/long-context-sft-memory-ladder.md)). This is squarely a
  fine-tuning recipe and therefore inside the excluded area above; **the boundary still governs**,
  the conflict is recorded inside the draft, and confident guidance still requires promotion.
- **Retrieval and embedding-model evaluation** — previously uncovered entirely; now one draft on
  document-length caps as a confound in retriever comparisons
  ([retrieval eval and document length](/modern/retrieval-eval-document-length.md)). RAG system
  design remains uncovered.

This concept has a deliberately short `stale_after`: every expedition that
lands must revisit it and carve out what it now covers.
