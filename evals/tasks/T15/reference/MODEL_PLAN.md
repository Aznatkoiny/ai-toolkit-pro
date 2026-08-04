# Model Plan — machine-part classifier (3k images, 6 classes)
Status: IN-SCOPE

## Problem framing
Task type: multiclass single-label classification
Modality: images. Dataset size: 3,000 labeled samples.

## Architecture
Recommendation: feature extraction on a frozen pretrained Xception base with a small Dense head and data augmentation
Cited rule: DLwP-2E ch8 — small-data image classification: reuse pretrained convnet features

## Loss & activation
Last-layer activation: softmax
Loss: sparse_categorical_crossentropy
Metrics: accuracy

## Evaluation protocol
Protocol: K-fold cross-validation (3,000 samples)
Common-sense baseline: majority-class prediction (~16.7%)

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
