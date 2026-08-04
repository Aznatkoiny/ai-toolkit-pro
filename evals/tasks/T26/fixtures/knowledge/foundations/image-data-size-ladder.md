---
type: Decision Rule
title: "Image data-size ladder"
description: "Dataset size decides pretrained feature extraction vs fine-tuning vs from-scratch."
tags: [routing, images, transfer-learning]
tier: book-canon
applies_to: "image classification"
sources:
  - id: dlwp2e-ch8
    resource: "../deep-learning-with-python/Deep_Learning_with_Python_Second_Editio (1).epub#OEBPS/Text/08.htm"
    title: "Deep Learning with Python 2E, chapter 8"
    author: F. Chollet
    last_modified: 2021-10-03
generated: {by: dl-model-advisor-pipeline/claude-fable-5, at: 2026-08-03T00:00:00Z}
verified:
  - {by: process:forge-eval-capability-v1, at: 2026-08-02T23:00:00Z}
status: stable
---

# Rule

| Labeled images | Approach |
|---|---|
| hundreds – few thousands | frozen pretrained base (VGG16/Xception) + small Dense head + augmentation; fine-tune the top block only after the head converges |
| tens of thousands | fine-tune deeper, or a compact convnet from scratch |
| hundreds of thousands+ | modern convnet from scratch: residual connections, batch normalization, separable convolutions |[^dlwp2e-ch8]

Augmentation (RandomFlip/Rotation/Zoom) is default below ~50k images.

[^dlwp2e-ch8]: DLwP-2E ch8, small-data regime and transfer learning; ch9
modern convnet patterns.
