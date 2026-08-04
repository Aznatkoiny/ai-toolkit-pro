---
type: Architecture Pattern
title: "Bag-of-bigrams text classifier (low-ratio text)"
description: "TextVectorization(ngrams=2, output_mode='tf_idf') into a small Dense model with dropout; the low-ratio text workhorse."
tags: [pattern, keras]
tier: book-canon
sources:
  - id: nb-bag-of-bigrams-text
    resource: ../chapter11_part01_introduction.ipynb
    title: "chapter11_part01_introduction.ipynb"
    author: F. Chollet
    last_modified: 2021-10-03
  - id: dlwp2e-ch11
    resource: "../Deep_Learning_with_Python_Second_Editio (1).epub#OEBPS/Text/11.htm"
    title: "Deep Learning with Python 2E, chapter 11"
    author: F. Chollet
    last_modified: 2021-10-03
generated: {by: dl-model-advisor-pipeline/claude-fable-5, at: 2026-08-03T00:00:00Z}
verified:
  - {by: process:forge-eval-capability-v1, at: 2026-08-02T23:00:00Z}
status: stable
stale_after: 2027-08-01
---

# Pattern

TextVectorization(ngrams=2, output_mode='tf_idf') into a small Dense model with dropout; the low-ratio text workhorse.[^nb-bag-of-bigrams-text]

Code is Keras 3 idiom, modernized from the book's TF/Keras 2.x notebooks at
build time — hence the `stale_after`: API drift, not content drift, is the
rot surface.

# Examples

```python
from keras.layers import TextVectorization
vectorizer = TextVectorization(max_tokens=20000, ngrams=2,
                               output_mode="tf_idf")
inputs = keras.Input(shape=(20000,))
x = layers.Dense(16, activation="relu")(inputs)
x = layers.Dropout(0.5)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)
```

[^nb-bag-of-bigrams-text]: Companion notebook chapter11_part01_introduction.ipynb; prose in DLwP-2E ch11.
