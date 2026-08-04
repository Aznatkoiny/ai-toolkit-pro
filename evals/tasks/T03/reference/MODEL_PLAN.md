# Model Plan — review sentiment classifier (2,300 reviews, ~180 words each)
Status: IN-SCOPE

## Problem framing
Task type: binary classification
Modality: text. Dataset size: 2,300 samples, ~180 words each. Ratio samples/mean-words ≈ 13 < 1,500.

## Architecture
Recommendation: bag-of-bigrams with TF-IDF weighting feeding a small Dense model — NOT a sequence model: samples / mean words per sample = 2,300 / 180 ≈ 13, far below the 1,500 threshold where sequence models start to pay off
Cited rule: DLwP-2E ch11 — when the ratio of samples to mean words per sample is below 1,500, bag-of-bigrams beats sequence models

## Loss & activation
Last-layer activation: sigmoid
Loss: binary_crossentropy
Metrics: accuracy

## Evaluation protocol
Protocol: K-fold cross-validation (2,300 samples)
Common-sense baseline: always predict the majority sentiment class (50% floor if balanced)

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
