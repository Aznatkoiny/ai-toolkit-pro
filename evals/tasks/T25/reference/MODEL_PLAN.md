# Model Plan — long-short alpha forecaster (3,000 stocks, 8y daily)
Status: IN-SCOPE

## Problem framing
Task type: cross-sectional return forecasting (alpha)
Modality: cross-sectional financial panel. Dataset size: ~6M stock-days. Low signal-to-noise regime.

## Architecture
Recommendation: the qlib full-chain workflow: point-in-time features (Alpha158-style), a boosted-tree baseline before neural models, signal to portfolio via a long-short strategy with backtest
Cited rule: qlib docs — alpha-forecasting routing [domains/quant-finance/alpha-forecasting-routing]
Cited rule: qlib docs — leakage and evaluation discipline [domains/quant-finance/leakage-and-evaluation]
Evidence: unverified

## Loss & activation
Last-layer activation: none
Loss: mse
Metrics: IC, RankIC

## Evaluation protocol
Protocol: chronological walk-forward with periodic retraining — never shuffled splits
Common-sense baseline: cross-sectional momentum rank (a zero-ML factor); the model must beat its IC

## Workflow
1. Beat the common-sense baseline: establish statistical power first.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: only after the baseline is beaten.

## Scope notes
Grounded in DRAFT expedition concepts (Evidence: unverified) — verified foundations do not cover quantitative finance; treat recommendations as a starting frame, not settled guidance.
