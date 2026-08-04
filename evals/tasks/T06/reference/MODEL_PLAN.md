# Model Plan — apartment price regressor (900 rows, 30 features)
Status: IN-SCOPE

## Problem framing
Task type: scalar regression
Modality: vector/tabular. Dataset size: 900 samples.

## Architecture
Recommendation: a small densely connected network (two Dense hidden layers, 64 units, relu) — vector data with no spatial or temporal structure assumes nothing a Dense stack cannot model; keep capacity small to avoid overfitting 900 samples; normalize features per column
Cited rule: DLwP-2E ch14 — vector data maps to densely connected models; ch4 Boston Housing pattern for small-sample regression

## Loss & activation
Last-layer activation: none
Loss: mse
Metrics: mae

## Evaluation protocol
Protocol: K-fold cross-validation (900 samples make single-split validation scores too noisy)
Common-sense baseline: predict the mean sale price of the training set; the model must beat its MAE

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
