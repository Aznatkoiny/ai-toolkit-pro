---
okf_version: "0.2"
---

# dl-model-advisor knowledge catalog

The knowledge layer behind the dl-model-advisor plugin. Concepts carry OKF
provenance (`sources`), trust (`generated`/`verified`), and lifecycle
(`status`/`stale_after`). The advisor cites concept IDs; evidence tiers in
its plans derive from the `verified` entries here.

# Foundations (book canon — DLwP-2E, 2021)

* [Modality → architecture map](/foundations/modality-architecture-map.md) - routes data modality to architecture family
* [Text ratio rule](/foundations/text-ratio-rule.md) - the 1,500 samples/word threshold
* [Image data-size ladder](/foundations/image-data-size-ladder.md) - pretrained vs from-scratch by dataset size
* [Evaluation protocol by size](/foundations/evaluation-protocol-by-size.md) - holdout vs K-fold vs iterated K-fold
* [Universal workflow](/foundations/universal-workflow.md) - baseline → overfit → regularize
* [Pairing: binary classification](/foundations/pairing-binary-classification.md) - sigmoid + binary_crossentropy
* [Pairing: multiclass single-label](/foundations/pairing-multiclass-single-label.md) - softmax + categorical_crossentropy
* [Pairing: multilabel](/foundations/pairing-multilabel.md) - sigmoid + binary_crossentropy
* [Pairing: scalar regression](/foundations/pairing-scalar-regression.md) - no activation + mse
* [Pretrained feature extraction](/foundations/pretrained-feature-extraction.md) - small-data image pattern
* [Modern convnet patterns](/foundations/modern-convnet-patterns.md) - residual + separable + batchnorm
* [Bag-of-bigrams text](/foundations/bag-of-bigrams-text.md) - low-ratio text pattern
* [Recurrent forecasting](/foundations/recurrent-forecasting.md) - stacked GRU timeseries pattern
* [Dense tabular](/foundations/dense-tabular.md) - vector-data pattern
* [Scope boundary](/foundations/scope-boundary.md) - what the catalog does not cover

# Modern (2022–2026)

* [Time-series foundation models for financial forecasting](/modern/tsfm-financial-forecasting.md) - zero-shot TSFMs as out-of-domain transfer; caveats from model cards (draft)
* [LLM-automated factor research](/modern/llm-automated-factor-research.md) - RD-Agent(Q)/AlphaGen loops paired with the qlib backtest stack (draft)

# Domains

## quant-finance (expedition qlib-2026-08-03 — all draft)

* [Alpha-forecasting routing](/domains/quant-finance/alpha-forecasting-routing.md) - when a problem is alpha-forecasting territory and the qlib workflow applies
* [Leakage and evaluation discipline](/domains/quant-finance/leakage-and-evaluation.md) - point-in-time data, chronological/purged splits, IC/RankIC, multi-run reporting
* [qlib model selection](/domains/quant-finance/qlib-model-selection.md) - boosted-tree baseline vs neural models in the qlib zoo
* [qlib qrun workflow](/domains/quant-finance/qlib-qrun-workflow.md) - declarative YAML from data to backtest

# Tier vocabulary (`tier` custom field)

`book-canon` (DLwP-2E, pedagogically complete) · `modern-consensus`
(multiple independent 2022–2026 sources agree) · `frontier` (single paper
or trending system; explicitly experimental). Orthogonal to OKF trust
tiers, which derive from `verified` entries.
