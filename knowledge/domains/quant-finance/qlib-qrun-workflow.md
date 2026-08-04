---
type: Architecture Pattern
title: "The qlib qrun workflow: declarative YAML from data to backtest"
description: >
  Qlib's canonical pipeline — data layer, feature dataset, forecast model, portfolio
  strategy, cost-aware backtest — driven end-to-end by a single declarative qrun YAML
  config with model/dataset/record sections.
tags: [quant-finance, qlib, workflow, qrun, backtesting, architecture]
tier: modern-consensus
status: draft
stale_after: 2027-02-01
generated:
  by: expedition/qlib-2026-08-03
  at: 2026-08-03T12:00:00Z
sources:
  - id: workflow
    resource: https://qlib.readthedocs.io/en/latest/component/workflow.html
    title: "Qlib docs: Workflow - Workflow Management (qrun)"
    author: Qlib maintainers
  - id: data-docs
    resource: https://qlib.readthedocs.io/en/latest/component/data.html
    title: "Qlib docs: Data Layer (expression engine, processors)"
    author: Qlib maintainers
  - id: qlib-readme
    resource: https://github.com/microsoft/qlib
    title: "Qlib README (performance numbers, data caveats)"
    author: Microsoft
    last_modified: 2026-04-22
  - id: qlib-paper
    resource: https://arxiv.org/abs/2009.11189
    title: "Qlib: An AI-oriented Quantitative Investment Platform"
    author: Microsoft Research
    last_modified: 2020-09-22
---

# Pattern

The canonical qlib pipeline is: data layer (raw OHLCV + expression engine) → feature dataset (Alpha158 or Alpha360) → forecast model training → portfolio strategy → backtest and evaluation. The `qrun` tool "run[s] the whole workflow automatically (including building dataset, training models, backtest and evaluation)" from a single YAML config,[^qlib-readme] invoked as `qrun configuration.yaml`.[^workflow]

The config has a standard shape: qlib init parameters (`provider_uri`, `region` cn/us), then a `task` section with three subsections — `model` (e.g., LGBModel with hyperparameters), `dataset` (a data handler plus train/valid/test temporal segments), and `record` (signal analysis + backtest records). Every component is declared as `class` / `module_path` / `kwargs`, making experiments declarative and reproducible.[^workflow] The underlying platform design is modular — data server, data enhancement, model creation/management/ensemble, portfolio generator, order executor, and analyser modules connected in a typical workflow.[^qlib-paper]

Feature engineering is declarative too: formulaic alphas are expression strings over raw fields (e.g., `Ref($close, 60) / $close` for the 60-day-ago price ratio), evaluated by an expression engine whose operator set lives in `qlib/data/ops.py` — not imperative pandas code.[^data-docs]

The reference backtest converts forecasts to portfolios with `TopkDropoutStrategy` (`topk: 50`, `n_drop: 5`) and models trading frictions via exchange kwargs: `limit_threshold 0.095` (China A-share price limit), `deal_price close`, `open_cost 0.0005`, `close_cost 0.0015`, `min_cost 5`.[^workflow]

Storage is a deliberate design point: the flat-file data server plus three-layer caching (MemCache, ExpressionCache, DatasetCache) reports 7.4±0.3 seconds on a single CPU for a data task where HDF5 takes 184.4+ seconds and MySQL/InfluxDB solutions 365+ seconds.[^qlib-readme]

**Data caveat:** the bundled community dataset "is collected from Yahoo Finance, and the data might not be perfect. We recommend users to prepare their own data if they have a high-quality dataset"[^qlib-readme] — i.e., treat published results on the free data as methodology comparisons, not production signals.

# Examples

Skeleton of the documented config shape (values are the documented reference defaults):[^workflow]

```yaml
qlib_init:
    provider_uri: "~/.qlib/qlib_data/cn_data"
    region: cn
task:
    model:
        class: LGBModel
        module_path: qlib.contrib.model.gbdt
        kwargs: { loss: mse, num_leaves: 210 }  # further documented hyperparameters elided
    dataset:
        class: DatasetH
        module_path: qlib.data.dataset
        kwargs:
            handler:
                class: Alpha158
                module_path: qlib.contrib.data.handler
            segments:
                train: [2008-01-01, 2014-12-31]
                valid: [2015-01-01, 2016-12-31]
                test:  [2017-01-01, 2020-08-01]
    record:
        - class: SignalRecord      # signal analysis (IC / Rank IC)
        - class: PortAnaRecord     # backtest with TopkDropoutStrategy
          # strategy kwargs: topk: 50, n_drop: 5
          # exchange kwargs: limit_threshold: 0.095, deal_price: close,
          #                  open_cost: 0.0005, close_cost: 0.0015, min_cost: 5
```

Run with `qrun configuration.yaml`.[^workflow]
