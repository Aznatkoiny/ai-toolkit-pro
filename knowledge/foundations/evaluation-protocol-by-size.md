---
type: Decision Rule
title: "Evaluation protocol by dataset size"
description: "Holdout vs K-fold vs iterated K-fold is a dataset-size decision; timeseries always splits chronologically."
tags: [evaluation, protocol]
tier: book-canon
applies_to: "every supervised problem"
sources:
  - id: dlwp2e-ch5
    resource: "../Deep_Learning_with_Python_Second_Editio (1).epub#OEBPS/Text/05.htm"
    title: "Deep Learning with Python 2E, chapter 5"
    author: F. Chollet
    last_modified: 2021-10-03
generated: {by: dl-model-advisor-pipeline/claude-fable-5, at: 2026-08-03T00:00:00Z}
verified:
  - {by: process:forge-eval-capability-v1, at: 2026-08-02T23:00:00Z}
status: stable
---

# Rule

| Samples | Protocol |
|---|---|
| < ~500 | iterated K-fold with shuffling |
| ~500 – ~10,000 | K-fold cross-validation |
| > ~10,000 | simple holdout |[^dlwp2e-ch5]

Timeseries always uses chronological splits (train past → validate future);
never shuffle time regardless of size.

[^dlwp2e-ch5]: DLwP-2E ch5, evaluation protocols.
