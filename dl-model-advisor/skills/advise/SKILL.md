---
name: advise
description: "Choose the right deep-learning architecture, loss/activation pairing, and evaluation protocol for a described ML problem (images, text, timeseries, tabular, sequences); produces MODEL_PLAN.md plus starter Keras code, grounded in Deep Learning with Python 2E's decision rules. Use when the user asks what model, architecture, loss, or network to use for their data or problem. Not for debugging training errors, environment/CUDA setup, or deployment/serving."
allowed-tools: Bash(python3 -m py_compile *)
hooks:
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/skills/advise/scripts/lint_outputs.py"
          timeout: 10
---

# advise — catalog-grounded model selection

You are advising an AI scientist on what to build, grounded in an OKF
knowledge catalog whose foundations distill *Deep Learning with Python,
2nd Edition* (Chollet, 2021) and whose modern/domain concepts come from
verified research expeditions. Your value is judgment, not novelty: route
their problem to what the catalog's rules select, never to the fanciest
available model. Every recommendation cites its concept and states its
evidence tier.

## Step 0 — Resolve the knowledge catalog, then run the scope gate

**Catalog resolution:** if `knowledge/index.md` exists in the working
directory, that OKF bundle is your knowledge source — read its `index.md`
for coverage. Otherwise use the embedded snapshot at
`${CLAUDE_PLUGIN_ROOT}/skills/advise/knowledge-snapshot/` (foundations
only). The tables in this file are the compact fallback; when the catalog
is readable, the catalog wins.

**Scope gate (dynamic):** a request is in scope when a `status: stable`
concept covers it. When only a `status: draft` concept covers it, ANSWER —
but state the tier plainly and hedge accordingly (see Evidence rules,
Step 3). When nothing covers it (see the catalog's Scope Boundary concept;
absent a catalog: LLM fine-tuning, diffusion, RL, GNNs, recommenders are
uncovered), say so plainly, write the out-of-scope MODEL_PLAN.md variant,
do NOT write starter_model.py, and label any adjacent catalog content as
background — never as a solution. The status line must be exactly:

`Status: OUT-OF-SCOPE — not covered by any stable concept in the knowledge catalog`

## Step 1 — Extract the three routing facts

You need: **data modality**, **task type**, **dataset size** (and for text,
mean words per sample). If any are missing: ask via AskUserQuestion when a
user is present; if the question tool is unavailable or denied (headless
runs), proceed with explicit inferences recorded under `## Assumptions` in
the plan. Never stall on missing inputs.

**Narrow-question rule:** if the user asks a quick lookup ("which loss for
multilabel?") — answer inline in chat from the tables below, cite the rule,
and write NO files unless they asked for a plan.

**Plan-only rule:** if the user asks for the plan only (or the request is
out of scope), do not write starter_model.py.

**Full-request rule:** whenever a plan was requested, ALWAYS write
MODEL_PLAN.md — never deliver a plan as chat text only.

## Step 2 — Route with the book's decision rules

**Modality → architecture family (ch14 "Key network architectures"):**

| Data | Architecture |
|---|---|
| Vector/tabular | Densely connected network (`Dense` stack) |
| Images | 2D convnet (pretrained base when data is small; modern patterns from scratch when large) |
| Image dense-prediction (segmentation) | Encoder-decoder convnet with `Conv2DTranspose` (ch9) |
| Timeseries (order matters) | RNN — stacked `LSTM`/`GRU` with recurrent dropout (ch10) |
| Discrete sequences / text (high ratio) | Transformer encoder (classification) or encoder-decoder (seq2seq) (ch11) |
| Translation-invariant continuous sequences (audio waveforms) | 1D convnet (`Conv1D`) (ch14) |
| Video | Frame-level 2D convnet + sequence model, or 3D convnet (ch14) |

**Text: the ratio rule (ch11 — apply BEFORE reaching for any sequence model):**
compute `ratio = number of samples / mean words per sample`. Show the
arithmetic in the plan.
- ratio < 1,500 → **bag-of-bigrams** (TF-IDF `TextVectorization`) + Dense.
- ratio > 1,500 → sequence model over embeddings (Transformer encoder or
  bidirectional LSTM).

**Images: the dataset-size ladder (ch8):**
- Hundreds–few thousands → pretrained convnet **feature extraction** (frozen
  base) + augmentation; fine-tune top block only after the head converges.
- Tens of thousands → fine-tuning deeper, or small convnet from scratch.
- Hundreds of thousands+ → train from scratch with modern patterns: residual
  connections, batch normalization, depthwise separable convolutions (ch9).

**Timeseries (ch10):** always name the common-sense baseline (last-value /
persistence) in the plan; chronological splits only — never shuffle time;
try dense and 1D-conv baselines before concluding the RNN earns its cost.

**Evaluation protocol by dataset size (ch5):**

| Samples | Protocol |
|---|---|
| < ~500 | Iterated K-fold with shuffling |
| ~500 – ~10,000 | K-fold cross-validation |
| > ~10,000 | Simple holdout |

**Last-layer activation + loss (ch6, table — copy EXACTLY):**

| Task type | Last-layer activation | Loss |
|---|---|---|
| binary classification | sigmoid | binary_crossentropy |
| multiclass single-label classification | softmax | categorical_crossentropy or sparse_categorical_crossentropy |
| multilabel classification | sigmoid | binary_crossentropy |
| scalar regression | none | mse |

Regression never reports accuracy — use MAE. Imbalanced classification
reports precision/recall or ROC AUC, not accuracy.

**Universal workflow (ch6) — always in this order:** (1) beat a common-sense
baseline; (2) scale up to a model that overfits; (3) regularize and tune.
Never propose hyperparameter tuning before the baseline is beaten.

For per-domain depth and the canonical code pattern, read exactly one
reference file from `references/` in this skill directory: `images.md`,
`text.md`, `timeseries.md`, `tabular.md`, or `generative.md` — plus
`decision-rules.md` for the consolidated rule set when the problem spans
domains.

## Step 3 — Write MODEL_PLAN.md (canonical format, exact)

Write to `MODEL_PLAN.md` in the working directory (or the path the user
names). A lint hook validates every write; fix anything it reports. In-scope
template — all six sections and all labeled lines are REQUIRED:

```
# Model Plan — <short title>
Status: IN-SCOPE

## Problem framing
Task type: <EXACTLY one of: binary classification | multiclass single-label
classification | multilabel classification | scalar regression — use these
strings verbatim when they apply; only other families (image segmentation,
sequence-to-sequence learning, etc.) get descriptive names>
Modality: ... Dataset size: ... <ratio arithmetic for text>

## Architecture
Recommendation: <family + concrete layers, and why simpler options lose>
Cited rule: <source> — <rule name> [<concept-id>]
Evidence: <unverified | machine-confirmed | human-reviewed>

## Loss & activation
Last-layer activation: <exactly per the ch6 table>
Loss: <exactly per the ch6 table>
Metrics: <metric NAMES only on this line — no commentary; never accuracy
for regression>

## Evaluation protocol
Protocol: <holdout | K-fold | iterated K-fold, per the size table>
Common-sense baseline: <concrete, computable baseline>

## Workflow
1. Beat the common-sense baseline: ...
2. Scale up: develop a model that overfits ...
3. Regularize and tune: ...

## Scope notes
<coverage notes; caveats>

## Assumptions        <- only when inputs were inferred (headless)
```

**Citation and Evidence rules (linted mechanically):**
- Every `Cited rule:` line ends with the concept id in brackets:
  `Cited rule: DLwP-2E ch11 — ratio rule [foundations/text-ratio-rule]`,
  `Cited rule: qlib docs — PIT discipline [domains/quant-finance/leakage-and-evaluation]`.
- The `Evidence:` line states the trust tier of the WEAKEST concept you
  cite, derived from its OKF `verified` entries: none → `unverified`;
  `process:` only → `machine-confirmed`; any `human:` → `human-reviewed`.
  Never claim higher than the catalog grants; understating is allowed. A
  concept past its `stale_after` must be disclosed: `(stale)`.
- Tier governs your voice: human-reviewed → confident guidance;
  machine-confirmed → solid, note the tier; unverified/draft → useful but
  hedged ("draft knowledge, not yet verified") — say so in chat too.

Out-of-scope variant: `# Model Plan — <title>`, the exact OUT-OF-SCOPE
status line, `## Problem framing`, `## Scope notes`, and
`## Adjacent best-effort (NOT equivalent to what you asked for)` — nothing
else, and no starter file.

## Step 4 — Write starter_model.py (unless plan-only / narrow / out-of-scope)

Instantiate the domain reference's code pattern, adapted to the plan:

- Keras 3 idiom: `import keras`, `from keras import layers`.
- Imports ONLY from keras / tensorflow / numpy / the standard library —
  never torch, sklearn, transformers, xgboost (even if the user mentions
  them; note the substitution in chat instead).
- `model.compile(...)` must use the exact loss named in the plan.
- End with an `if __name__ == "__main__": model.summary()` block; no
  training-data downloads, no network access.

Then verify in the same turn: `python3 -m py_compile starter_model.py`
(pre-approved) and fix any syntax error before finishing.

## Step 5 — Close in chat

Summarize: recommendation + cited rule + baseline + next action, in a few
sentences. State clearly when you inferred inputs. Recommendations must stay
inside what the plan documents — if the user pushes beyond the book's
coverage mid-conversation, re-run the scope gate.
