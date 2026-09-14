---
type: Decision Rule
title: "Configured is not eligible, and eligible is not executed"
description: >
  A kernel or backend being enabled in configuration does not establish that it ran, and a speedup
  observed after enabling it does not establish that it caused the speedup. Verify execution with a
  dispatch trace before attributing a performance result, tune against post-sharding local tensor
  shapes rather than model-card dimensions, and re-baseline after upgrades because engines change
  which kernel executes without any change to your configuration.
tags: [performance, profiling, kernels, attribution, tensor-parallelism, quantization, benchmarking]
tier: modern-consensus
applies_to:
  - attributing a measured speedup to a specific kernel, backend, or flag
  - tuning GEMM or attention kernel selection for a sharded deployment
  - reading a vendor performance post that credits a named optimization
  - deciding whether a framework upgrade requires re-running your performance baseline
status: draft
stale_after: 2026-12-14
generated:
  by: expedition/weekly-2026-09-14
  at: 2026-09-14T00:00:00Z
sources:
  - id: vllm-m3-mi355x
    resource: https://github.com/vllm-project/vllm-project.github.io/blob/ee2f6ddb875ae2adb3803d9c81d0733d483be572/_posts/2026-09-10-minimax-m3-mi355x.md
    title: "Optimizing MiniMax M3 on AMD MI355X (source of blog.vllm.ai)"
    author: AMD and Embedded LLM teams, published by vLLM Project
    last_modified: 2026-09-10
  - id: trl-1130
    resource: https://github.com/huggingface/trl/releases/tag/v1.13.0
    title: "huggingface/trl release v1.13.0 — chunked cross-entropy tensor-core fix; PPOTrainer removal"
    author: huggingface/trl contributors
    last_modified: 2026-09-10
  - id: vllm-55899
    resource: https://github.com/vllm-project/vllm/pull/55899
    title: "vllm-project/vllm PR #55899 — BF16x3 router GEMM made unconditional on Blackwell; opt-out flag removed (commit cc4210f6719e3285fdfe4da862ae04c8dbb77ab1)"
    author: vLLM contributors
    last_modified: 2026-09-09
  - id: vllm-55170
    resource: https://github.com/vllm-project/vllm/pull/55170
    title: "vllm-project/vllm PR #55170 — reorder NVFP4 linear kernel preference on SM120/121 (commit 13cf9e05c1eda0bfe5cbfb9344343ca2737d0723)"
    author: vLLM contributors
    last_modified: 2026-09-08
---

# Rule

**Before you credit a kernel, backend, or flag with a speedup, establish that it executed.** The
strongest evidence for this rule is a vendor team publicly retracting its own attribution: while
optimizing MiniMax M3 on MI355X, the authors initially credited an INT4 QuickReduce path, then found
via dispatch tracing that the 1.5 MB decode collective never cleared QuickReduce's separate 16 MB
BF16/TP4 eligibility gate — the kernel was configured, was not eligible, and never
ran.[^vllm-m3-mi355x] Their formulation is the one to adopt: **`configured != eligible !=
executed`**.[^vllm-m3-mi355x]

**Tune against post-sharding local shapes, not model-card dimensions.** At TP8, MiniMax M3's 64 query
heads shard to 8 per rank, but its 4 KV heads and 4 index heads *replicate* to 1 per rank — so the
fused QKV projection sees a local N of 1536, not the global N divided by 8.[^vllm-m3-mi355x] Splitting
the kernel launcher into large-M and small-M regimes against the true local shape yielded a reported
7.8–9.4%.[^vllm-m3-mi355x] **A kernel tuned against the dimensions printed on the model card is tuned
for a tensor your deployment never materializes.**

**Changing the parallelism degree can change the operator graph, not merely the collective size.** The
AITER sparse-attention path requires exactly 1 KV head per rank, so TP4 takes AITER while TP2 silently
falls back to Triton.[^vllm-m3-mi355x] A TP sweep is therefore not a clean single-variable experiment:
two points in the sweep may be running different attention implementations.

**Distinguish a launch-amortization win from a mathematical one by its concurrency signature.** Folding
the shared expert into the routed-expert table is reported at 30.2% at concurrency 1, decaying to 5.6%
at 128.[^vllm-m3-mi355x] That decay *is* the diagnostic: a win that evaporates as batch size grows was
buying you fewer kernel launches, and will not survive into a loaded server. A win that holds across
concurrency is doing less arithmetic or moving fewer bytes.

**The same trap appears in training, where a dtype upcast can silently cost you the tensor cores.** TRL
v1.13.0 fixed a chunked cross-entropy path whose `lm_head` projection computed `h.float() @ w.float().t()`,
forcing fp32 SIMT execution instead of tensor cores.[^trl-1130] Nothing in the configuration said
"fp32"; the precision policy said bf16 and the kernel did not honor it. Reported end-to-end effect on
Qwen3-8B full fine-tuning (2×H100, FSDP2): 3554 → 6009 tokens/s/GPU (1.69×), and 4531 → 7125 for LoRA
(1.57×), with the isolated chunk going 23.37 ms → 3.86 ms and peak memory 5.99 → 3.03 GB.[^trl-1130]
**If your throughput is well below what the arithmetic intensity predicts, profile for an upcast before
concluding the model is simply expensive.**

**Re-baseline after upgrades, because engines change what executes underneath a frozen
configuration.** Two in-window examples from one serving engine, neither requiring any change on the
operator's side: the BF16x3 router GEMM became unconditional on Blackwell whenever `is_cuda and
is_blackwell and input_size % 8 == 0` with a bf16 activation and fp32 router weight, and its
`--enable-bf16x3-router-gemm` opt-out flag was **deleted outright**, so MoE router numerics change on
upgrade with no way to revert.[^vllm-55899] Separately, the weight-only NVFP4 kernel was demoted below
the three W4A4 kernels on SM120/121, so NVFP4 checkpoints that had been quietly falling back to W4A16
now run W4A4 — different throughput *and* different accuracy, again with no configuration
change.[^vllm-55170] **A pinned config file is not a pinned execution path.**

**Consequence for reading published performance work.** Ask of any speedup claim: was the credited
kernel shown to have executed, at what local shapes, and does the win hold across concurrency? A post
that answers all three is doing something most do not. This extends
[published-result reproducibility](published-result-reproducibility.md) from "was the result
reproduced" to "was the stated *cause* of the result ever established", and it is the general form of
the concurrency-dependence warning in
[speculative-decoding concurrency](speculative-decoding-concurrency.md).

# Open questions

- The MiniMax M3 post is vendor-authored (AMD and Embedded LLM teams) and single-source; no independent
  party has reproduced its numbers. It is nonetheless unusually self-skeptical — it retracts one of its
  own attributions, separates correctness fixes from speedups, and declines to credit a curve to a
  kernel it could not prove ran — which is why it is cited here for *method* rather than for its
  figures.[^vllm-m3-mi355x]
- That post's own weakest number is flagged by its authors: the 943.5 tokens/s/GPU MXFP4 point moves
  from TP4 to TP2, making it a deployment-density result rather than a fixed-topology speedup, and the
  hero figure carries the instruction to "compare points within a row".[^vllm-m3-mi355x] Per-optimization
  gains come from isolated A/B tests; cumulative checkpoints bundle several changes at once.
- The TRL figures are release-note measurements by the library's own authors on one hardware
  configuration (2×H100, FSDP2) and one model (Qwen3-8B). The *diagnosis* — an fp32 upcast in the
  projection — is a specific, checkable engineering claim; the 1.69× is not independently
  confirmed.[^trl-1130]
- Whether the BF16x3 router-GEMM numerics change is large enough to matter for downstream quality is
  not established by its source; the change ships alongside accuracy work (bounded TMEM accumulation
  chain, split-K reduce config, an fp64 test reference), which suggests the authors consider it an
  improvement, but no before/after quality measurement is given.[^vllm-55899]
- This concept prescribes verifying execution but does not standardize *how*; the cited practice is
  dispatch tracing, and the sources do not specify a portable tool for it across CUDA and ROCm.

# Out of scope for this concept

The MiniMax M3 post's specific launch flags and container tags, and the vLLM PRs' kernel-selection
ladders, are deployment details that change with each release and are deliberately not distilled here.
Cite the sources, not this concept, for a specific flag.

[^vllm-m3-mi355x]: vLLM blog, "Optimizing MiniMax M3 on AMD MI355X" (source id: vllm-m3-mi355x), read at repo commit `ee2f6dd`, post dated 2026-09-10 (verified from the `_posts/` filename, the post frontmatter `date: 2026-09-10`, and the single `git log` entry for the file). The QuickReduce retraction and its 1.5 MB vs 16 MB gate, the `configured != eligible != executed` formulation, the TP8 local-shape analysis and its 7.8–9.4%, the AITER-vs-Triton TP dependence, the 30.2%→5.6% shared-expert decay, and the MXFP4 TP4→TP2 caveat are all stated in the post. Measurements are on AMD Instinct MI355X with a fixed 8K-input/1K-output random dataset.
[^trl-1130]: huggingface/trl release v1.13.0 (source id: trl-1130), dated 2026-09-10. The chunked cross-entropy `h.float() @ w.float().t()` upcast, its fp32-SIMT consequence, and the 3554→6009 / 4531→7125 tokens/s/GPU and 23.37→3.86 ms / 5.99→3.03 GB figures are stated in the release notes; the configuration given is Qwen3-8B on 2×H100 with FSDP2. The same release removes `PPOTrainer`, `PPOConfig` and `modeling_value_head.py` outright — see the serving-and-training upgrade blast-radius concept.
[^vllm-55899]: vllm-project/vllm PR #55899 (source id: vllm-55899), commit `cc4210f`, dated 2026-09-09 from `git log`. The removal of `--enable-bf16x3-router-gemm` and `KernelConfig.enable_bf16x3_router_gemm`, and the `is_cuda and is_blackwell and input_size % 8 == 0` selection condition, were confirmed in the diff (`config/kernel.py`, `engine/arg_utils.py`, `gate_linear.py`). Scope: tier 3 of a 5-tier selection ladder; requires fp32 router weight, bf16 input, SM100. This commit is not contained in tag `v0.29.0` and is reachable only from `v0.29.1rc0`.
[^vllm-55170]: vllm-project/vllm PR #55170 (source id: vllm-55170), commit `13cf9e0`, dated 2026-09-08 from `git log`. The reordering of `FlashInferCuteDslNvFp4W4A16LinearKernel` below the three W4A4 kernels in `_POSSIBLE_NVFP4_KERNELS[CUDA]`, and the accompanying comment "Weight-only: a fallback on a W4A4-capable checkpoint, not a preference", were confirmed in the diff. Scope is exactly SM120/121 and only W4A4-capable checkpoints. Also reachable only from `v0.29.1rc0`, not `v0.29.0`.
