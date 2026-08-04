# Vector / tabular data — routing depth + canonical patterns (ch4, ch5, ch14)

## The decision procedure

1. Vector data assumes no structure → **Dense stack** (ch14). Depth and
   width scale with data size; two hidden layers of 16–64 units cover most
   tabular problems in the book's range.
2. **Normalize every feature** (zero mean, unit variance, training-set
   statistics only). Heterogeneous-scale features cripple gradient descent
   (ch4 Boston Housing).
3. **Capacity follows data size** (ch5): tiny datasets (≤ a few hundred
   rows) get the smallest network that can beat the baseline, strong L2 +
   dropout; do not add layers before the baseline is beaten.
4. Protocol by size (ch5): <~500 → iterated K-fold; ~500–10k → K-fold;
   >10k → holdout. The ch4 Boston example (404 samples) is the canonical
   K-fold regression case.
5. Pairings (ch6): binary → sigmoid + binary_crossentropy; multiclass →
   softmax + (sparse_)categorical_crossentropy; regression → none + mse
   (metric MAE, never accuracy). Imbalanced problems (fraud, churn) report
   ROC AUC / precision-recall; accuracy misleads.
6. Baselines: majority class (classification), training-mean prediction
   (regression), per-label base rates (multilabel).

Honest scope note: for many small tabular problems, gradient-boosted trees
are the practical winner — the book itself concedes deep learning is not
always the right tool (ch14). Recommend Dense as the book-grounded deep
approach; note the caveat in Scope notes when rows < ~1k.

## Canonical pattern — small tabular classifier

```python
import keras
from keras import layers

inputs = keras.Input(shape=(NUM_FEATURES,))
x = layers.Dense(16, activation="relu")(inputs)
x = layers.Dropout(0.4)(x)
x = layers.Dense(16, activation="relu")(x)
x = layers.Dropout(0.4)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)
model = keras.Model(inputs, outputs)
model.compile(optimizer="rmsprop", loss="binary_crossentropy",
              metrics=["accuracy", keras.metrics.AUC(name="roc_auc")])
```

Regression variant: final `Dense(1)` with no activation, `loss="mse"`,
`metrics=["mae"]`. Multiclass variant: `Dense(N, activation="softmax")` +
sparse_categorical_crossentropy.

## K-fold sketch (ch4)

Split into K folds; train K models each holding one fold out; report the
mean validation score. Iterated K-fold repeats this over multiple shuffles
and averages — the tiny-data protocol (ch5).
