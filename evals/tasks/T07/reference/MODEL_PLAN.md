# Model Plan — abstract topic tagger (12k abstracts, 15 tags, multilabel)
Status: IN-SCOPE

## Problem framing
Task type: multilabel classification
Modality: text. Dataset size: 12,000 samples. Labels: 15, non-exclusive (multilabel).

## Architecture
Recommendation: bag-of-bigrams TF-IDF into a Dense model with 15 sigmoid outputs — one independent binary decision per label; ratio 12,000/≈200 ≈ 60 < 1,500, so bag-of-words beats a sequence model here
Cited rule: DLwP-2E ch6 — multiclass multilabel classification takes sigmoid + binary_crossentropy (one binary decision per label); ch11 ratio rule

## Loss & activation
Last-layer activation: sigmoid
Loss: binary_crossentropy
Metrics: precision, recall (per-label)

## Evaluation protocol
Protocol: simple holdout (12k samples)
Common-sense baseline: predict each label at its base rate (per-label majority guess); the model must beat its per-label F1

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
