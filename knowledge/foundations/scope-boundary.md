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

# Draft coverage (expedition weekly-2026-08-10 — unverified tier)

LLM **inference and serving** has its first DRAFT concepts under
[/modern/](/modern/): online (load-time) quantization scheme selection and
its GPU-architecture gates, and vLLM's migration of optional integrations
to out-of-tree plugins. Two limits on this coverage, both deliberate:

- It is vLLM-specific and single-project (`tier: frontier`). Nothing here
  generalizes to other serving stacks, and no accuracy or throughput
  evidence was gathered.
- Both concepts describe `main`-branch behavior that reached no vLLM
  release as of 2026-08-10, so each carries an explicit version gate.

LLM *training* and *fine-tuning* remain uncovered, as listed above —
serving coverage does not touch that boundary.

This concept has a deliberately short `stale_after`: every expedition that
lands must revisit it and carve out what it now covers.
