---
type: Task Pairing
title: "Pairing: multiclass single-label classification"
description: "Last-layer activation and loss for multiclass single-label classification, per the ch6 table."
tags: [pairing, loss, activation]
tier: book-canon
task_type: "multiclass single-label classification"
activation: "softmax"
loss: ['categorical_crossentropy', 'sparse_categorical_crossentropy']
metrics: "accuracy"
sources:
  - id: dlwp2e-ch6
    resource: "../deep-learning-with-python/Deep_Learning_with_Python_Second_Editio (1).epub#OEBPS/Text/06.htm"
    title: "Deep Learning with Python 2E, chapter 6"
    author: F. Chollet
    last_modified: 2021-10-03
generated: {by: dl-model-advisor-pipeline/claude-fable-5, at: 2026-08-03T00:00:00Z}
verified:
  - {by: process:forge-eval-capability-v1, at: 2026-08-02T23:00:00Z}
status: stable
---

# Rule

For **multiclass single-label classification**: last-layer activation **softmax**, loss **categorical_crossentropy**
(alternatives: sparse_categorical_crossentropy). Metrics: accuracy.[^dlwp2e-ch6]

This row is machine-consumed: the plugin's `data/pairings.json` is generated
from the `task_type` / `activation` / `loss` fields above (drift-checked by
eval CI-03 and task T11).

[^dlwp2e-ch6]: DLwP-2E ch6, "Choosing the right last-layer activation and
loss function" table.
