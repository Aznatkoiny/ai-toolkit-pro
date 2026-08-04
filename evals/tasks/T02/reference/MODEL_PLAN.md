# Model Plan — large-scale product classifier (600k images, 40 classes)
Status: IN-SCOPE

## Problem framing
Task type: multiclass single-label classification
Modality: images. Dataset size: 600,000 labeled samples (large-data regime).

## Architecture
Recommendation: a modern convnet trained from scratch: convolutional base organized in residual blocks with batch normalization and depthwise separable convolutions (mini-Xception pattern), GlobalAveragePooling2D head
Cited rule: DLwP-2E ch9 — modern convnet architecture patterns (residual connections, batchnorm, separable convolutions); ch8: with abundant data, training from scratch is justified

## Loss & activation
Last-layer activation: softmax
Loss: sparse_categorical_crossentropy
Metrics: accuracy

## Evaluation protocol
Protocol: simple holdout (600k samples give a stable validation split)
Common-sense baseline: majority-class prediction (~2.5% accuracy); any useful model must beat it by an order of magnitude

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
