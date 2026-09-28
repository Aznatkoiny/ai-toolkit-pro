---
type: Decision Rule
title: "On a library upgrade, budget for the changes that do not raise"
description: >
  Across four independent load-bearing projects in one week, defaults and compatibility shims moved
  in ways that change numerics or model loading: a GGUF attention backend now selected
  automatically, a legacy config remap entry deleted while two were added, an Inductor RNG path
  switched off after shipping only in nightlies, and an FP8 serving default inverted. Some announce
  themselves and some do not. Pin exact versions, keep a golden-output baseline, and establish which
  release tag contains a change before planning around it.
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
    title: "transformers configuration_utils.py at commit e2d83fd — _LEGACY_LAYER_TYPE_REMAP after the indexer remap"
    author: Hugging Face (transformers contributors)
    last_modified: 2026-09-22
  - id: tfm-config-remap-v5170
    resource: https://raw.githubusercontent.com/huggingface/transformers/v5.17.0/src/transformers/configuration_utils.py
    title: "transformers configuration_utils.py at tag v5.17.0 — the same table before the change"
    author: Hugging Face (transformers contributors)
    last_modified: 2026-09-09
  - id: tfm-gemma-config
    resource: https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/models/gemma/configuration_gemma.py
    title: "transformers configuration_gemma.py — hidden_act legacy-value conversion"
    author: Hugging Face (transformers contributors)
    last_modified: 2026-09-25
  - id: pt-inductor-rand4x
    resource: https://raw.githubusercontent.com/pytorch/pytorch/983d11f91bd577039613d36d58da6c1c729a12e2/torch/_inductor/config.py
    title: "PyTorch torch/_inductor/config.py — use_rand4x disabled pending issue 198333"
    author: PyTorch contributors
    last_modified: 2026-09-26
  - id: pt-inductor-v2140
    resource: https://raw.githubusercontent.com/pytorch/pytorch/v2.14.0/torch/_inductor/config.py
    title: "PyTorch torch/_inductor/config.py at tag v2.14.0 — no rand4x option present"
    author: PyTorch contributors
    last_modified: 2026-08-26
  - id: keras-label-smoothing
    resource: https://raw.githubusercontent.com/keras-team/keras/a4f89709117d2db66b6a211b8ac6e05cd88640cb/keras/src/losses/losses.py
    title: "Keras losses.py — _validate_label_smoothing and its two call sites"
    author: Keras contributors
    last_modified: 2026-09-25
  - id: vllm-fp8-online
    resource: https://raw.githubusercontent.com/vllm-project/vllm/90a951500699b1aa499f350b3352450cdcc13340/vllm/model_executor/layers/quantization/fp8.py
    title: "vLLM fp8.py — online FP8 quantization removed from --quantization fp8"
    author: vLLM contributors
    last_modified: 2026-09-24
  - id: vllm-fp8-v0290
    resource: https://raw.githubusercontent.com/vllm-project/vllm/v0.29.0/vllm/model_executor/layers/quantization/fp8.py
    title: "vLLM fp8.py at tag v0.29.0 — the same default before the change"
    author: vLLM contributors
    last_modified: 2026-09-16
  - id: stable-tags-20260928
    resource: https://github.com/vllm-project/vllm/tags
    title: "Newest stable release tags for vllm, transformers and keras, measured by git ls-remote on 2026-09-28"
    author: "expedition/weekly-2026-09-28 (direct measurement)"
    last_modified: 2026-09-28
---

# Rule

**Split every dependency upgrade into two budgets: the changes that fail loudly, and the changes that alter your outputs while everything still appears to work. The first budget is small and self-announcing. The second is the one that costs you a week, and you cannot detect it without a golden-output baseline captured before the upgrade.** One week across four independent projects supplies both kinds — and, usefully, one case that sits between them.

## The silent class — outputs move, nothing errors

**An attention backend can be selected for you.** As of 2026-09-21, loading a GGUF file in transformers on MPS with `kernels` installed selects `ggml-attn` as the default attention: "the same flash-attention kernel llama.cpp uses for decode and prefill. If the kernel cannot be fetched, the model keeps its attention implementation. Passing `attn_implementation` (for example `"sdpa"`) always takes precedence."[^tfm-gguf-doc] **Three consequences worth separating.** Your attention numerics now depend on whether an optional package is installed and whether a remote kernel fetch succeeded, so identical code on two machines can compute differently. The documented fallback is silent in the doc's own account — it states only that the model "keeps its attention implementation," with no error and no warning mentioned. And passing `attn_implementation` explicitly is the only way to make the choice deterministic. Scope note: the doc restricts this packed path to particular model families, with others going through the legacy loader, so read the doc's own compatibility list before assuming it applies.[^tfm-gguf-doc]

**A compatibility shim can be deleted in the same change that adds one.** At tag v5.17.0, `_LEGACY_LAYER_TYPE_REMAP` contained exactly three entries: `"conv": "linear_attention"` — annotated in-source as "only in LFMv2" — plus `"mamba": "linear_attention"` and `"attention": "full_attention"`.[^tfm-config-remap-v5170] At commit `e2d83fd` the `"conv"` entry is **gone**, and two new entries `"deepseek_sparse_attention"` and `"qwen_sparse_attention"` both map to `"indexed_attention"`.[^tfm-config-remap] (`"mamba"` and `"attention"` keep their own distinct targets; only the two new keys map to `indexed_attention`.) **So one family of configs gained normalization in the same edit that another family lost it**, and the only stated behaviour for an unmatched key is pass-through: "any name that does not fit one of the `_LEGACY_LAYER_TYPE_REMAP` patterns is returned unchanged."[^tfm-config-remap] An LFMv2-style config carrying `layer_types=["conv", ...]` is therefore no longer normalized, and nothing announces it. **When a remap table is edited, check that your key is still in it.**

**An RNG codegen path can be switched off after reaching only nightly users.** PyTorch's Inductor carries `use_rand4x`, default off, with the comment "Use tl.rand4x/randn4x for 1D CUDA Triton random. Disabled pending https://github.com/pytorch/pytorch/issues/198333" and opt-in via `TORCHINDUCTOR_USE_RAND4X=1`.[^pt-inductor-rand4x] **The containment detail is what makes this actionable: the option does not exist at all in `torch/_inductor/config.py` at tag v2.14.0**,[^pt-inductor-v2140] so `rand4x` was live only on `main`/nightlies and never in a stable release. **If you captured dropout or sampling reference outputs against a nightly in that window, your RNG streams changed and then changed back; if you only ever used stable releases, this one never touched you.** Random-number streams are the canonical difference that loose-tolerance unit tests miss and a seeded end-to-end test catches.

## The announced-but-easy-to-miss case

**A checkpoint's declared activation function is corrected under you — with a warning.** Gemma configs shipping `hidden_act="gelu"` are rewritten to `gelu_pytorch_tanh` in `__post_init__`, emitting `logger.warning_once`: "We found `hidden_act=\"gelu\"` in this Gemma config. This is a legacy value of the official releases but it is meant to target the tanh approximation."[^tfm-gemma-config] **Two corrections to the obvious reading.** This is *not* silent — it logs, so it belongs in neither the silent nor the fail-fast class but in the easily-swallowed middle, since a `warning_once` in a busy training log is functionally invisible. And it is a **restoration, not a new divergence**: the in-source comment records that "#35235 dropped this conversion (which is needed per #29402) which we now handle here instead."[^tfm-gemma-config] **So behaviour is being returned toward a pre-#35235 state rather than departing from every earlier version** — which means the direction of any output change depends on which version you are coming from, and cannot be stated as a blanket "differs from all earlier v5.x." Establish your own before-state rather than assuming.

## The loud class — cheap, because it stops

**Validation tightens, but check its coverage.** Keras added `_validate_label_smoothing`, which raises "`label_smoothing` must be a float or int" for a bool or non-real value and rejects values outside `[0, 1]`, deliberately skipping tensors because they are "validated at runtime by the ops themselves."[^keras-label-smoothing] **The important qualification is that it has exactly two call sites — `categorical_crossentropy` and `binary_crossentropy`.** Three other losses in the same file that accept `label_smoothing` (`categorical_focal_crossentropy`, `sparse_categorical_crossentropy`, `binary_focal_crossentropy`) do not call it, so `True` or `1.5` still passes silently there.[^keras-label-smoothing] **A tightened validation is not a guarantee across an API surface — check whether your call path is one of the covered ones.** Note also that the raise fires when the loss is called, not at import or model construction.

**A CLI contract narrows.** vLLM's `--quantization fp8` on a checkpoint that is not FP8-serialized now raises: "The `fp8` quantization method no longer supports online quantization. Please use `--quantization fp8_per_tensor` instead."[^vllm-fp8-online] The `is_checkpoint_fp8_serialized` parameter default is `True` at that commit,[^vllm-fp8-online] where at tag v0.29.0 it was `False`[^vllm-fp8-v0290] — an inverted default confirmed by comparing the two published files. Any serve command doing on-the-fly FP8 will not start. **That is a one-line migration precisely because it fails at startup.**

## Release containment: read the tag, not the commit

Most of the above had not shipped when observed. Checked by `git ls-remote` on 2026-09-28, the newest stable tags were **vLLM v0.30.0**, **transformers v5.17.0**, and **Keras v3.15.1**.[^stable-tags-20260928] vLLM v0.30.0 was cut 2026-09-21, so the FP8 change (2026-09-24) postdates it; the transformers items (2026-09-21/22) postdate v5.17.0 (2026-09-09); the Keras item postdates v3.15.1. **The rule: a commit, a changelog line, or a blog post is not an available feature.** Before planning a migration, establish which tag contains the change — `git tag --contains <sha>` answers it directly — and distinguish a release candidate from a stable tag. Planning around something reachable only on `main` means pinning to a commit or waiting.

**The corollary, and `rand4x` is the clean example: the shipped artifact is ground truth, not the source tree.** A configuration option present on `main` may never have existed in any release you could install,[^pt-inductor-v2140] which decides whether a hazard was ever yours. The same logic runs the other way for platform support — check that an installable artifact exists for your platform rather than trusting a declared version floor.

**What to do**

1. **Pin exact versions** for anything whose outputs you compare over time. Floating a minor version is a decision to accept undetected output drift.
2. **Keep a golden-output test** — fixed prompts or batches, fixed seeds, outputs stored — and run it across every upgrade. This is the only cheap detector for the silent class.
3. **Re-baseline, don't just re-run.** After an upgrade touching attention, activations, RNG or quantization, treat prior metrics as belonging to the old stack.
4. **Make implicit choices explicit.** Pass `attn_implementation`, dtypes and quantization modes rather than inheriting a default that can move or depend on an optional package resolving.
5. **Treat `warning_once` as invisible.** If a correctness-relevant change only warns, it will be missed in a real log; assert on it or pin around it.
6. **Check containment and coverage before planning.** Which tag has the change, and does a tightened check actually cover your call path.

This extends [the universal workflow](../foundations/universal-workflow.md)'s discipline of holding the evaluation fixed while varying one thing: an upgrade varies many things at once, several invisibly. It is the mirror image of [eval-harness version provenance](eval-harness-version-provenance.md) — there the instrument's version moves, here the system under test moves — and both defeat a stored number carrying no version.

# Open questions

- **No magnitude is established for any silent change here.** None of these sources quantifies how far outputs move — whether the GGUF attention switch, the Gemma activation conversion, or the RNG option changes a downstream metric measurably or only in the last decimal place. Directions are documented; sizes are not.
- The GGUF item's *before*-state is not established by the cited doc, which shows only the current documented default. The change is corroborated by the commit subject "Better attn default for gguf (#48935)" dated 2026-09-21, read via `git fetch` of that SHA; treat the doc as evidence of the current default and the commit as evidence that it is new.
- Whether `ggml-attn` remains MPS-only, and what the numeric difference against `sdpa` is on the same checkpoint, is not addressed by the cited doc.
- For Gemma, which released versions did and did not perform the conversion is not established here — only that #35235 dropped it and the current code restores it. The blast radius needs a version-by-version check.
- This concept generalizes from four projects in one week. That establishes the silent class exists across independent ecosystems; it does not estimate a rate, and a week with four such changes may not be typical.
- `use_rand4x` is disabled "pending" an open issue,[^pt-inductor-rand4x] so that default is explicitly temporary and will move again — an argument for the golden-output test rather than for memorizing current defaults. This session could not confirm the referenced issue's state, `github.com` issue pages being unreachable here.
- An earlier revision of this concept asserted that PyTorch had ceased building cp310 nightly wheels ahead of a 3.11 minimum. That rested on a commit body and a wheel matrix this session cannot verify (`download.pytorch.org` is egress-blocked), so the claim has been withdrawn rather than carried unverified.

[^tfm-gguf-doc]: transformers `docs/source/en/quantization/gguf.md` read at commit `abd76d1` (source id: tfm-gguf-doc). The default-attention sentence, the fetch-failure fallback wording, the precedence of an explicit `attn_implementation`, and the model-family scoping are stated there. The doc does not describe the fallback as emitting a warning.
[^tfm-config-remap]: transformers `src/transformers/configuration_utils.py` read at commit `e2d83fd` (source id: tfm-config-remap). At that commit the table holds `mamba → linear_attention`, `attention → full_attention`, `deepseek_sparse_attention → indexed_attention` and `qwen_sparse_attention → indexed_attention`, and contains no `conv` key; the pass-through behaviour is stated in the `remap_legacy_layer_types` docstring.
[^tfm-config-remap-v5170]: transformers `src/transformers/configuration_utils.py` at tag `v5.17.0` (source id: tfm-config-remap-v5170). The table there holds exactly `conv → linear_attention` (commented "only in LFMv2"), `mamba → linear_attention` and `attention → full_attention`. Comparing this file against the one above is what establishes both the addition and the removal, without relying on a commit diff.
[^tfm-gemma-config]: transformers `src/transformers/models/gemma/configuration_gemma.py` (source id: tfm-gemma-config), read 2026-09-28 at branch `main`. The `logger.warning_once` text, the reassignment to `gelu_pytorch_tanh`, and the comment recording that #35235 dropped the conversion are all in `__post_init__`. Fetched at a branch ref, so this reflects the state on 2026-09-28.
[^pt-inductor-rand4x]: PyTorch `torch/_inductor/config.py` read at commit `983d11f` (source id: pt-inductor-rand4x). The quoted comment and the `os.environ.get("TORCHINDUCTOR_USE_RAND4X") == "1"` default appear there. The commit's subject, "[inductor] Turn off random 4x by default (#198680)" dated 2026-09-26, was read via `git fetch --depth 1` of that SHA and establishes that the option was previously on.
[^pt-inductor-v2140]: PyTorch `torch/_inductor/config.py` at tag `v2.14.0` (source id: pt-inductor-v2140). The string `rand4x` does not occur in that file, establishing that the option was never present in that stable release.
[^keras-label-smoothing]: Keras `keras/src/losses/losses.py` read at commit `a4f8970` (source id: keras-label-smoothing). `_validate_label_smoothing` is defined at line 18 and called at exactly two sites, within `categorical_crossentropy` and `binary_crossentropy`; `categorical_focal_crossentropy`, `sparse_categorical_crossentropy` and `binary_focal_crossentropy` also accept `label_smoothing` and do not call it.
[^vllm-fp8-online]: vLLM `vllm/model_executor/layers/quantization/fp8.py` read at commit `90a9515` (source id: vllm-fp8-online). The raise text and the `is_checkpoint_fp8_serialized: bool = True` default both appear there.
[^vllm-fp8-v0290]: vLLM `vllm/model_executor/layers/quantization/fp8.py` at tag `v0.29.0` (source id: vllm-fp8-v0290). The same parameter defaults to `False` there, which establishes the inversion by file comparison rather than by commit diff.
[^stable-tags-20260928]: Direct measurement by this expedition: `git ls-remote --tags --refs` against each of vllm-project/vllm, huggingface/transformers and keras-team/keras on 2026-09-28, filtered to plain `vX.Y.Z` tags, gave newest stable tags v0.30.0, v5.17.0 and v3.15.1 respectively. Release-candidate tags were excluded by that filter, so this establishes the newest *stable* tag only. The `resource` URL for this source is the vLLM tag listing as a representative human-readable entry point; the measurement covered all three repositories by the command above.
