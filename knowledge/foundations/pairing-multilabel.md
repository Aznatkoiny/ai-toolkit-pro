---
type: Task Pairing
title: "Pairing: multilabel classification"
description: "Last-layer activation and loss for multilabel classification, per the ch6 table."
tags: [pairing, loss, activation]
tier: book-canon
task_type: "multilabel classification"
activation: "sigmoid"
loss: ['binary_crossentropy']
metrics: "per-label precision/recall"
sources:
  - id: dlwp2e-ch6
    resource: "../Deep_Learning_with_Python_Second_Editio (1).epub#OEBPS/Text/06.htm"
    title: "Deep Learning with Python 2E, chapter 6"
    author: F. Chollet
    last_modified: 2021-10-03
generated: {by: dl-model-advisor-pipeline/claude-fable-5, at: 2026-08-03T00:00:00Z}
verified:
  - {by: process:forge-eval-capability-v1, at: 2026-08-02T23:00:00Z}
status: stable
---

# Rule

For **multilabel classification**: last-layer activation **sigmoid**, loss **binary_crossentropy**
(alternatives: none). Metrics: per-label precision/recall.[^dlwp2e-ch6]

This row is machine-consumed: the plugin's `data/pairings.json` is generated
from the `task_type` / `activation` / `loss` fields above (drift-checked by
eval CI-03 and task T11).

[^dlwp2e-ch6]: DLwP-2E ch6, "Choosing the right last-layer activation and
loss function" table.
