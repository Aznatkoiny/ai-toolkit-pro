# Model Plan — 24h-ahead temperature forecaster (5 years hourly)
Status: IN-SCOPE

## Problem framing
Task type: scalar regression
Modality: timeseries. Dataset size: ~43,800 hourly samples over 5 years.

## Architecture
Recommendation: a recurrent model — stacked GRU/LSTM layers with recurrent dropout over windowed sequences; consider a 1D convnet front-end only if latency demands it; densely connected and 1D-conv-only baselines first to prove the RNN earns its cost
Cited rule: DLwP-2E ch10 — order-sensitive timeseries: recurrent networks exploit temporal ordering that dense and convnet models discard

## Loss & activation
Last-layer activation: none
Loss: mse
Metrics: mae

## Evaluation protocol
Protocol: simple holdout with a strictly chronological split (train on the past, validate on the future; never shuffle time)
Common-sense baseline: the naive last-value baseline: predict that the temperature 24h from now equals the temperature now; the model must beat its MAE

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
