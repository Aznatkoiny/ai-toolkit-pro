# Model Plan — zero-shot TSFM assessment for demand and market forecasting
Status: IN-SCOPE

## Problem framing
Task type: timeseries forecasting (zero-shot transfer)
Modality: timeseries. Zero-shot use means no training data leaves your side, but domain gap on financial series is real.

## Architecture
Recommendation: trial a time-series foundation model (Chronos-class) zero-shot as a BASELINE, gated against the last-value naive baseline and a trained GRU; treat financial series as out-of-domain transfer with reduced expectations
Cited rule: HF model cards — TSFMs for financial forecasting [modern/tsfm-financial-forecasting]
Cited rule: DLwP-2E ch10 — order-sensitive timeseries [foundations/recurrent-forecasting]
Evidence: unverified

## Loss & activation
Last-layer activation: none
Loss: mse
Metrics: mae; scaled error vs naive baseline

## Evaluation protocol
Protocol: chronological holdout; compare against the naive last-value baseline before trusting any zero-shot output
Common-sense baseline: last-value/persistence forecast; the TSFM must beat its MAE

## Workflow
1. Beat the common-sense baseline: establish statistical power first.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: only after the baseline is beaten.

## Scope notes
Grounded partly in DRAFT expedition concepts (Evidence: unverified) - the TSFM landscape moves fast; stale_after applies.
