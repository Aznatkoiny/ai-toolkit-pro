# Model Plan — street-scene segmenter (5k images, 3 classes per pixel)
Status: IN-SCOPE

## Problem framing
Task type: image segmentation (per-pixel multiclass classification)
Modality: images with dense per-pixel targets. Dataset size: 5,000 masked images.

## Architecture
Recommendation: an encoder-decoder convnet: downsampling Conv2D stack, then Conv2DTranspose upsampling back to full resolution with a per-pixel softmax over the 3 classes (the ch9 Oxford-IIIT pattern); data augmentation given only 5,000 images
Cited rule: DLwP-2E ch9 — image segmentation is one of the three essential computer-vision tasks; encoder-decoder convnets with Conv2DTranspose upsampling are its canonical architecture

## Loss & activation
Last-layer activation: softmax
Loss: sparse_categorical_crossentropy
Metrics: mean IoU, per-pixel accuracy

## Evaluation protocol
Protocol: K-fold is impractical for dense prediction; holdout split with augmentation (5k samples)
Common-sense baseline: predict the most frequent class (background) for every pixel; the model must beat its mean IoU

## Workflow
1. Beat the common-sense baseline: establish statistical power before anything else.
2. Scale up: develop a model that overfits, to find the capacity ceiling.
3. Regularize and tune: dropout, weight decay, early stopping, then hyperparameter search — only after the baseline is beaten.

## Scope notes
In scope: covered directly by the book.
