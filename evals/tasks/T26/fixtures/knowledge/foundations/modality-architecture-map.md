---
type: Decision Rule
title: "Modality → architecture map"
description: "Which architecture family each data modality maps to, and why."
tags: [routing, architecture]
tier: book-canon
applies_to: "any problem with a known data modality"
sources:
  - id: dlwp2e-ch14
    resource: "../deep-learning-with-python/Deep_Learning_with_Python_Second_Editio (1).epub#OEBPS/Text/14.htm"
    title: "Deep Learning with Python 2E, chapter 14"
    author: F. Chollet
    last_modified: 2021-10-03
generated: {by: dl-model-advisor-pipeline/claude-fable-5, at: 2026-08-03T00:00:00Z}
verified:
  - {by: process:forge-eval-capability-v1, at: 2026-08-02T23:00:00Z}
status: stable
---

# Rule

An architecture encodes assumptions about data structure — a hypothesis
space. Route by matching structure to assumptions:[^dlwp2e-ch14]

| Data | Architecture | Assumption exploited |
|---|---|---|
| Vector/tabular | Dense stack | none — no structure assumed |
| Images | 2D convnet | translation invariance, spatial hierarchy |
| Dense image prediction | Encoder-decoder convnet (Conv2DTranspose) | per-pixel output |
| Order-sensitive timeseries | RNN (LSTM/GRU) | temporal ordering carries signal |
| Discrete sequences (text) | Transformer | pairwise relevance via attention |
| Translation-invariant continuous sequences (audio) | 1D convnet | local patterns, position-free |
| Video | frame 2D convnet + sequence model, or 3D convnet | spatial + temporal |

Related: [text ratio rule](/foundations/text-ratio-rule.md),
[image data-size ladder](/foundations/image-data-size-ladder.md).

[^dlwp2e-ch14]: DLwP-2E ch14, "Key network architectures".
