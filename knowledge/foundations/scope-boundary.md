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

# Draft coverage (expedition weekly-2026-09-21 — unverified tier)

Four further areas gained DRAFT concepts, usable only WITH THEIR TIER STATED
(`Evidence: unverified`). All four are `frontier`:

- **Dependency and release engineering** — previously uncovered entirely; now
  [release-containment discipline](/modern/release-containment-discipline.md) (merged is
  not shipped; check ancestry, not dates) and its quant-finance instance,
  [qlib dependency pinning](/domains/quant-finance/qlib-dependency-pinning.md). The
  latter extends the existing quant-finance module rather than opening new ground.
- **Serving-benchmark methodology** — extends the inference-serving coverage opened on
  2026-08-17 with
  [serving-benchmark measurement windows](/modern/serving-benchmark-measurement-windows.md).
  Inference deployment more broadly still remains uncovered.
- **Adapter configuration mechanics**
  ([adapter target-matching](/modern/adapter-target-matching.md)). **This draft touches
  the LLM/foundation-model fine-tuning area listed as uncovered above, and the boundary
  above still governs:** LoRA/PEFT *methodology* — which rank, which modules are worth
  adapting, whether LoRA suits a task — remains an OUT-OF-SCOPE response. The draft
  covers only the mechanical check that a configured adapter attached to anything at
  all. The conflict is recorded inside the draft rather than resolved here, following
  the precedent set by
  [open-weight model-selection signals](/modern/open-weight-model-selection-signals.md).

This concept has a deliberately short `stale_after`: every expedition that
lands must revisit it and carve out what it now covers.
