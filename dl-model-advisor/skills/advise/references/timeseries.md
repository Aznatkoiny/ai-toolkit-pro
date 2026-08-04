# Timeseries — routing depth + canonical patterns (ch10)

## Task kinds (ch10)

Forecasting (the chapter's focus), classification, anomaly detection, event
detection. All share the windowed-sequence input shape `(window, features)`.

## The decision procedure

1. **Name the common-sense baseline FIRST** — for forecasting, the naive
   last-value/persistence baseline: predict x(t+Δ) = x(t). The book's Jena
   temperature case shows this baseline embarrassing many fancy models;
   every plan must state it and the model must beat its MAE.
2. **Chronological splits only.** Train on the past, validate on the future.
   Never shuffle time — shuffling leaks the future and fabricates skill.
3. **Escalation ladder** (each rung must beat the last): naive baseline →
   dense model on flattened windows → 1D convnet → recurrent model
   (`LSTM`/`GRU`) → stacked/bidirectional RNN with recurrent dropout.
   The RNN must EARN its cost by beating the cheap rungs.
4. 1D convnets suit patterns where position in the window doesn't matter;
   order-sensitive dynamics (weather, demand) favor RNNs (ch10's comparison:
   the 1D convnet underperforms the GRU on Jena precisely because weather
   data ordering matters).
5. Forecasting a continuous value = scalar regression: activation none,
   loss mse, metric MAE. Timeseries classification pairs per the ch6 table.

## Canonical pattern — stacked GRU forecaster

```python
import keras
from keras import layers

inputs = keras.Input(shape=(WINDOW, NUM_FEATURES))
x = layers.GRU(32, recurrent_dropout=0.25, return_sequences=True)(inputs)
x = layers.GRU(32, recurrent_dropout=0.25)(x)
x = layers.Dropout(0.25)(x)
outputs = layers.Dense(1)(x)
model = keras.Model(inputs, outputs)
model.compile(optimizer="rmsprop", loss="mse", metrics=["mae"])
```

Windowing: build `(window, features)` samples with a stride; normalize each
feature using TRAINING-period statistics only (computing normalization over
the full series is a leak).

## Regularization specifics (ch10)

Use `recurrent_dropout` (the recurrent-state variant) rather than plain
dropout between recurrent layers; stack a second recurrent layer only after
the first overfits; `Bidirectional` helps text more than strict forecasting
(the future is unavailable at inference for forecasting — don't use it).
