# Model Plan — fraud classifier (800k transactions)
Status: IN-SCOPE

## Problem framing
Task type: binary classification
Modality: vector/tabular. Dataset size: 800,000 samples (class-imbalanced).

## Architecture
Recommendation: a Dense network over engineered transaction features; vector data maps to densely connected models — start simple before anything exotic
Cited rule: DLwP-2E ch5/ch6 — with 800k samples a simple holdout validation split is statistically sufficient; ch14: vector data maps to Dense models

## Loss & activation
Last-layer activation: sigmoid
Loss: binary_crossentropy
Metrics: ROC AUC, precision at fixed recall (fraud is rare — accuracy is misleading)

## Evaluation protocol
Protocol: simple holdout (800k samples; keep the split chronological if fraud patterns drift)
Common-sense baseline: flag every transaction as legit (majority class): near-perfect accuracy, zero recall — the model must beat its precision/recall, not its accuracy

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
