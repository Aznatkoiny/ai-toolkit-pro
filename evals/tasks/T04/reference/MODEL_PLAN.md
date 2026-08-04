# Model Plan — intent classifier (400k posts, ~18 words each)
Status: IN-SCOPE

## Problem framing
Task type: multiclass single-label classification
Modality: text. Dataset size: 400,000 samples, ~18 words each. Ratio ≈ 22,000 > 1,500.

## Architecture
Recommendation: a sequence model over learned word embeddings — a Transformer encoder (or bidirectional LSTM) with positional embeddings: samples / mean words per sample = 400,000 / 18 ≈ 22,000, far above the 1,500 threshold, so word-order-aware models pay off
Cited rule: DLwP-2E ch11 — above the 1,500 samples/mean-words ratio, sequence models beat bag-of-words models

## Loss & activation
Last-layer activation: softmax
Loss: sparse_categorical_crossentropy
Metrics: accuracy

## Evaluation protocol
Protocol: simple holdout (400k samples)
Common-sense baseline: majority-class prediction (~33% if balanced)

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
