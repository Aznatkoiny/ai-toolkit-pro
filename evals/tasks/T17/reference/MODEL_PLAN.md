# Model Plan — churn classifier (1,200 rows)
Status: IN-SCOPE

## Problem framing
Task type: binary classification
Modality: vector/tabular. Dataset size: 1,200 samples.

## Architecture
Recommendation: a small Dense network (two hidden layers, 16 units, dropout) over normalized tabular features
Cited rule: DLwP-2E ch14 — vector data maps to densely connected models; ch5 small-data regularization discipline

## Loss & activation
Last-layer activation: sigmoid
Loss: binary_crossentropy
Metrics: ROC AUC, accuracy

## Evaluation protocol
Protocol: K-fold cross-validation (1,200 samples)
Common-sense baseline: always predict no-churn; the model must beat its ROC AUC of 0.5

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
