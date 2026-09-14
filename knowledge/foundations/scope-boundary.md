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

# Draft coverage (expedition weekly-2026-09-14 — unverified tier)

Four further areas gained DRAFT concepts under [/modern/](/modern/), all at `frontier`
and usable only WITH THEIR TIER STATED (`Evidence: unverified`):

- **Correctness validation of distributed training** — previously uncovered; now one
  draft holding that a sharded run which does not crash is not thereby correct, and
  that gradients should be compared against a single-device reference
  ([sharded-training silent correctness](/modern/sharded-training-silent-correctness.md)).
  **This draft touches the LLM/foundation-model fine-tuning area listed as uncovered
  above.** The boundary still governs: fine-tuning *methodology* (LoRA, PEFT,
  instruction tuning) remains an OUT-OF-SCOPE response. The draft covers only whether
  a completed distributed run can be trusted, and the conflict is recorded inside it.
- **Performance attribution and profiling discipline** — previously uncovered; now one
  draft on establishing that a kernel or backend actually executed before crediting it
  with a speedup
  ([performance attribution discipline](/modern/performance-attribution-discipline.md)).
  Its evidence is drawn partly from fine-tuning runs and partly from serving-side
  kernel selection, both listed as uncovered; the conflict is recorded inside the draft
  and the boundary still governs both areas.
- **Agentic serving topology and routing** — extends the inference-serving opening made
  on 2026-08-17, which recorded that "inference deployment more broadly remains
  uncovered". That is now **partially** carved out: routing policy, PP/DCP topology
  choice, and capacity planning for multi-turn agent traffic have draft coverage
  ([agentic serving routing](/modern/agentic-serving-routing.md)). Inference deployment
  outside those three questions remains uncovered.
- **Upgrade and release-containment auditing** — previously uncovered; now one draft on
  bounding the blast radius of a version bump and verifying that a fix is contained in
  the tag being pinned ([upgrade blast radius](/modern/upgrade-blast-radius.md)). It
  touches both reinforcement learning (via a PPO-pipeline removal) and inference
  deployment; the boundary governs both and the conflict is recorded inside the draft.

**Still entirely uncovered**, by stable or draft concepts: diffusion models and
text-to-image systems, graph neural networks, recommender systems, and reinforcement-learning
methodology. No paper-derived concept entered the catalog on 2026-09-14 because the arXiv
and Hugging Face source classes were unreachable from that session; see
[the log](/log.md) — that is an access gap, not a coverage judgement.

This concept has a deliberately short `stale_after`: every expedition that
lands must revisit it and carve out what it now covers.
