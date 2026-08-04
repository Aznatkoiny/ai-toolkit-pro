---
type: Architecture Pattern
title: "Pretrained feature extraction (images, small data)"
description: "Frozen Xception/VGG16 base + augmentation + GlobalAveragePooling2D + Dense head; keep training=False on the base call; fine-tune the top block at low "
tags: [pattern, keras]
tier: book-canon
sources:
  - id: nb-pretrained-feature-extraction
    resource: ../chapter08_intro-to-dl-for-computer-vision.ipynb
    title: "chapter08_intro-to-dl-for-computer-vision.ipynb"
    author: F. Chollet
    last_modified: 2021-10-03
  - id: dlwp2e-ch8
    resource: "../Deep_Learning_with_Python_Second_Editio (1).epub#OEBPS/Text/08.htm"
    title: "Deep Learning with Python 2E, chapter 8"
    author: F. Chollet
    last_modified: 2021-10-03
generated: {by: dl-model-advisor-pipeline/claude-fable-5, at: 2026-08-03T00:00:00Z}
verified:
  - {by: process:forge-eval-capability-v1, at: 2026-08-02T23:00:00Z}
status: stable
stale_after: 2027-08-01
---

# Pattern

Frozen Xception/VGG16 base + augmentation + GlobalAveragePooling2D + Dense head; keep training=False on the base call; fine-tune the top block at low LR only after the head converges.[^nb-pretrained-feature-extraction]

Code is Keras 3 idiom, modernized from the book's TF/Keras 2.x notebooks at
build time — hence the `stale_after`: API drift, not content drift, is the
rot surface.

# Examples

```python
import keras
from keras import layers

base = keras.applications.Xception(weights="imagenet", include_top=False,
                                   input_shape=(180, 180, 3))
base.trainable = False
inputs = keras.Input(shape=(180, 180, 3))
x = keras.applications.xception.preprocess_input(inputs)
x = base(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
outputs = layers.Dense(NUM_CLASSES, activation="softmax")(x)
model = keras.Model(inputs, outputs)
model.compile(optimizer="rmsprop", loss="sparse_categorical_crossentropy",
              metrics=["accuracy"])
```

[^nb-pretrained-feature-extraction]: Companion notebook chapter08_intro-to-dl-for-computer-vision.ipynb; prose in DLwP-2E ch8.
