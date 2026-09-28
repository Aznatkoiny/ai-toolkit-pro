---
type: Decision Rule
title: "On a library upgrade, budget for the changes that do not raise"
description: >
  Across four independent load-bearing projects in one week, upgrades changed defaults that alter
  numerics or generated text without any error: a GGUF attention backend selected automatically, a
  checkpoint activation function silently corrected, an Inductor RNG path switched off, and a
  legacy config remap deleted. The loud breakages are cheap because they fail at startup; the
  silent ones require a golden-output baseline to detect. Pin exact versions and re-baseline
  outputs on every upgrade, and check release containment before planning around any change.
tags: [dependencies, upgrades, numerics, reproducibility, migration, pinning]
tier: modern-consensus
applies_to:
  - upgrading transformers, pytorch, keras, vllm or a comparable load-bearing dependency
  - deciding whether an inference or training stack can float versions or must pin exactly
  - diagnosing changed model outputs after a dependency bump with no code change
  - planning a migration around a change you read about in a commit or changelog
status: draft
stale_after: 2027-03-28
generated:
  by: expedition/weekly-2026-09-28
  at: 2026-09-28T00:36:57Z
sources:
  - id: tfm-gguf-doc
    resource: https://raw.githubusercontent.com/huggingface/transformers/abd76d121e6230e4a1386332863dba4c27d416e0/docs/source/en/quantization/gguf.md
    title: "transformers GGUF docs — ggml-attn as default attention on MPS"
    author: Hugging Face (transformers contributors)
    last_modified: 2026-09-21
  - id: tfm-config-remap
    resource: https://raw.githubusercontent.com/huggingface/transformers/e2d83fdf9c25a0f6021e90a241263a4a59faa15f/src/transformers/configuration_utils.py
    title: "transformers configuration_utils.py — _LEGACY_LAYER_TYPE_REMAP"
    author: Hugging Face (transformers contributors)
    last_modified: 2026-09-22
  - id: pt-inductor-rand4x
    resource: https://raw.githubusercontent.com/pytorch/pytorch/983d11f91bd577039613d36d58da6c1c729a12e2/torch/_inductor/config.py
    title: "PyTorch torch/_inductor/config.py — use_rand4x disabled pending issue 198333"
    author: PyTorch contributors
    last_modified: 2026-09-26
  - id: keras-label-smoothing
    resource: https://raw.githubusercontent.com/keras-team/keras/a4f89709117d2db66b6a211b8ac6e05cd88640cb/keras/src/losses/losses.py
    title: "Keras losses.py — _validate_label_smoothing"
    author: Keras contributors
    last_modified: 2026-09-25
  - id: vllm-fp8-online
    resource: https://raw.githubusercontent.com/vllm-project/vllm/90a951500699b1aa499f350b3352450cdcc13340/vllm/model_executor/layers/quantization/fp8.py
    title: "vLLM fp8.py — online FP8 quantization removed from --quantization fp8"
    author: vLLM contributors
    last_modified: 2026-09-24
  - id: stable-tags-20260928
    resource: https://github.com/vllm-project/vllm/tags
    title: "Latest stable release tags, checked by git ls-remote on 2026-09-28"
    author: "expedition/weekly-2026-09-28 (direct measurement)"
    last_modified: 2026-09-28
---

# Rule

**Split every dependency upgrade into two budgets: the changes that fail loudly, and the changes that alter your outputs while everything still appears to work. The first budget is small and self-announcing. The second is the one that costs you a week, and you cannot detect it without a golden-output baseline captured before the upgrade.** One week across four independent projects supplies both kinds.

## The silent class — outputs move, nothing errors

**An attention backend can be selected for you.** As of 2026-09-21, loading a GGUF file in transformers on MPS with `kernels` installed selects `ggml-attn` as the default attention: "the same flash-attention kernel llama.cpp uses for decode and prefill. If the kernel cannot be fetched, the model keeps its attention implementation. Passing `attn_implementation` (for example `"sdpa"`) always takes precedence."[^tfm-gguf-doc] **Three consequences worth separating.** The numerics of your attention path now depend on whether an optional package is installed and whether a remote kernel fetch succeeded — so the same code on two machines can compute differently. The fallback is a warning, not an error, so a failed fetch is a silent performance and numerics difference rather than a stop. And passing `attn_implementation` explicitly is the only way to make the choice deterministic.

**A checkpoint's declared activation function can be corrected under you.** Transformers now remaps Gemma 1.0's shipped `hidden_act="gelu"` (exact erf GELU) to the tanh approximation the weights were actually trained with, and writes the corrected value on `save_pretrained`. **Generated text for Gemma 1.0 therefore differs from any earlier v5.x**, and a re-saved config differs on disk from the one you loaded. This is the right fix and still an output-changing one. *Evidence note: this item rests on a commit message reported by this expedition's repo sweep, which could not be re-fetched independently — `github.com` commit endpoints are not reachable from this session (see the log entry for 2026-09-28). It is recorded here as the weakest-sourced claim in this concept and should be re-verified before the concept is promoted.*

**An RNG codegen path can flip back.** PyTorch's Inductor gained `use_rand4x`, default off, with the comment "Use tl.rand4x/randn4x for 1D CUDA Triton random. Disabled pending https://github.com/pytorch/pytorch/issues/198333" and opt-in via `TORCHINDUCTOR_USE_RAND4X=1`.[^pt-inductor-rand4x] **If you captured dropout or sampling reference outputs against a nightly in the window where `rand4x` was live, your RNG streams have changed twice**, and neither change raised. Random-number streams are the canonical example of a difference that unit tests with loose tolerances will not catch but a seeded end-to-end test will.

**A legacy compatibility shim can be removed in the same commit that adds one.** `_LEGACY_LAYER_TYPE_REMAP` at 2026-09-22 maps `"mamba"`, `"attention"`, and — newly — `"deepseek_sparse_attention"` and `"qwen_sparse_attention"` to `"indexed_attention"`.[^tfm-config-remap] The `"conv" → "linear_attention"` entry that previously covered LFMv2-style configs is **absent** from the map at that commit.[^tfm-config-remap] So one family of configs gained normalization in the same change that another family lost it. **When a remap table is edited, check that your config's key is still in it** — a removed entry does not announce itself; the docstring states only that "any name that does not fit one of the `_LEGACY_LAYER_TYPE_REMAP` patterns is returned unchanged."[^tfm-config-remap]

## The loud class — cheap, because it stops

**Validation tightens.** Keras now rejects a static `label_smoothing` that is not a real number or lies outside `[0, 1]`, raising "`label_smoothing` must be a float or int" for a bool or non-real value; tensor values are deliberately skipped because they are "validated at runtime by the ops themselves."[^keras-label-smoothing] Code that passed `True` or `1.5` and silently trained on nonsense now fails fast. **This is a silent bug becoming a loud one — the good direction.**

**A CLI contract narrows.** vLLM's `--quantization fp8` on a checkpoint that is not FP8-serialized now raises: "The `fp8` quantization method no longer supports online quantization. Please use `--quantization fp8_per_tensor` instead."[^vllm-fp8-online] The default for `is_checkpoint_fp8_serialized` flipped from `False` to `True` in the same file.[^vllm-fp8-online] Any serve command doing on-the-fly FP8 will not start. That is a one-line migration precisely *because* it fails at startup.

## Release containment: read the tag, not the commit

Most of the above had not shipped when observed. Checked by `git ls-remote` on 2026-09-28, the newest stable tags were **vLLM v0.30.0**, **transformers v5.17.0**, and **Keras v3.15.1**.[^stable-tags-20260928] vLLM v0.30.0 was cut 2026-09-21, so the FP8 change (2026-09-24) postdates it; the transformers items (2026-09-21/22) postdate v5.17.0 (2026-09-09); the Keras item postdates v3.15.1. **The rule: a commit, a changelog line, or a blog post is not an available feature.** Before planning a migration, establish which tag contains the change — `git tag --contains <sha>` answers it directly — and distinguish a release candidate from a stable tag. Planning around something reachable only on `main` means either pinning to a commit or waiting.

**A corollary about declared metadata.** Platform-support signals can live in the build matrix before they reach the package metadata, so the artifact you can actually install is ground truth. This expedition's sweep reports PyTorch ceasing to build and upload cp310 nightly wheels ahead of 2.15 raising its minimum Python to 3.11, while `pyproject.toml` on `main` still declared `requires-python = ">=3.10"`. *That pair rests on a commit body and a file state this concept could not re-fetch independently, so it is recorded as a direction to check rather than an established fact.* The transferable discipline stands on its own: **check whether a wheel exists for your platform, rather than trusting a declared version floor.**

**What to do**

1. **Pin exact versions** for anything whose outputs you compare over time. Floating a minor version is a decision to accept undetected output drift.
2. **Keep a golden-output test** — a handful of fixed prompts or batches with fixed seeds, outputs stored — and run it across every upgrade. This is the only cheap detector for the silent class.
3. **Re-baseline, don't just re-run.** After an upgrade that touches attention, activations, RNG or quantization, treat prior metrics as belonging to the old stack.
4. **Make implicit choices explicit.** Pass `attn_implementation`, dtypes, and quantization modes rather than inheriting a default that can move or depend on whether an optional package resolved.
5. **Check containment before planning.** Establish the tag, and whether it is stable or an rc, before scheduling work around a change.

This extends [the universal workflow](../foundations/universal-workflow.md)'s discipline of holding the evaluation fixed while varying one thing: a dependency upgrade varies many things at once, several of them invisibly. It is the mirror image of [eval-harness version provenance](eval-harness-version-provenance.md) — there the instrument's version moves, here the system under test moves — and both defeat a stored number that carries no version.

# Open questions

- **No magnitude is established for any silent change here.** None of these sources quantifies how far outputs move — whether the GGUF attention switch, the Gemma activation correction, or the RNG flip changes a downstream metric measurably or only in the last decimal place. The direction is documented; the size is not.
- Two items in this concept (the Gemma activation remap, and the PyTorch cp310 wheel-matrix change) rest on commit messages this session could not re-fetch, because `github.com` commit and API endpoints are refused here while `raw.githubusercontent.com` is served. They are flagged inline and are the first thing to re-verify before promotion.
- Whether `ggml-attn` remains MPS-only, and what the numeric difference against `sdpa` actually is on the same checkpoint, is not addressed by the cited doc.
- The concept generalizes from four projects in one week. That is enough to establish that the silent class exists across independent ecosystems, but not enough to estimate a rate, and a week with four such changes may not be typical.
- `use_rand4x` is disabled "pending" an open issue,[^pt-inductor-rand4x] so this particular default is explicitly temporary and will move again — an argument for the golden-output test rather than for memorizing the current default.

[^tfm-gguf-doc]: transformers `docs/source/en/quantization/gguf.md` read at commit `abd76d1` (source id: tfm-gguf-doc). The default-attention sentence, the fetch-failure fallback, and the precedence of an explicit `attn_implementation` are stated there verbatim.
[^tfm-config-remap]: transformers `src/transformers/configuration_utils.py` read at commit `e2d83fd` (source id: tfm-config-remap). `_LEGACY_LAYER_TYPE_REMAP` at that commit contains `mamba`, `attention`, `deepseek_sparse_attention` and `qwen_sparse_attention`, and does not contain `conv`; the unchanged-passthrough behaviour is stated in the `remap_legacy_layer_types` docstring.
[^pt-inductor-rand4x]: PyTorch `torch/_inductor/config.py` read at commit `983d11f` (source id: pt-inductor-rand4x). The quoted comment and the `os.environ.get("TORCHINDUCTOR_USE_RAND4X") == "1"` default appear there.
[^keras-label-smoothing]: Keras `keras/src/losses/losses.py` read at commit `a4f8970` (source id: keras-label-smoothing). `_validate_label_smoothing` raises on bool or non-`numbers.Real` input and documents that tensor values are skipped; it is called from the crossentropy loss paths.
[^vllm-fp8-online]: vLLM `vllm/model_executor/layers/quantization/fp8.py` read at commit `90a9515` (source id: vllm-fp8-online). The raise text and the `is_checkpoint_fp8_serialized: bool = True` default both appear there.
[^stable-tags-20260928]: Direct measurement by this expedition (source id: stable-tags-20260928): `git ls-remote --tags --refs` against each repository on 2026-09-28 gave newest stable semver tags v0.30.0 (vLLM), v5.17.0 (transformers), v3.15.1 (Keras). Release-candidate tags were excluded by the version filter used, so this establishes the newest *stable* tag only.
