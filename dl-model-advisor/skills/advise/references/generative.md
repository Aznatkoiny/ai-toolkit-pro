# Generative deep learning — routing depth + boundaries (ch12)

## What the book covers (2021 state of the art)

- **Text generation**: Transformer language model trained from scratch with
  temperature-based sampling (ch12). Softmax over vocabulary,
  sparse_categorical_crossentropy, sampling temperature as the
  creativity/coherence dial.
- **DeepDream** and **neural style transfer**: optimization-in-image-space
  techniques over pretrained convnets (InceptionV3 / VGG19 feature losses).
- **VAE** (variational autoencoder): continuous, structured latent space;
  good for concept-vector arithmetic and smooth interpolation; blurrier
  samples. Custom Layer with the reparameterization trick; loss =
  reconstruction + KL.
- **GAN** (DCGAN-style): sharper samples, notoriously unstable training —
  the ch12 "bag of tricks" (LeakyReLU, dropout in the discriminator, label
  noise) is required reading before attempting one.

Routing within scope: "generate images like my dataset" at 2021 tech →
VAE for structured latent-space control, GAN for sharpness; both need tens
of thousands of images and meaningful GPU budget. Set expectations honestly:
neither approaches modern diffusion quality.

## The boundary (state it, don't blur it)

Diffusion models, latent diffusion, text-to-image systems, and LLM-based
generation post-date the book. Requests for them get the OUT-OF-SCOPE plan
variant: cite VAE/GAN chapters as adjacent background only, produce no
starter script, and point at current literature. Do not present a VAE or
GAN as a diffusion substitute.

## Canonical pattern — VAE encoder sketch (ch12)

```python
import keras
from keras import layers

latent_dim = 2
inputs = keras.Input(shape=(28, 28, 1))
x = layers.Conv2D(32, 3, activation="relu", strides=2, padding="same")(inputs)
x = layers.Conv2D(64, 3, activation="relu", strides=2, padding="same")(x)
x = layers.Flatten()(x)
x = layers.Dense(16, activation="relu")(x)
z_mean = layers.Dense(latent_dim, name="z_mean")(x)
z_log_var = layers.Dense(latent_dim, name="z_log_var")(x)
```

Decoder mirrors with `Conv2DTranspose`; total loss = reconstruction +
KL(z_mean, z_log_var). Train via a custom `train_step` (ch12).

Text-generation and GAN patterns: see ch12 notebooks
(chapter12_part01_text-generation, chapter12_part05_gans) — both require
custom training loops; flag that complexity in the plan's Scope notes.
