---
type: Decision Rule
title: "Text ratio rule (1,500 threshold)"
description: "samples / mean words per sample decides bag-of-bigrams vs sequence model."
tags: [routing, text, nlp]
tier: book-canon
applies_to: "text classification and tagging"
sources:
  - id: dlwp2e-ch11
    resource: "../Deep_Learning_with_Python_Second_Editio (1).epub#OEBPS/Text/11.htm"
    title: "Deep Learning with Python 2E, chapter 11"
    author: F. Chollet
    last_modified: 2021-10-03
generated: {by: dl-model-advisor-pipeline/claude-fable-5, at: 2026-08-03T00:00:00Z}
verified:
  - {by: process:forge-eval-capability-v1, at: 2026-08-02T23:00:00Z}
status: stable
---

# Rule

Compute `ratio = samples / mean_words_per_sample` and show the arithmetic.

- **ratio < 1,500** → bag-of-bigrams (TF-IDF TextVectorization) + Dense.
  Faster, and it wins at low ratios.
- **ratio > 1,500** → sequence model over embeddings (Transformer encoder;
  bidirectional LSTM as the lighter option).[^dlwp2e-ch11]

Never default to a Transformer because it is fashionable. The rule holds for
large corpora with long documents (60k articles × 400 words ≈ 150 → still
bag-of-bigrams).

[^dlwp2e-ch11]: DLwP-2E ch11, "When to use sequence models over
bag-of-words models".
