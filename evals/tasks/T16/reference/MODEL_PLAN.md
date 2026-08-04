# Model Plan — urgent-ticket classifier (4k tickets, ~120 words)
Status: IN-SCOPE

## Problem framing
Task type: binary classification
Modality: text. Dataset size: 4,000 samples, ~120 words each. Ratio ≈ 33 < 1,500.

## Architecture
Recommendation: bag-of-bigrams TF-IDF via TextVectorization into a small Dense model: ratio 4,000/120 ≈ 33 < 1,500 — sequence models do not pay off here
Cited rule: DLwP-2E ch11 — below the 1,500 samples/mean-words ratio, bag-of-bigrams beats sequence models

## Loss & activation
Last-layer activation: sigmoid
Loss: binary_crossentropy
Metrics: accuracy, recall on the urgent class

## Evaluation protocol
Protocol: K-fold cross-validation (4,000 samples)
Common-sense baseline: predict not-urgent for everything; the model must beat its recall on the urgent class

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
