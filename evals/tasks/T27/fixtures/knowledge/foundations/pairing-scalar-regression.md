---
type: Task Pairing
title: "Pairing: scalar regression"
description: "Last-layer activation and loss for scalar regression, per the ch6 table."
tags: [pairing, loss, activation]
tier: book-canon
task_type: "scalar regression"
activation: "none"
loss: ['mse', 'mean_squared_error']
metrics: "mae — never accuracy"
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

For **scalar regression**: last-layer activation **none**, loss **mse**
(alternatives: mean_squared_error). Metrics: mae — never accuracy.[^dlwp2e-ch6]

This row is machine-consumed: the plugin's `data/pairings.json` is generated
from the `task_type` / `activation` / `loss` fields above (drift-checked by
eval CI-03 and task T11).

[^dlwp2e-ch6]: DLwP-2E ch6, "Choosing the right last-layer activation and
loss function" table.
