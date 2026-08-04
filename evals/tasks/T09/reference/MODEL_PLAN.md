# Model Plan — EN-DE support-doc translator (150k pairs)
Status: IN-SCOPE

## Problem framing
Task type: sequence-to-sequence learning
Modality: text, paired sequences. Dataset size: 150,000 sentence pairs.

## Architecture
Recommendation: a Transformer encoder-decoder: encoder over the English source, decoder with causal + cross attention emitting German tokens; the ch11 seq2seq Transformer beats the GRU-based seq2seq at this scale
Cited rule: DLwP-2E ch11 — sequence-to-sequence learning: Transformer encoder-decoder is the canonical architecture for translation

## Loss & activation
Last-layer activation: softmax
Loss: sparse_categorical_crossentropy
Metrics: accuracy (next-token), BLEU

## Evaluation protocol
Protocol: simple holdout (150k pairs), plus BLEU spot checks on a held-out sample
Common-sense baseline: copy the source sentence unchanged (a surprisingly strong floor for related languages); the model must beat its BLEU

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
