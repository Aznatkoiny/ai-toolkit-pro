---
type: Decision Rule
title: "Routing: when a problem is alpha-forecasting territory"
description: >
  Recognize cross-sectional return-forecasting (alpha) problems, route them into the
  qlib-style quant workflow, and sub-route between supervised forecasting, market-dynamics
  adaptation, and RL execution. Generic tabular/time-series solutions rarely transfer
  to this domain without adaptation.
tags: [quant-finance, routing, alpha-forecasting, qlib, problem-framing]
tier: modern-consensus  # skeptic note: tier vocabulary for domains/ is undefined in the catalog; lead to confirm before landing
applies_to:
  - cross-sectional stock/asset return prediction
  - alpha signal research and portfolio construction
  - trade execution optimization
route_when:
  - "many assets, target = relative future returns for ranking/selection"
  - "success is judged by cost-aware backtest, not held-out prediction accuracy"
  - "features derive from prices/volumes/fundamentals with strict temporal ordering"
route_away_when:
  - "single or few independent series, no cross-sectional ranking (general time-series forecasting)"
  - "unstructured financial text tasks (finance NLP, not this rule)"
status: draft
stale_after: 2027-02-01
generated:
  by: expedition/qlib-2026-08-03
  at: 2026-08-03T12:00:00Z
sources:
  - id: qlib-readme
    resource: https://github.com/microsoft/qlib
    title: "Qlib: AI-oriented Quantitative Investment Platform (README)"
    author: Microsoft
    last_modified: 2026-04-22
  - id: qlib-paper
    resource: https://arxiv.org/abs/2009.11189
    title: "Qlib: An AI-oriented Quantitative Investment Platform"
    author: Microsoft Research
    last_modified: 2020-09-23
  - id: qlib-rl
    resource: https://qlib.readthedocs.io/en/latest/component/rl/overall.html
    title: "QlibRL: Reinforcement Learning in Quantitative Trading (docs)"
    author: Qlib maintainers
    last_modified: 2022-11-10  # skeptic note: unverified; /latest/ tracks main and may be newer
  - id: survey
    resource: https://arxiv.org/abs/2503.21422
    title: "From Deep Learning to LLMs: A survey of AI in Quantitative Investment"
    author: "B. Cao, S. Wang, X. Lin, X. Wu, H. Zhang, L. M. Ni, J. Guo"
    last_modified: 2025-03-27
---

# Rule

Route a problem into the alpha-forecasting domain when it has all three of: (a) a cross-section of many tradable assets, (b) the target is forecasting *relative* future returns so assets can be ranked and selected, and (c) success is judged by a cost-aware backtest downstream of the prediction. This matches the problem-class span of Microsoft's Qlib platform, which covers "the entire chain of quantitative investment: alpha seeking, risk modeling, portfolio optimization, and order execution" along with the full ML pipeline of data processing, model training, and backtesting.[^qlib-readme]

Once routed, sub-route by learning paradigm. Qlib distinguishes three: supervised learning for return forecasting, market dynamics modeling for concept-drift adaptation (the DDG-DA framework), and reinforcement learning for continuous decision problems.[^qlib-readme] Order execution specifically — choosing "the order size, price, and timing of execution" — is framed as RL, not supervised forecasting.[^qlib-rl] Multi-granularity problems (a daily portfolio strategy plus an intraday execution strategy) are handled by the Nested Decision Execution Framework, which lets strategies and executors at different granularities be nested, optimized, and backtested together.[^qlib-readme]

Sub-route the model family by task geometry: temporal models (CNNs/RNNs/Transformers) for individual-asset trend forecasting, spatial models (GNNs, full cross-section self-attention, hypergraphs) for inter-asset relations and relative ranking, and spatiotemporal hybrids for both.[^survey]

Why this domain gets its own rules instead of generic tabular/time-series advice — per the Qlib paper, applying ML solutions to quant research tasks "without any adaptation rarely works":[^qlib-paper]

- **Extreme noise.** Financial data has an extremely low signal-to-noise ratio; even a minor implementation mistake can make a model overfit noise rather than learn effective patterns.[^qlib-paper]
- **Non-differentiable objectives.** Typical strategy objectives, such as annualized return, are often not differentiable, which makes it hard to train models on them directly — a structural mismatch with standard supervised losses.[^qlib-paper]
- **Non-stationarity.** The market is dynamic; the standard practice is to update models regularly as new data arrives, and Qlib treats dynamic model/strategy updating as a platform-level design concern (its Dynamic Modeling modules), not an afterthought.[^qlib-paper]
- **Feature explosion at scale.** Pipelines routinely derive thousands of engineered features from basic price/volume data that has only five raw dimensions, and data can reach terabyte scale in high-frequency settings — which is why Qlib built a specialized time-series flat-file database rather than using general-purpose databases.[^qlib-paper]

Route **away** from this domain when the problem is forecasting one or a few independent series with no cross-sectional ranking and no trading frictions — that is general time-series forecasting (see /foundations/recurrent-forecasting.md; a modern TSFM concept is not yet in the catalog), and when the task is unstructured financial text (sentiment, filings QA), which is finance NLP.

# Conflicts with stable concepts

- /foundations/scope-boundary.md (stable) currently lists reinforcement learning, graph neural networks, and quantitative-finance ML workflows as *not covered*; this draft sub-routes into RL execution and GNN-family models. Per catalog policy, stable wins until this concept lands, and scope-boundary must be revised in the same landing (its own text requires every landing expedition to revisit it).

# Open questions

- Scouts gathered no evidence on where classic portfolio optimization *without* an ML forecasting stage should bypass this workflow entirely; the boundary between "alpha forecasting + strategy" and pure optimization problems is undocumented in the sourced material.

[^qlib-readme]: microsoft/qlib README: "covers the entire chain of quantitative investment: alpha seeking, risk modeling, portfolio optimization, and order execution"; "supports diverse machine learning modeling paradigms, including supervised learning, market dynamics modeling, and RL" (DDG-DA listed under "Adapting to Market Dynamics"); Nested Decision Execution Framework: "Multiple trading strategies and executors in different levels or granularities can be nested to be optimized and run together."
[^qlib-rl]: QlibRL docs, "Reinforcement Learning in Quantitative Trading": "actions can include selecting the order size, price, and timing of execution."
[^qlib-paper]: arXiv:2009.11189, sections 2–3: "extremely low SNR (Signal to Noise Ratio) in financial data"; "Even a minor mistake can make the model over-fit the noise rather than learn effective patterns"; "the typical objectives, such as annualized return, are often not differentiable, which makes it hard to train models directly"; regular model updating due to the "dynamic nature of the stock market" (Dynamic Modeling modules); "thousands of new features (e.g., Alpha101) from the basic price and volume data, which consist of only five dimensions in total"; data "could reach the order of TB magnitude in the scenario of high-frequency trading"; "a timeseries flat-file database... greatly outperforms current popular storage solutions like general-purpose databases."
[^survey]: arXiv:2503.21422, forecasting-model sections "To capture temporal patterns", "To capture spatial patterns", "To capture spatiotemporal interactions."
