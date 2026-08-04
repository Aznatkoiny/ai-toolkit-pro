# Text — routing depth + canonical patterns (ch11)

## The decision procedure (always in this order)

1. Compute `ratio = samples / mean_words_per_sample`. Show the arithmetic.
2. **ratio < 1,500** → bag-of-bigrams TF-IDF + Dense. Do not apologize for
   it: at low ratios it beats sequence models and trains orders of magnitude
   faster.
3. **ratio > 1,500** → sequence model over learned embeddings: Transformer
   encoder for classification; bidirectional LSTM is the lighter alternative;
   Transformer encoder-decoder for seq2seq (translation, summarization).
4. Pretrained word embeddings (GloVe) help only when training data is too
   small to learn embeddings (ch11) — note it, don't default to it.

Pairings: binary → sigmoid + binary_crossentropy; single-label multiclass →
softmax + (sparse_)categorical_crossentropy; multilabel → sigmoid +
binary_crossentropy (one independent decision per label).

## Canonical pattern — bag-of-bigrams (low ratio)

```python
import keras
from keras import layers
from keras.layers import TextVectorization

vectorizer = TextVectorization(max_tokens=20000, ngrams=2,
                               output_mode="tf_idf")
# vectorizer.adapt(text_only_dataset)
inputs = keras.Input(shape=(20000,))
x = layers.Dense(16, activation="relu")(inputs)
x = layers.Dropout(0.5)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)
model = keras.Model(inputs, outputs)
model.compile(optimizer="rmsprop", loss="binary_crossentropy",
              metrics=["accuracy"])
```

## Canonical pattern — Transformer encoder classifier (high ratio)

```python
class TransformerEncoder(layers.Layer):
    def __init__(self, embed_dim, dense_dim, num_heads, **kw):
        super().__init__(**kw)
        self.attention = layers.MultiHeadAttention(num_heads=num_heads,
                                                   key_dim=embed_dim)
        self.dense_proj = keras.Sequential([
            layers.Dense(dense_dim, activation="relu"),
            layers.Dense(embed_dim)])
        self.norm1 = layers.LayerNormalization()
        self.norm2 = layers.LayerNormalization()

    def call(self, inputs, mask=None):
        attn = self.attention(inputs, inputs)
        proj_in = self.norm1(inputs + attn)
        return self.norm2(proj_in + self.dense_proj(proj_in))
```

Embed tokens + positions (`Embedding(vocab, dim)` + `Embedding(seq_len,
dim)` added), one or two encoder blocks, `GlobalMaxPooling1D`, dropout,
task-appropriate output layer.

## Seq2seq (translation)

Transformer encoder over source + decoder with causal self-attention and
cross-attention; loss sparse_categorical_crossentropy over target tokens;
report next-token accuracy plus BLEU spot checks. The GRU-based seq2seq is
the simpler teaching baseline; the Transformer wins at 100k+ pairs.

## Baselines

Majority class for classification; copy-source for translation between
related languages. State them in the plan's Common-sense baseline line.
