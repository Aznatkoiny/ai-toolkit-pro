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

# Draft coverage (expedition weekly-2026-08-31 — unverified tier)

Three further areas gained DRAFT concepts under [/modern/](/modern/), usable only
WITH THEIR TIER STATED (`Evidence: unverified`):

- **Serving-stack upgrade and configuration discipline** — how inference-server
  defaults are selected from device memory and compute capability, and what changes
  silently on upgrade
  ([hardware-gated serving defaults](/modern/hardware-gated-serving-defaults.md)).
  **This draft conflicts with the sentence above** recording that "Inference
  deployment more broadly remains uncovered" for the 2026-08-17 expedition. **That
  boundary still governs:** general inference-deployment questions remain an
  OUT-OF-SCOPE response. The draft covers only which defaults to pin and how to read
  a serving benchmark, and the conflict is recorded inside the draft rather than
  resolved here.
- **Post-training quantization validation** — verifying that a calibration-based
  quantization run actually calibrated, rather than silently falling back to
  round-to-nearest
  ([quantization calibration silent no-op](/modern/quantization-calibration-silent-noop.md)).
  Quantization was not previously listed either as covered or as uncovered. It sits
  adjacent to the LLM/foundation-model fine-tuning exclusion above, which is
  unchanged: fine-tuning *methodology* remains OUT-OF-SCOPE.
- **Benchmark scores as a model-selection signal** — benchmark fitting, aggregation
  hiding slice variance, and single-reference metrics rewarding annotator orthography
  ([benchmark score as a selection signal](/modern/benchmark-score-as-selection-signal.md)).
  **Its evidence is drawn entirely from speech recognition, a modality no concept in
  this catalog covers** and which the
  [modality → architecture map](/foundations/modality-architecture-map.md) does not
  route. This draft does NOT open ASR coverage: speech-recognition modelling
  questions remain an OUT-OF-SCOPE response, and only the draft's eval-methodology
  claims are usable.

This concept has a deliberately short `stale_after`: every expedition that
lands must revisit it and carve out what it now covers.
