# Consolidated decision rules — Deep Learning with Python 2E

The distilled rule set. Per-domain files (images/text/timeseries/tabular/
generative) carry depth and code patterns; this file is the cross-domain
router. Cite rules as `DLwP-2E ch<N> — <rule name>`.

## 1. Modality → architecture (ch14 "Key network architectures")

A network architecture encodes assumptions about the structure of the data —
a hypothesis space. Whether an architecture works depends entirely on the
match between the data's structure and the architecture's assumptions.

| Data | Architecture | Assumption exploited |
|---|---|---|
| Vector/tabular | Dense stack | none — no structure assumed |
| Images | 2D convnet | translation invariance, spatial hierarchy |
| Dense image prediction | Encoder-decoder convnet (`Conv2DTranspose`) | same, plus per-pixel output |
| Order-sensitive timeseries | RNN (`LSTM`/`GRU`) | temporal ordering carries signal |
| Discrete sequences (words, tokens) | Transformer | pairwise relevance (attention), order via positional info |
| Translation-invariant continuous sequences (audio waveforms) | 1D convnet | local patterns matter, position does not |
| Video | frame 2D convnet + sequence model, or 3D convnet | spatial + temporal |

## 2. Text: the ratio rule (ch11 — "when to use sequence models over bag-of-words")

`ratio = samples / mean_words_per_sample`
- **ratio < 1,500 → bag-of-bigrams** (TF-IDF) + Dense. Faster, stronger.
- **ratio > 1,500 → sequence model** (Transformer encoder / bi-LSTM over embeddings).

Never default to a Transformer because it is fashionable; compute the ratio
and show the arithmetic. This rule holds even for large corpora with long
documents (60k articles × 400 words ≈ 150 → still bag-of-bigrams).

## 3. Images: the dataset-size ladder (ch8)

- Hundreds–few thousands: pretrained convnet **feature extraction** (frozen
  base, e.g. VGG16/Xception) + small Dense head + augmentation; optionally
  fine-tune the top convolutional block after the head converges.
- Tens of thousands: fine-tune deeper, or train a compact convnet.
- Hundreds of thousands+: from scratch with modern patterns (ch9): residual
  connections, batch normalization, depthwise separable convs, GAP head.

## 4. Evaluation protocol by dataset size (ch5)

| Samples | Protocol |
|---|---|
| < ~500 | Iterated K-fold with shuffling |
| ~500 – ~10,000 | K-fold cross-validation |
| > ~10,000 | Simple holdout |

Timeseries always uses chronological splits (train past → validate future),
regardless of size. Never shuffle time.

## 5. Last-layer activation + loss (ch6 table — exact)

| Task type | Activation | Loss |
|---|---|---|
| binary classification | sigmoid | binary_crossentropy |
| multiclass single-label classification | softmax | categorical_crossentropy / sparse_categorical_crossentropy |
| multilabel classification | sigmoid | binary_crossentropy |
| scalar regression | none | mse |

Metrics discipline: regression → MAE (never accuracy); imbalanced
classification → precision/recall/ROC AUC (accuracy misleads); multilabel →
per-label precision/recall.

## 6. Universal workflow (ch6) — fixed order

1. **Beat a common-sense baseline** (majority class, base rates, last-value).
   No result is meaningful before this — statistical power first.
2. **Scale up: develop a model that overfits.** Find the capacity ceiling —
   if you cannot overfit, the model is under-powered or the data broken.
3. **Regularize and tune.** Dropout, L2, early stopping, capacity reduction,
   data curation; hyperparameter search (KerasTuner) LAST (ch13).

## 7. Small-data discipline (ch5)

Little data → shrink capacity, regularize hard (L2 + dropout), feature
normalization always, and prefer transfer learning where a pretrained base
exists. The manifold hypothesis does not rescue a 240-row dataset.

## 8. Scope boundary (2021)

The book does not cover: LLM fine-tuning / LoRA / instruction tuning,
diffusion models, RL, GNNs, recommenders. Out-of-scope requests get the
canonical OUT-OF-SCOPE plan variant and no starter code; in-book material is
offered only as clearly-labeled adjacent background.
