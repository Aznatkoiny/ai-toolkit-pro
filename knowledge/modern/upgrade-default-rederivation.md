---
type: Decision Rule
title: "An engine upgrade re-derives your defaults from hardware and version"
description: >
  Serving and training runtimes compute their operating defaults at startup from the device they
  find and the version they are, not from your config file. Five independent projects moved such a
  default inside two weeks — three in a tagged release, four on trunk only. The loud failures (a
  removed flag) are the safe ones; the dangerous change keeps your command line working and moves
  the operating point, so pin every value you benchmarked and re-baseline after upgrading.
tags: [inference, serving, deployment, upgrades, vllm, sglang, tensorrt-llm, llama-cpp, pytorch]
tier: frontier
applies_to:
  - upgrading an inference engine (vLLM, SGLang, TensorRT-LLM, llama.cpp) in a deployment
  - upgrading PyTorch on a distributed training or CPU-bound inference job
  - reproducing a latency/throughput benchmark across two versions of the same engine
  - writing the change-management checklist for a serving rollout
status: draft
stale_after: 2027-03-07
generated:
  by: expedition/weekly-2026-09-07
  at: 2026-09-07T00:00:00Z
sources:
  - id: vllm-028-args
    resource: https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/engine/arg_utils.py
    title: "vllm-project/vllm v0.28.0 — vllm/engine/arg_utils.py (batch-size tier defaults)"
    author: vLLM contributors
    last_modified: 2026-08-24
  - id: vllm-027
    resource: https://github.com/vllm-project/vllm/blob/v0.27.0/vllm/engine/arg_utils.py
    title: "vllm-project/vllm v0.27.0 — arg_utils.py, config/cache.py, config/model.py (the prior tier and the removed knobs)"
    author: vLLM contributors
    last_modified: 2026-08-10
  - id: sglang-radix-default
    resource: https://github.com/sgl-project/sglang/blob/v0.5.19/python/sglang/srt/mem_cache/registry.py
    title: "sgl-project/sglang v0.5.19 — mem_cache/registry.py and srt/environ.py (unified radix tree becomes the fall-through)"
    author: SGLang contributors
    last_modified: 2026-09-03
  - id: trtllm-kvm-v2
    resource: https://github.com/NVIDIA/TensorRT-LLM/blob/v1.3.0rc25/tensorrt_llm/_torch/models/modeling_deepseekv3.py
    title: "NVIDIA/TensorRT-LLM v1.3.0rc25 — get_preferred_kv_cache_manager_version returning V2"
    author: NVIDIA TensorRT-LLM contributors
    last_modified: 2026-08-27
  - id: llamacpp-preserve-reasoning
    resource: https://github.com/ggml-org/llama.cpp/commit/e750b887a82719c27200b71545f63ed78ec24719
    title: "ggml-org/llama.cpp commit e750b88 — common, server : enable preserve_reasoning kwarg by default, log its effective state (#28174)"
    author: Georgi Gerganov
    last_modified: 2026-09-02
  - id: pytorch-nccl2-default
    resource: https://github.com/pytorch/pytorch/commit/e632bee7b8c7e590b70bf70283dde89dc451c855
    title: "pytorch/pytorch commit e632bee — [c10d] Make nccl2 the default NCCL backend (#192281)"
    author: Tristan Rice
    last_modified: 2026-09-01
  - id: pytorch-cpuset-threads
    resource: https://github.com/pytorch/pytorch/commit/7059aa341923e8d50a67679f971e0e12efca374d
    title: "pytorch/pytorch commit 7059aa3 — Clamp default num_threads to cpuset/affinity mask (#194605)"
    author: Nikita Shulga
    last_modified: 2026-08-24
  - id: pytorch-nested-reduction
    resource: https://github.com/pytorch/pytorch/commit/abaacefd1437dd1e192a2b10a110654c69443e08
    title: "pytorch/pytorch commit abaacef — Enable nested reductions by default in OSS (#191974)"
    author: Elias Ellison
    last_modified: 2026-09-03
---

# Rule

**Your config file does not hold your operating point; the engine derives it at startup from the
device it finds and the version it is. Upgrading re-runs that derivation.** Between 2026-08-24 and
2026-09-04, five independent projects — vLLM, SGLang, NVIDIA TensorRT-LLM, llama.cpp and PyTorch —
each moved a value that a user who sets nothing receives by default. None requires a config change
to take effect. That is the point: **the command line that worked yesterday is the one that lands
somewhere else today.**

## The two failure shapes, and which one to fear

**Loud (safe): a removal.** vLLM v0.28.0 deletes the in-tree bitsandbytes loader and quantization
method — `vllm/model_executor/model_loader/bitsandbytes_loader.py` and
`vllm/model_executor/layers/quantization/bitsandbytes.py` both resolve at tag `v0.27.0` and are
absent at `v0.28.0` — and drops the `calculate_kv_scales` and `override_attention_dtype` engine
knobs, which exist as config fields at v0.27.0 (`config/cache.py` and `config/model.py`
respectively) and have no definition sites at v0.28.0.[^vllm-027][^vllm-028-args] A launch command
carrying `--calculate-kv-scales` now fails at argument parsing. **This is the good case:** it stops
the rollout instead of quietly changing it, and it was signposted — v0.27.0 already carried a
deprecation validator on that field.[^vllm-027]

**Silent (dangerous): a re-derivation.** The same release adds a GPU memory tier above the existing
one: on devices with at least 160 GiB, the OpenAI-API-server default `max_num_batched_tokens`
becomes 16384, under the comment "for GPUs like B200/B300 with >= 160GB memory, use the largest
defaults". The previous top tier — `device_memory >= 70 * GiB_bytes and "a100" not in device_name` —
gave that context 8192.[^vllm-028-args][^vllm-027] **On a B200 API server that is a silent doubling
of the prefill token budget per step**, with a different latency/throughput point and higher
activation memory, from an upgrade alone.

The other four are the same shape:

- **SGLang v0.5.19** makes the unified radix tree the default tree cache. The env-var opt-in is
  marked deprecated — "The unified radix tree is the default tree cache now; unset this env" — and,
  more tellingly, the cache-selection fall-through in `mem_cache/registry.py` changed from
  `return RadixCache(params)` at v0.5.18 to `return _create_unified_radix_cache(...)` at v0.5.19,
  with the env var gone from the selection chain.[^sglang-radix-default] Deployments that never
  opted in are now on a different prefix-cache implementation.
- **TensorRT-LLM v1.3.0rc25** has model classes declare
  `get_preferred_kv_cache_manager_version()` returning `"V2"` — "Prefer KV cache manager V2 for this
  model implementation" — which the engine adopts while the user's
  `kv_cache_config.use_kv_cache_manager_v2` stays at its unchanged default `"auto"`. Thirteen model
  files declare the preference at rc25 and none at rc24.[^trtllm-kvm-v2] **The config value you can
  read did not change; the implementation it selects did.**
- **PyTorch** makes `nccl` resolve to the nccl2 ProcessGroup, inverting the registration "so an
  unset variable or `TORCH_DIST_USE_NCCL2=1` selects nccl2, while `TORCH_DIST_USE_NCCL2=0` and the
  explicit `nccl-legacy` name remain rollback paths";[^pytorch-nccl2-default] clamps the default
  thread count to the process's CPU affinity mask instead of the host topology reported by
  cpuinfo;[^pytorch-cpuset-threads] and turns on Inductor's nested reductions in OSS, keeping
  `TORCHINDUCTOR_NESTED_REDUCTION` "as the force override".[^pytorch-nested-reduction]

**Announced, but still a default change: llama.cpp.** The `preserve_reasoning` chat-template kwarg
is now enabled when neither `--reasoning-preserve` nor `--no-reasoning-preserve` is given — but the
same commit makes the server "log its effective state" and warn when the default applied, and the
flag's help text says "(default: enabled)".[^llamacpp-preserve-reasoning] **This is the well-behaved
version of the pattern:** the operating point still moved without a config change, and for a
reasoning model whose template advertises the `supports_preserve_reasoning` capability it changes
the templated prompt itself — and with it token counts and prefix-cache keys — but the change
announces itself in the log rather than only in your metrics.

## What to do

1. **Pin what you benchmarked.** Every case above respects an explicit setting: TensorRT-LLM adopts
   the model preference only while the field is left at `"auto"`,[^trtllm-kvm-v2] llama.cpp defers
   to the explicit flags,[^llamacpp-preserve-reasoning] PyTorch keeps named rollback
   paths,[^pytorch-nccl2-default][^pytorch-nested-reduction] and vLLM's derived batch defaults apply
   only when the user set none.[^vllm-028-args] A tuned value that is written down is a value the
   upgrade cannot move.
2. **Diff the effective configuration the engine reports, not the configuration you wrote.** The
   whole class is invisible in a diff of your own files.
3. **Re-baseline latency and cache-hit metrics after the upgrade, before attributing any change to
   your own code.** A different prefix-cache implementation, KV-cache manager, prompt template, or
   collective backend moves the numbers you compare against.
4. **Know each rollback lever before you roll forward**: `--max-num-batched-tokens` and
   `--max-num-seqs` set explicitly (vLLM), `use_kv_cache_manager_v2=False` (TensorRT-LLM),
   `--no-reasoning-preserve` (llama.cpp), `TORCH_DIST_USE_NCCL2=0` or `backend="nccl-legacy"` and
   `TORCHINDUCTOR_NESTED_REDUCTION=0` (PyTorch).
5. **Check whether the change is in a release or only on trunk.** Three of these shipped in a tagged
   artifact you can upgrade to (vLLM v0.28.0, SGLang v0.5.19, TensorRT-LLM v1.3.0rc25 — a release
   candidate). The other four are trunk commits: all three PyTorch items, and the llama.cpp one. No
   PyTorch release tag landed in the observation window, so the PyTorch items reach you through
   nightlies, not through a release upgrade.
6. **Expect the thread-count change to move CPU numbers in containers.** Clamping to the affinity
   mask makes the explicit `OMP_NUM_THREADS` workaround unnecessary on the default path in a pinned
   pod, and by the same token invalidates any thread setting autotuned against the old
   behavior.[^pytorch-cpuset-threads]

# Open questions

- **Tier.** Filed `frontier`, not `modern-consensus`: the catalog defines the latter as multiple
  independent sources agreeing on a claim, and these five projects agree on nothing — they are five
  instances from which this concept induces a class. The shared timing is coincidence.
- **What this concept deliberately does not carry: performance numbers.** The release-note bodies of
  these projects were not retrievable in verifiable form this week (see the coverage note in the
  [catalog update log](../log.md) for 2026-09-07), so every speedup figure circulating with these
  releases is omitted. Every claim above is read from source files and commit messages at pinned
  refs.
- **An internal contradiction in the SGLang source, flagged rather than resolved.** `environ.py`
  tells the user to unset `SGLANG_ENABLE_UNIFIED_RADIX_TREE`, while at the same tag
  `mem_cache/kv_cache_builder.py` still raises on the disaggregated-decode plus hybrid-SWA path
  unless that same variable is set to 1, and the variable defaults to
  `False`.[^sglang-radix-default] A deployment on that path should test before unsetting it.
- **Dates are committer dates at the tagged commit, which run ahead of the published release.**
  vLLM v0.28.0's tag commit is 2026-08-24 while its release page lists 26 Aug; SGLang v0.5.19's tag
  commit is 2026-09-03 while the annotated tag object was written 2026-09-04. The window stated
  above (2026-08-24 to 2026-09-04) spans both conventions. The release-page dates could not be
  verified from this session, so the tag artifacts are used throughout.
- Whether the vLLM ≥160 GiB tier is well chosen for any specific workload is not addressed by the
  source, which states the intent ("use the largest defaults") and not a
  justification.[^vllm-028-args]
- Author affiliations are omitted where the commit artifacts do not evidence them; all three PyTorch
  commits carry personal email addresses.

# Conflict with a stable concept

The stable [scope boundary](../foundations/scope-boundary.md) records, in the draft-coverage section
added by expedition weekly-2026-08-17, that "Inference deployment more broadly remains uncovered".
This draft covers part of that ground — the upgrade and default-management discipline for inference
engines — and so narrows what that sentence excludes. **The boundary still governs:** this is a
draft, usable only with `Evidence: unverified` stated, and nothing here covers capacity planning,
kernel selection, or engine choice. Recorded here and reflected in the boundary's draft-coverage
section, not resolved.

# Related

- [Speculative-decoding concurrency dependence](speculative-decoding-concurrency.md) — the same
  lesson one level down: a serving parameter tuned at one operating point is untuned at another.
- [The dangerous defects are the ones that do not raise](silent-training-defects.md) — the training
  side of the same distinction between loud and silent change.

[^vllm-028-args]: vllm-project/vllm, `vllm/engine/arg_utils.py` at tag `v0.28.0` (source id: vllm-028-args). Tag commit `2cf0a6915ce544dc493a0990f2ea38d81601128a`, committer date 2026-08-24T16:42:42-07:00. The `device_memory >= 160 * GiB_bytes` branch with `OPENAI_API_SERVER: 16384` is at lines 2582–2591. A repository-wide search at this tag finds no `override_attention_dtype` definition and no `calculate_kv_scales` outside a comment. **Correction made during the skeptic pass:** an earlier draft claimed `--performance-mode throughput` newly doubles the batch defaults; the doubling block is byte-identical at v0.27.0 (lines 2744–2749) and v0.28.0 (2788–2793), so the only change this release makes to batch sizing is the new memory tier. Verified 2026-09-07.
[^vllm-027]: vllm-project/vllm at tag `v0.27.0`, tag commit `4bdc8a788d2e2ce9165d552b3d4d8b72604626bf`, committer date 2026-08-10T11:48:34+01:00 (source id: vllm-027). Prior top tier at `arg_utils.py:2544–2549`; `calculate_kv_scales: bool = False` at `config/cache.py:111` with a `@field_validator` deprecation warning at lines 273–283; `override_attention_dtype` at `config/model.py:348`; `bitsandbytes_loader.py` and `layers/quantization/bitsandbytes.py` both resolve at this tag and 404 at v0.28.0. Verified 2026-09-07.
[^sglang-radix-default]: sgl-project/sglang at tag `v0.5.19`, tag commit `0bcd822377da7b5718e674eaf9c870d349424dd1`, committer date 2026-09-03T14:22:46-07:00; the annotated tag object was written 2026-09-04 (source id: sglang-radix-default). The `_DeprecatedEnv` note is at `python/sglang/srt/environ.py:1784–1787` and the field remains defined at line 641 "for legacy call sites"; the fall-through change is in `python/sglang/srt/mem_cache/registry.py` (v0.5.18 line 167 versus v0.5.19 line 143); the contradicting raise is in `python/sglang/srt/mem_cache/kv_cache_builder.py` around lines 255–262. Verified 2026-09-07.
[^trtllm-kvm-v2]: NVIDIA/TensorRT-LLM, `tensorrt_llm/_torch/models/modeling_deepseekv3.py` at tag `v1.3.0rc25`, tag commit `785c948197b55267260fec3f7f52e47000888d0a`, committer date 2026-08-27T19:59:30+08:00 (source id: trtllm-kvm-v2). `get_preferred_kv_cache_manager_version` returning `Literal["V2"]` is at lines 1907–1911; the base-class hook in `modeling_utils.py` states the preference "is adopted only when the user leaves ``kv_cache_config.use_kv_cache_manager_v2`` at ``\"auto\"``". The count of thirteen model files declaring the override at rc25 against zero at rc24 was confirmed during the skeptic pass by grep across `tensorrt_llm/_torch/` at both tags. The field is typed `bool | Literal["auto"]`, so `False` is a valid rollback value. Verified 2026-09-07.
[^llamacpp-preserve-reasoning]: ggml-org/llama.cpp commit e750b88, "common, server : enable preserve_reasoning kwarg by default, log its effective state (#28174)", committer date 2026-09-02 (source id: llamacpp-preserve-reasoning). The commit message describes the default, the logging and warning behavior, and deprecates setting the kwarg through `--chat-template-kwargs`; `common/arg.cpp` registers `--reasoning-preserve` / `--no-reasoning-preserve` with help text noting "(default: enabled)" and compatibility with templates carrying the `supports_preserve_reasoning` capability. Verified 2026-09-07.
[^pytorch-nccl2-default]: pytorch/pytorch commit e632bee, "[c10d] Make nccl2 the default NCCL backend (#192281)", committer date 2026-09-01 (author date 2026-08-31 local) (source id: pytorch-nccl2-default). The commit message carries the quoted inversion, notes three nccl2 compatibility gaps the defaulting exposed, and includes a TorchTitan release-test table dated 2026-08-11 reporting exact loss and grad-norm parity against legacy NCCL over 10 steps. An earlier draft stated this change had been landed, reverted and re-landed; the commit message does not say so and the claim is withdrawn. Verified 2026-09-07.
[^pytorch-cpuset-threads]: pytorch/pytorch commit 7059aa3, "Clamp default num_threads to cpuset/affinity mask (#194605)", committer date 2026-08-24 (source id: pytorch-cpuset-threads). The commit message describes the cpuinfo-derived default ignoring the affinity mask and the `libgomp: Thread creation failed` import failure under a tight process ulimit. It does not itself claim that the change removes the need for `OMP_NUM_THREADS`; that reading is this concept's, and is stated as applying to the default path only. Verified 2026-09-07.
[^pytorch-nested-reduction]: pytorch/pytorch commit abaacef, "Enable nested reductions by default in OSS (#191974)", committer date 2026-09-03 (author date 2026-09-02 local) (source id: pytorch-nested-reduction). Quoted text from the commit message, which also notes internal enablement is JustKnob-gated and rolled out separately. Verified 2026-09-07.
