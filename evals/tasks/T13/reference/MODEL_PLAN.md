# Model Plan — tumor/benign classifier validation plan (300 images)
Status: IN-SCOPE

## Problem framing
Task type: binary classification
Modality: images. Dataset size: 300 labeled samples (tiny-data regime).

## Architecture
Recommendation: pretrained convnet feature extraction with a tiny sigmoid head and aggressive augmentation — 300 images cannot train any convnet from scratch
Cited rule: DLwP-2E ch5 — evaluation protocol is chosen by data size: with ~300 samples, iterated K-fold with shuffling is the only protocol whose scores are stable enough to act on; ch8 small-data transfer learning

## Loss & activation
Last-layer activation: sigmoid
Loss: binary_crossentropy
Metrics: ROC AUC, sensitivity at fixed specificity

## Evaluation protocol
Protocol: iterated K-fold with shuffling (multiple K-fold rounds with different shuffles, averaged)
Common-sense baseline: always predict benign (the majority class); no model result is meaningful until it beats this baseline

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
