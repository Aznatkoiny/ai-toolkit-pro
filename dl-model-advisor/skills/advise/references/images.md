# Images — routing depth + canonical patterns (ch8, ch9)

## Task taxonomy (ch9: "three essential computer vision tasks")

- **Classification** → convnet, size-laddered (below).
- **Semantic segmentation** → encoder-decoder convnet: Conv2D downstack,
  `Conv2DTranspose` upstack, per-pixel softmax. Loss: (sparse_)categorical_
  crossentropy; metric: mean IoU.
- **Object detection** → named in the book but not implemented; recommend an
  established detector framework and mark the plan's Scope notes accordingly.

## Classification by dataset size (ch8)

| Size | Approach |
|---|---|
| ~100s–few 1,000s | Frozen pretrained base (VGG16/Xception) + Dense head + augmentation; then fine-tune top block, low LR |
| ~10k–100k | Fine-tune more of the base, or compact modern convnet from scratch |
| 100k+ | Modern convnet from scratch (ch9): residual blocks, BatchNormalization, SeparableConv2D, GlobalAveragePooling2D head |

Augmentation is the default for anything under ~50k images: RandomFlip,
RandomRotation, RandomZoom. Baselines: majority class; for segmentation,
all-background per pixel.

## Canonical pattern — small-data feature extraction (Keras 3)

```python
import keras
from keras import layers

augment = keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.2),
])
base = keras.applications.Xception(weights="imagenet", include_top=False,
                                   input_shape=(180, 180, 3))
base.trainable = False
inputs = keras.Input(shape=(180, 180, 3))
x = augment(inputs)
x = keras.applications.xception.preprocess_input(x)
x = base(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.25)(x)
outputs = layers.Dense(NUM_CLASSES, activation="softmax")(x)
model = keras.Model(inputs, outputs)
model.compile(optimizer="rmsprop", loss="sparse_categorical_crossentropy",
              metrics=["accuracy"])
```

## Canonical pattern — modern convnet from scratch (ch9 mini-Xception)

```python
def conv_block(x, filters):
    residual = x
    x = layers.Activation("relu")(x)
    x = layers.SeparableConv2D(filters, 3, padding="same", use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.SeparableConv2D(filters, 3, padding="same", use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D(3, strides=2, padding="same")(x)
    residual = layers.Conv2D(filters, 1, strides=2, padding="same",
                             use_bias=False)(residual)
    return layers.add([x, residual])
```

## Canonical pattern — segmentation encoder-decoder (ch9)

Downsample with strided Conv2D (padding="same"), upsample with mirrored
Conv2DTranspose stack, final `Conv2D(num_classes, 3, activation="softmax",
padding="same")`. Compile with sparse_categorical_crossentropy.

## Fine-tuning rules (ch8)

Freeze the base until the new head converges (else large random gradients
destroy pretrained features). Then unfreeze the top block only, LR ~1e-5.
Always keep `training=False` on the frozen base call so BatchNorm stays in
inference mode.
