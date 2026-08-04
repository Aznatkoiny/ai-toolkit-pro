---
type: Decision Rule
title: "Leakage and evaluation discipline for financial ML"
description: >
  Point-in-time data discipline, strict chronological splits and walk-forward validation,
  IC/RankIC-family signal metrics, and multi-seed reporting. Extends the chronological-split
  clause of /foundations/evaluation-protocol-by-size.md to all financial market data; the
  size-based random-split table there does not apply.
tags: [quant-finance, evaluation, data-leakage, point-in-time, IC, walk-forward]
tier: modern-consensus
applies_to:
  - any model trained or evaluated on financial market data
  - alpha signal evaluation before backtesting
  - LLM-in-the-loop factor research
status: draft
stale_after: 2027-02-01
generated:
  by: expedition/qlib-2026-08-03
  at: 2026-08-03T12:00:00Z
sources:
  - id: pit
    resource: https://qlib.readthedocs.io/en/latest/advanced/PIT.html
    title: "Qlib docs: (Point-In-Time) Database"
    author: Qlib maintainers
    last_modified: 2022-03-10
  - id: report
    resource: https://qlib.readthedocs.io/en/latest/component/report.html
    title: "Qlib docs: Analysis - Evaluation & Results Analysis"
    author: Qlib maintainers
  - id: benchmarks
    resource: https://github.com/microsoft/qlib/tree/main/examples/benchmarks
    title: "Qlib examples/benchmarks (model zoo results and methodology)"
    author: Microsoft
    last_modified: 2023-05-26
  - id: qlib-paper
    resource: https://arxiv.org/abs/2009.11189
    title: "Qlib: An AI-oriented Quantitative Investment Platform"
    author: Microsoft Research
    last_modified: 2020-09-23
  - id: rdagentq
    resource: https://arxiv.org/abs/2505.15155
    title: "R&D-Agent-Quant: A Multi-Agent Framework for Data-Centric Factors and Model Joint Optimization"
    author: Microsoft Research
    last_modified: 2025-05-21
  - id: master
    resource: https://arxiv.org/abs/2312.15235
    title: "MASTER: Market-Guided Stock Transformer for Stock Price Forecasting"
    author: Li et al. (AAAI 2024)
    last_modified: 2023-12-23
  - id: alphagen
    resource: https://arxiv.org/abs/2306.12964
    title: "Generating Synergistic Formulaic Alpha Collections via Reinforcement Learning (AlphaGen)"
    author: Yu et al. (KDD 2023)
    last_modified: 2023-06-22
  - id: survey
    resource: https://arxiv.org/abs/2503.21422
    title: "From Deep Learning to LLMs: A survey of AI in Quantitative Investment"
    author: Bokai Cao et al.
    last_modified: 2025-03-27
---

# Rule

**Financial data rules out the size-based random-split table.** The k-fold / random-split guidance in [/foundations/evaluation-protocol-by-size.md](/foundations/evaluation-protocol-by-size.md) assumes exchangeable samples; financial samples are not exchangeable. That foundation already mandates chronological splits for timeseries; this concept extends the same discipline to all financial market data — including cross-sectional stock panels — and adds the quant-specific controls below. Every sourced work uses strictly chronological train/valid/test splits — e.g., RD-Agent(Q): CSI300 train 2008–2014, valid 2015–2016, test 2017–Aug 2020, with walk-forward validation for model training and cost-aware backtests[^rdagentq]; MASTER: train 2008–Q1'20, valid Q2'20, test Q3'20–Q4'22.[^master] Models are also periodically retrained as new data arrives (rolling retrain), a stated design assumption of the tooling, rather than evaluated once on a frozen split.[^qlib-paper]

**Point-in-time discipline.** Fundamental data gets amended after publication. Qlib's PIT database exists precisely because "if we only use the latest version for historical backtesting, data leakage will happen": a signal computed for 2020-01-01 must only see data available through 2019-12-31, not later restatements.[^pit] The implementation stores each fundamental feature with publication `date`, `period`, `value`, and a `_next` pointer to the next revision, enabling as-of queries.[^pit] Limitations as of the cited docs (2022): only quarterly/annual fundamentals are supported, and the maintainers note the PIT calculation "is not performed in the optimal way."[^pit]

**LLM-in-the-loop leakage.** When an LLM participates in factor/model research, RD-Agent(Q)'s protocol never exposes the LLM to raw market data or explicit temporal split boundaries — only schema-level information — explicitly to mitigate leakage into generated factors and models.[^rdagentq]

**Signal metrics before portfolio metrics.** IC is the Pearson correlation series between label and prediction score; Rank IC is the Spearman rank correlation series[^report] — the standard predictive-power gauges for alpha factors, computed daily and averaged.[^alphagen] ICIR/RankICIR normalize IC/RankIC by dividing by the standard deviation.[^master] Signal autocorrelation (correlation between latest scores and lagged scores) estimates turnover requirements *before* any backtest — a cheap early tradability check.[^report] Calibrate expectations to the noise floor: in the sourced 2023 CSI300/CSI500 results, even the best mean ICs are ≈0.07 and ≈0.04 respectively.[^alphagen]

**Portfolio metrics with costs.** Risk analysis reports std of excess returns, annualized return, information ratio with and without transaction cost, max drawdown, and turnover; group analysis splits stocks into quintile groups by ranking and tracks the Group1-minus-Group5 long-short cumulative-return series.[^report]

**Seed variance is first-class.** Qlib benchmarks report the mean and std over 20 runs with different random seeds[^benchmarks]; MASTER averages over 5 repetitions with random initialization and reports t-tests at p<0.01.[^master] Single-seed results are not comparable evidence. Also note backtests are not comparable across qlib versions: the benchmarks README warns the backtest from 0.8.0 onward "is quite different from previous version."[^benchmarks]

# Relation to stable foundations

This concept does not contradict [/foundations/evaluation-protocol-by-size.md](/foundations/evaluation-protocol-by-size.md); it extends that concept's timeseries clause ("never shuffle time regardless of size") to all financial market data and layers PIT discipline, IC-family signal metrics, cost-aware portfolio metrics, and multi-seed reporting on top. Only the size-based random-split table is inapplicable here.

# Open questions

- Purged/embargoed cross-validation and survivorship bias are not treated in any of the five core papers the scouts read (Qlib, RD-Agent(Q), AlphaGen, MASTER, and the 2025 survey — verified absent in the survey[^survey]); the field's published discipline rests on chronological splits, walk-forward retraining, IC-family metrics, cost-aware backtests, and multi-seed testing, leaving these bias controls an evidence gap.

[^pit]: Qlib docs, (Point-In-Time) Database (source id: pit).
[^report]: Qlib docs, Analysis: Evaluation & Results Analysis (source id: report).
[^benchmarks]: Qlib examples/benchmarks README (source id: benchmarks).
[^qlib-paper]: Qlib platform paper, arXiv:2009.11189 (source id: qlib-paper).
[^rdagentq]: R&D-Agent-Quant, arXiv:2505.15155 (source id: rdagentq).
[^master]: MASTER, arXiv:2312.15235 (source id: master).
[^alphagen]: AlphaGen, arXiv:2306.12964 (source id: alphagen).
[^survey]: AI in Quantitative Investment survey, arXiv:2503.21422 (source id: survey).
