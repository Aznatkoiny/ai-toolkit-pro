---
type: Decision Rule
title: "Universal workflow (baseline → overfit → regularize)"
description: "The fixed ordering of model development; tuning never precedes a beaten baseline."
tags: [workflow, methodology]
tier: book-canon
applies_to: "every model-development effort"
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

1. **Beat a common-sense baseline** (majority class, base rates, last-value).
   No result means anything before this — statistical power first.
2. **Scale up: develop a model that overfits** to find the capacity ceiling.
3. **Regularize and tune**: dropout, L2, early stopping, curation;
   hyperparameter search last.[^dlwp2e-ch6]

Small-data corollary (ch5): with very little data, shrink capacity and
regularize hard; prefer transfer learning where a pretrained base exists.

[^dlwp2e-ch6]: DLwP-2E ch6, "The universal workflow of machine learning".
