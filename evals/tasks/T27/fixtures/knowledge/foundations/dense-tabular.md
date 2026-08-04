---
type: Architecture Pattern
title: "Dense network for vector/tabular data"
description: "Two hidden Dense layers (16-64 units) with dropout over normalized features; capacity follows data size; K-fold validation for small samples (the Bost"
tags: [pattern, keras]
tier: book-canon
sources:
  - id: nb-dense-tabular
    resource: ../deep-learning-with-python/chapter04_getting-started-with-neural-networks.ipynb
    title: "chapter04_getting-started-with-neural-networks.ipynb"
    author: F. Chollet
    last_modified: 2021-10-03
  - id: dlwp2e-ch4
    resource: "../deep-learning-with-python/Deep_Learning_with_Python_Second_Editio (1).epub#OEBPS/Text/04.htm"
    title: "Deep Learning with Python 2E, chapter 4"
    author: F. Chollet
    last_modified: 2021-10-03
generated: {by: dl-model-advisor-pipeline/claude-fable-5, at: 2026-08-03T00:00:00Z}
verified:
  - {by: process:forge-eval-capability-v1, at: 2026-08-02T23:00:00Z}
status: stable
stale_after: 2027-08-01
---

# Pattern

Two hidden Dense layers (16-64 units) with dropout over normalized features; capacity follows data size; K-fold validation for small samples (the Boston Housing pattern).[^nb-dense-tabular]

Code is Keras 3 idiom, modernized from the book's TF/Keras 2.x notebooks at
build time — hence the `stale_after`: API drift, not content drift, is the
rot surface.

# Examples

```python
inputs = keras.Input(shape=(NUM_FEATURES,))
x = layers.Dense(16, activation="relu")(inputs)
x = layers.Dropout(0.4)(x)
x = layers.Dense(16, activation="relu")(x)
x = layers.Dropout(0.4)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)   # or Dense(1) + mse
```

[^nb-dense-tabular]: Companion notebook chapter04_getting-started-with-neural-networks.ipynb; prose in DLwP-2E ch4.
