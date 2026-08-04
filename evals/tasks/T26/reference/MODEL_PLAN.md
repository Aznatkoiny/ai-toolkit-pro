# Model Plan — evaluation redesign for a stock-return model
Status: IN-SCOPE

## Problem framing
Task type: cross-sectional return forecasting (alpha)
Modality: financial timeseries panel. The random split leaks the future; accuracy is meaningless for continuous relative returns.

## Architecture
Recommendation: keep the model; replace the evaluation harness: point-in-time data, chronological walk-forward splits with periodic retraining, and rank-correlation metrics instead of accuracy
Cited rule: qlib docs — leakage and evaluation discipline [domains/quant-finance/leakage-and-evaluation]
Evidence: unverified

## Loss & activation
Last-layer activation: none
Loss: mse
Metrics: IC, RankIC, ICIR

## Evaluation protocol
Protocol: chronological walk-forward; purge overlapping label windows; never random splits on temporal financial data
Common-sense baseline: report the IC of a naive momentum factor as the floor

## Workflow
1. Beat the common-sense baseline: establish statistical power first.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: only after the baseline is beaten.

## Scope notes
Grounded in DRAFT expedition concepts (Evidence: unverified).
