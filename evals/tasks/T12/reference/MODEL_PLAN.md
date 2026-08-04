# Model Plan — building energy regressor (3k records)
Status: IN-SCOPE

## Problem framing
Task type: scalar regression
Modality: vector/tabular. Dataset size: 3,000 samples.

## Architecture
Recommendation: a small Dense network over normalized tabular features (two hidden layers); vector data with no structure to exploit
Cited rule: DLwP-2E ch6 — regression to arbitrary values takes NO last-layer activation and mse loss; accuracy is meaningless for regression, track MAE instead

## Loss & activation
Last-layer activation: none
Loss: mse
Metrics: mae

## Evaluation protocol
Protocol: K-fold cross-validation (3,000 samples)
Common-sense baseline: predict the training-set mean consumption; the model must beat its MAE

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
