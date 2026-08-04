# Model Plan — product attribute tagger (30k listings, 22 tags, multilabel)
Status: IN-SCOPE

## Problem framing
Task type: multilabel classification
Modality: text/vector. Dataset size: 30,000 samples. Labels: 22, non-exclusive (multilabel).

## Architecture
Recommendation: bag-of-bigrams TF-IDF over listing text into a Dense model with 22 independent sigmoid outputs
Cited rule: DLwP-2E ch6 — multilabel classification takes sigmoid + binary_crossentropy: one independent binary decision per tag

## Loss & activation
Last-layer activation: sigmoid
Loss: binary_crossentropy
Metrics: per-label precision/recall

## Evaluation protocol
Protocol: simple holdout (30k samples)
Common-sense baseline: per-tag base-rate guessing; the model must beat per-tag F1

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
