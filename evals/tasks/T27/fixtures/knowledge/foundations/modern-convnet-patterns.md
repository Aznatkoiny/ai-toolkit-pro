---
type: Architecture Pattern
title: "Modern convnet from scratch (residual + separable + batchnorm)"
description: "Mini-Xception: residual blocks of SeparableConv2D + BatchNormalization, strided max-pooling, GlobalAveragePooling2D head. For large image datasets tra"
tags: [pattern, keras]
tier: book-canon
sources:
  - id: nb-modern-convnet-patterns
    resource: ../deep-learning-with-python/chapter09_part02_modern-convnet-architecture-patterns.ipynb
    title: "chapter09_part02_modern-convnet-architecture-patterns.ipynb"
    author: F. Chollet
    last_modified: 2021-10-03
  - id: dlwp2e-ch9
    resource: "../deep-learning-with-python/Deep_Learning_with_Python_Second_Editio (1).epub#OEBPS/Text/09.htm"
    title: "Deep Learning with Python 2E, chapter 9"
    author: F. Chollet
    last_modified: 2021-10-03
generated: {by: dl-model-advisor-pipeline/claude-fable-5, at: 2026-08-03T00:00:00Z}
verified:
  - {by: process:forge-eval-capability-v1, at: 2026-08-02T23:00:00Z}
status: stable
stale_after: 2027-08-01
---

# Pattern

Mini-Xception: residual blocks of SeparableConv2D + BatchNormalization, strided max-pooling, GlobalAveragePooling2D head. For large image datasets trained from scratch.[^nb-modern-convnet-patterns]

Code is Keras 3 idiom, modernized from the book's TF/Keras 2.x notebooks at
build time — hence the `stale_after`: API drift, not content drift, is the
rot surface.

# Examples

```python
def conv_block(x, filters):
    residual = x
    x = layers.Activation("relu")(x)
    x = layers.SeparableConv2D(filters, 3, padding="same", use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.SeparableConv2D(filters, 3, padding="same", use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D(3, strides=2, padding="same")(x)
    residual = layers.Conv2D(filters, 1, strides=2, padding="same",
                             use_bias=False)(residual)
    return layers.add([x, residual])
```

[^nb-modern-convnet-patterns]: Companion notebook chapter09_part02_modern-convnet-architecture-patterns.ipynb; prose in DLwP-2E ch9.
