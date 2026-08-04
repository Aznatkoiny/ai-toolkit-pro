# Model Plan — readmission classifier (240 records, 19 features)
Status: IN-SCOPE

## Problem framing
Task type: binary classification
Modality: vector/tabular. Dataset size: 240 samples (tiny-data regime).

## Architecture
Recommendation: the smallest Dense network that beats the baseline: one or two narrow Dense layers (8-16 units) with strong L2 weight decay and dropout — 240 samples cannot support more capacity; feature normalization mandatory
Cited rule: DLwP-2E ch5 — with very little data, shrink capacity and regularize hard; the manifold hypothesis does not rescue a 240-row dataset

## Loss & activation
Last-layer activation: sigmoid
Loss: binary_crossentropy
Metrics: ROC AUC, accuracy

## Evaluation protocol
Protocol: iterated K-fold with shuffling (the ch5 protocol for tiny datasets where single K-fold scores are still too noisy)
Common-sense baseline: always predict no-readmission (the majority class); the model must beat its ROC AUC of 0.5 and its accuracy floor

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
