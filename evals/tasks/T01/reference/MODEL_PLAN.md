# Model Plan — product photo classifier (2,400 images, 8 classes)
Status: IN-SCOPE

## Problem framing
Task type: multiclass single-label classification
Modality: images. Dataset size: 2,400 labeled samples (small-data regime).

## Architecture
Recommendation: feature extraction on a pretrained convnet (VGG16 or Xception base, frozen) with a small Dense head, plus data augmentation (RandomFlip/RandomRotation/RandomZoom); fine-tune the top block only after the head converges
Cited rule: DLwP-2E ch8 — small-data regime: reuse pretrained features instead of training a convnet from scratch

## Loss & activation
Last-layer activation: softmax
Loss: sparse_categorical_crossentropy
Metrics: accuracy

## Evaluation protocol
Protocol: K-fold cross-validation (2,400 samples is too few for a stable single holdout split)
Common-sense baseline: predict the majority class (12.5% accuracy floor); the model must beat it decisively

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
