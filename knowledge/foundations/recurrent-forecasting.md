---
type: Architecture Pattern
title: "Stacked recurrent forecaster (timeseries)"
description: "Stacked GRU/LSTM with recurrent_dropout over windowed sequences; normalize with training-period statistics only; always gate on the last-value naive b"
tags: [pattern, keras]
tier: book-canon
sources:
  - id: nb-recurrent-forecasting
    resource: ../chapter10_dl-for-timeseries.ipynb
    title: "chapter10_dl-for-timeseries.ipynb"
    author: F. Chollet
    last_modified: 2021-10-03
  - id: dlwp2e-ch10
    resource: "../Deep_Learning_with_Python_Second_Editio (1).epub#OEBPS/Text/10.htm"
    title: "Deep Learning with Python 2E, chapter 10"
    author: F. Chollet
    last_modified: 2021-10-03
generated: {by: dl-model-advisor-pipeline/claude-fable-5, at: 2026-08-03T00:00:00Z}
verified:
  - {by: process:forge-eval-capability-v1, at: 2026-08-02T23:00:00Z}
status: stable
stale_after: 2027-08-01
---

# Pattern

Stacked GRU/LSTM with recurrent_dropout over windowed sequences; normalize with training-period statistics only; always gate on the last-value naive baseline; chronological splits.[^nb-recurrent-forecasting]

Code is Keras 3 idiom, modernized from the book's TF/Keras 2.x notebooks at
build time — hence the `stale_after`: API drift, not content drift, is the
rot surface.

# Examples

```python
inputs = keras.Input(shape=(WINDOW, NUM_FEATURES))
x = layers.GRU(32, recurrent_dropout=0.25, return_sequences=True)(inputs)
x = layers.GRU(32, recurrent_dropout=0.25)(x)
x = layers.Dropout(0.25)(x)
outputs = layers.Dense(1)(x)
model.compile(optimizer="rmsprop", loss="mse", metrics=["mae"])
```

[^nb-recurrent-forecasting]: Companion notebook chapter10_dl-for-timeseries.ipynb; prose in DLwP-2E ch10.
