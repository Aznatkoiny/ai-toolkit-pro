---
type: Decision Rule
title: "Model selection in the qlib zoo: boosted-tree baseline vs neural models"
description: >
  Start with a LightGBM baseline on engineered Alpha158 features; escalate to deep
  sequential or cross-sectional models only on raw Alpha360-style inputs. The feature
  set, not fashion, drives the model family.
tags: [quant-finance, model-selection, gbdt, lightgbm, deep-learning, qlib, alpha158, alpha360]
tier: modern-consensus
applies_to:
  - choosing a forecast model for cross-sectional return prediction
  - qlib model zoo usage
default_baseline: "LightGBM on Alpha158"
status: draft
stale_after: 2026-12-01
generated:
  by: expedition/qlib-2026-08-03
  at: 2026-08-03T12:00:00Z
sources:
  - id: benchmarks
    resource: https://github.com/microsoft/qlib/tree/main/examples/benchmarks
    title: "Qlib examples/benchmarks (model zoo, dataset guidance, CSI300 results)"
    author: Microsoft
    last_modified: 2023-08-01
  - id: data-docs
    resource: https://qlib.readthedocs.io/en/latest/component/data.html
    title: "Qlib docs: Data Layer"
    author: Qlib maintainers
  - id: master
    resource: https://arxiv.org/abs/2312.15235
    title: "MASTER: Market-Guided Stock Transformer for Stock Price Forecasting"
    author: Li et al. (AAAI 2024)
    last_modified: 2023-12-23
  - id: rdagentq
    resource: https://arxiv.org/abs/2505.15155
    title: "R&D-Agent-Quant (baseline suite for CSI300 stock prediction)"
    author: Microsoft Research
    last_modified: 2025-05-21
  - id: alphagen
    resource: https://arxiv.org/abs/2306.12964
    title: "Generating Synergistic Formulaic Alpha Collections via Reinforcement Learning (AlphaGen)"
    author: Yu et al. (KDD 2023)
    last_modified: 2023-06-22
---

# Rule

**Match the model family to the feature set, and baseline with boosted trees.**

Qlib's own dataset guidance draws the line: "Alpha158 is a tabular dataset. There are less spatial relationships between different features. Each feature [is] carefully designed by human (a.k.a feature engineering)" — engineered tabular features that suit tree-based and linear models.[^benchmarks] Conversely, "Alpha360 contains raw price and volume data without much feature engineering. There are strong spatial relationships between the features in the time dimension" — raw price/volume time-series inputs that suit sequential deep architectures (LSTM/GRU/Transformer-family) rather than trees.[^benchmarks]

The CSI300 benchmarks (mean±std over 20 seeds; README snapshot last modified 2023-08-01) bear this out:

- **Alpha158 (engineered/tabular):** ensembles and GBDTs lead. DoubleEnsemble posts both the best annualized return 0.1158±0.01 (IR 1.3432±0.11) and the best IC 0.0521±0.00; XGBoost (IC 0.0498±0.00) and CatBoost (IC 0.0481±0.00) complete an all-tree-ensemble IC top three; LightGBM reaches AR 0.0901±0.00 (IC 0.0448±0.00). Neural nets are not hopeless on engineered features — MLP's AR 0.0895±0.02 nearly ties LightGBM — but none cracks the IC top three.[^benchmarks]
- **Alpha360 (raw time-series):** specialized deep models win. HIST posts the best AR 0.0987±0.02, IR 1.3726±0.27, and lowest max drawdown −0.0681±0.01, followed by IGMTF (AR 0.0946±0.02) and TRA (AR 0.0920±0.03).[^benchmarks]

The zoo spans 20+ architectures — GBDTs (XGBoost, LightGBM, CatBoost), deep sequential (LSTM, GRU, ALSTM, TCN, ADARNN, Transformer, Localformer, TFT, SFM), graph/cross-sectional (GATs, HIST, IGMTF), tabular nets (TabNet, MLP), routing/ensemble methods (TRA, TCTS, DoubleEnsemble, ADD, KRNN, Sandwich), and Linear baselines — most traceable to a published paper (Linear, MLP, KRNN, and Sandwich carry no paper citation in the README).[^benchmarks] The wider 2025 baseline suite for this task also includes PatchTST, iTransformer, Mamba, and MASTER.[^rdagentq]

**Preprocessing must match the family:** "GBDT may work well on data that contains nan or None value, while neural networks such as MLP will break down on such data"; qlib ships processors including MinMaxNorm, ZscoreNorm, RobustZScoreNorm, cross-sectional CSZScoreNorm/CSRankNorm, Dropna/Fillna variants, and TanhProcess for noise.[^data-docs]

**Do not read the leaderboard as a definitive architecture ranking.** The maintainers state: "We have very limited resources to implement and finetune the models... some models may have greater potential than what it looks like in the table below."[^benchmarks] Results are also not comparable across qlib versions (backtest changed at v0.8.0).[^benchmarks]

**Frontier pressure on this rule:** MASTER — a transformer alternating intra-stock (temporal) and inter-stock (cross-sectional) attention with market-guided gating — beat XGBoost, LSTM, GRU, TCN, Transformer, GAT, and DTML on CSI300/CSI800 (~13% better ranking metrics, ~47% better portfolio metrics; CSI300 IC 0.064 vs 0.054 for runner-up GAT). These are the authors' self-reported numbers on their own splits and protocol — not qlib's 20-seed benchmark — so they are not comparable to the table above.[^master] And factor quality can dominate model choice: AlphaGen's RL-mined alpha set reached IC 0.0725 on CSI300 vs 0.0404 for XGBoost on its splits.[^alphagen] Related caveat when pruning factor inputs: high pairwise correlation between alphas does not imply redundancy — two alphas with mutual IC 0.9746 still improved combined pool IC.[^alphagen]

# Conflicts with stable concepts

Recorded, not resolved (house rule). The book-canon
[modality → architecture map](/foundations/modality-architecture-map.md)
routes vector/tabular data to a Dense stack, and
[dense network for vector/tabular data](/foundations/dense-tabular.md) is the
catalog's stable tabular pattern. This concept routes engineered tabular
factors (Alpha158-style) to a boosted-tree baseline instead. The book canon
is deep-learning-only by scope and never weighs GBDTs; within cross-sectional
return prediction the qlib evidence above favors trees as the first baseline.
Until this draft is verified, the advisor should surface both concepts with
their trust tiers stated.

# Open questions

- Whether specialized neural models genuinely dominate GBDTs under equal tuning budgets is unresolved: the qlib zoo's own under-tuning caveat[^benchmarks] cuts both ways, and no sourced study equalizes tuning effort across families.

[^benchmarks]: Qlib examples/benchmarks README (last modified 2023-08-01). Quoted dataset descriptions lightly normalized for typos in the original.
[^data-docs]: Qlib docs, Data Layer — NaN-handling guidance and processor list.
[^master]: arXiv:2312.15235 (AAAI 2024); authors' own experimental protocol, not qlib's benchmark harness.
[^rdagentq]: arXiv:2505.15155; baseline table for CSI300 stock prediction.
[^alphagen]: arXiv:2306.12964 (KDD 2023); Table 2 and Section 4.3.
