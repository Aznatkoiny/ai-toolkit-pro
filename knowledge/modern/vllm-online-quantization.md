---
type: Decision Rule
title: "Online (load-time) quantization in vLLM: when you can skip the pre-quantized checkpoint"
description: >
  vLLM can quantize a BF16/FP16 checkpoint's Linear and MoE weights at load time — no
  pre-quantized checkpoint and no calibration data — via a small set of named schemes
  whose usability is gated by GPU architecture. As of 2026-08-10 the MXFP4 scheme is on
  main only and reaches no released version.
tags: [inference, serving, quantization, vllm, fp8, mxfp4, deployment]
tier: frontier
applies_to:
  - deploying an LLM on vLLM when only a BF16/FP16 checkpoint exists
  - choosing a quantization scheme for a vLLM serving deployment
  - deciding whether calibration data or a pre-quantized checkpoint is needed
status: draft
stale_after: 2027-02-10
generated:
  by: expedition/weekly-2026-08-10
  at: 2026-08-10T00:00:00Z
sources:
  - id: online-doc
    resource: https://github.com/vllm-project/vllm/blob/main/docs/features/quantization/online.md
    title: "vLLM docs: Online Quantization"
    author: vLLM maintainers
    last_modified: 2026-08-07
  - id: mxfp4-commit
    resource: https://github.com/vllm-project/vllm/commit/3518110f2f4532c4605d8b1ea2a9bdc7d61b9f04
    title: "[Online quantization] Add online MXFP4 quantization support (#49347)"
    author: vLLM contributors
    last_modified: 2026-08-07
  - id: vllm-repo
    resource: https://github.com/vllm-project/vllm
    title: "vllm-project/vllm git repository (release tags v0.26.0, v0.27.0rc1, v0.27.0rc2)"
    author: vLLM maintainers
    last_modified: 2026-08-10
  - id: vllm-pypi
    resource: https://pypi.org/pypi/vllm/json
    title: "vllm on PyPI (latest released version)"
    author: vLLM maintainers
    last_modified: 2026-08-10
---

# Rule

**If you only have a BF16/FP16 checkpoint and no calibration data, you do not need to produce a quantized checkpoint before serving on vLLM — pass a scheme name to `quantization` and let vLLM convert weights during model loading.** Online quantization "lets you take a BF16/FP16 model and quantize its Linear and MoE weights to lower precision (such as FP8) at load time, without needing a pre-quantized checkpoint or calibration data"; weights are converted during loading and activations are dynamically scaled each forward pass.[^online-doc] The same names work from Python (`LLM("meta-llama/Llama-3.1-8B", quantization="fp8_per_tensor")`) and the CLI (`vllm serve … --quantization fp8_per_tensor`).[^online-doc]

**Pick the scheme by GPU architecture first, granularity second.** The documented schemes are `fp8_per_tensor`, `fp8_per_block`, `mxfp8`, and `mxfp4`.[^online-doc] The hardware gate is the part that silently changes what you get:

- `mxfp8` (fp8_e4m3 data, e8m0 per-1x32-block scales for both weights and activations) **requires SM 100+ (Blackwell or newer) for w8a8; other GPUs fall back to w8a16**.[^online-doc] Ask for MXFP8 on pre-Blackwell hardware and you keep 16-bit activations rather than getting an error.
- `fp8_per_tensor` uses fp32 per-tensor scales, but "on some GPUs (Ada, Hopper) linear activations use per-token scaling for better performance" — the effective activation recipe is platform-dependent, not what the scheme name implies.[^online-doc]
- `fp8_per_block` is the explicit-granularity option: fp32 per-128x128-block weight scales and per-1x128-block activation scales.[^online-doc]
- `mxfp4` gives fp4_e2m1 weights with e8m0 per-1x32-block scales, but its **linear backend is auto-selected per platform and does not enforce an activation dtype — some backends use BF16 activations**. Pin one with `--linear-backend` (e.g. `--linear-backend flashinfer`) if you need a known activation format.[^online-doc]

**Do not assume the scheme applies uniformly.** `quantization_config` takes separate `linear` and `moe` specs (each a `{weight, activation}` dict or a bare shorthand string) plus an `ignore` list accepting exact layer names and `re:`-prefixed regexes; unset fields fall back to the `--quantization` shorthand's defaults.[^online-doc] Two traps are documented: for fused layers such as `qkv_proj`, **the ignore pattern must match the unfused shard names** (`q_proj`, `k_proj`, `v_proj`), not the fused name;[^online-doc] and on XPU, non-block FP8 scaled-mm linear layers **default to W8A16** unless `--linear-backend xpu` forces W8A8.[^online-doc]

**Online quantization also reaches already-quantized checkpoints, narrowly.** For checkpoint-quantized models, `quantization_config` can select an activation format independently of the baked-in weights, but the overrides are checkpoint-specific — as documented, this is wired up today only for MXFP4 MoE checkpoints (gpt-oss), where you can opt into FP8 activations via `--quantization-config.moe.activation mxfp8`.[^online-doc]

**Version gate — check before you plan around this.** The MXFP4 online scheme landed on `main` on 2026-08-07.[^mxfp4-commit] As of 2026-08-10 it is **not in any release**: the docs at tags `v0.26.0`, `v0.27.0rc1`, and `v0.27.0rc2` contain no `mxfp4` online-quantization text, and the latest version on PyPI is 0.26.0.[^vllm-repo][^vllm-pypi] A builder on a pip-installed vLLM today gets the FP8 schemes, not MXFP4; treat MXFP4 as "coming in a release after v0.27.0rc2" and verify against your installed version before designing around it.

**Scope note:** LLM/foundation-model serving and quantization are not covered by any `status: stable` concept; the catalog's [scope boundary](../foundations/scope-boundary.md) lists LLM fine-tuning as uncovered and says nothing about inference-time quantization. This draft opens inference/deployment as a draft-covered area and does not conflict with any stable concept.

# Open questions

- No accuracy or throughput measurements were gathered. The vLLM documentation describes the *mechanics* of each scheme and says nothing about the accuracy cost of online versus calibrated quantization, so the choice between online quantization and a properly calibrated checkpoint remains unevidenced here.
- Which release ships online MXFP4 is not yet determinable — it is absent from v0.27.0rc2 (2026-08-09), and no later tag existed at the time of this sweep.
- The vLLM blog post "Efficient Decode Context Parallelism with vLLM for Long Context Workloads" (2026-08-07) was surfaced by the sweep but could not be retrieved from this environment, so no claim here rests on it.

[^online-doc]: vLLM docs, `docs/features/quantization/online.md` on `main` (source: online-doc), read 2026-08-10. Supplies the definition of online quantization, the Quick Start Python/CLI forms, the four-row Supported Schemes table (weight recipe, activation recipe, and the SM 100+/w8a16 and Ada-Hopper per-token notes), the `quantization_config` schema, the XPU W8A16 default, the fused-layer ignore-pattern note, and the gpt-oss MXFP4 MoE activation override. File last modified 2026-08-07 per the repository's git history.
[^mxfp4-commit]: vLLM commit 3518110f (source: mxfp4-commit), "[Online quantization] Add online MXFP4 quantization support (#49347)", committer date 2026-08-07, the change that added the `mxfp4` row to the doc above.
[^vllm-repo]: vllm-project/vllm git repository (source: vllm-repo). Checked 2026-08-10 by resolving tags `v0.26.0` (2026-07-26), `v0.27.0rc1` (2026-08-06), and `v0.27.0rc2` (2026-08-09) and inspecting `docs/features/quantization/online.md` at each: none contains the string `mxfp4`.
[^vllm-pypi]: vllm PyPI JSON metadata (source: vllm-pypi), read 2026-08-10: `info.version` is 0.26.0.
