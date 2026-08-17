---
type: Decision Rule
title: "Speculative decoding is a concurrency-dependent trade, not a fixed setting"
description: >
  Draft-token acceptance decays sharply with position and the value of a drafted token flips sign
  as the server moves from memory-bound (low batch) to compute-bound (high batch), so no single
  num_speculative_tokens is optimal across a load range. Benchmark speculation at your real
  concurrency; prefer adaptive verification where the backend supports it.
tags: [inference, serving, speculative-decoding, vllm, throughput, latency]
tier: frontier
applies_to:
  - configuring speculative decoding on an LLM inference server
  - reading a speculative-decoding speedup claim from a blog post or paper
  - capacity planning where request concurrency varies over the day
status: draft
stale_after: 2027-02-17
generated:
  by: expedition/weekly-2026-08-17
  at: 2026-08-17T00:00:00Z
sources:
  - id: vllm-adaptive
    resource: https://github.com/vllm-project/vllm-project.github.io/blob/1843cc42496d0687b8c8841e16b424d150632de5/_posts/2026-08-14-dspark-adaptive-verification.md
    title: "Adaptive Verification in vLLM: DSpark confidence-scheduled verification (source of blog.vllm.ai)"
    author: vLLM Team (Lucas Wilkinson, Red Hat; Benjamin Chislett, NVIDIA)
    last_modified: 2026-08-14
  - id: vllm-repo
    resource: https://github.com/vllm-project/vllm/commit/7f7a32cfec0f1bc5b73c37200b86631523a1ea8f
    title: "vllm-project/vllm commit 7f7a32c — [Spec Decode] DSpark confidence-scheduled verification (#47808)"
    author: vLLM contributors
    last_modified: 2026-08-12
---

# Rule

**Do not treat `num_speculative_tokens` as a model-level constant. Its optimal value depends on the concurrency your server actually runs at, so any speculation setting tuned at batch size 1 is untuned for a loaded server — and vice versa.** Speculative decoding buys fewer decode steps with more compute. At batch size 1 the GPU is memory-bound with spare compute, so drafting is close to free; at high concurrency draft tokens compete with real tokens for the same compute and every rejected token wastes it, and with enough rejections throughput drops significantly.[^vllm-adaptive]

**Acceptance decays sharply within a single draft block.** On DeepSeek-V4-Pro-0813, the last drafted token of a 7-token block survives verification less than 10% of the time, against more than 70% for the first.[^vllm-adaptive] That tail token occupies a slot in every verification batch regardless. The crossover at which those slots stop being free "moves with load and workload dependent acceptance rates", which is precisely why a static block length cannot be optimal across a concurrency range.[^vllm-adaptive]

**Consequence for reading published speedups:** a speculative-decoding number quoted without its concurrency is not actionable. Ask for the batch size or concurrency sweep; a single-stream speedup tells you nothing about a server at concurrency 256.

**Where a fix exists, it is a scheduler, not a bigger draft.** vLLM's `enable_adaptive_verification` sizes the verification budget per step from the DSpark confidence head's per-token survival estimates rather than verifying the whole draft, choosing the budget that maximizes expected tokens per unit of step time against a cost table profiled at engine startup.[^vllm-adaptive] The reported behavior is qualitative — with `num_speculative_tokens: 7` it stays "on the edge of the Pareto curve" across a concurrency 1–256 sweep, behaving like a long fixed block at low concurrency and a short one at high concurrency.[^vllm-adaptive] **No speedup ratio is tabulated in the source; the Pareto claim is read off a figure.** Measured on DeepSeek-V4-Pro-0813, TP=8 on 8×B300 (SM100), expert parallel, FP8 KV cache, `max_model_len` 16384, at vLLM `main` commit `73b8394`, over 880 prompts at temperature 1.0.[^vllm-adaptive]

**Availability gate — check before you plan around it.** The feature landed 2026-08-12 as PR #47808; the commit is contained in tag `v0.27.2rc0` and is **not** an ancestor of `v0.27.1`, the newest non-rc tag at the time of writing, so as of 2026-08-17 it is release-candidate/`main` only, not in a stable vLLM release.[^vllm-repo]

**Hard constraints that disqualify most deployments today.** Adaptive verification requires FULL varlen decode CUDA graphs, i.e. an attention backend reporting `AttentionCGSupport.ALWAYS` — the DSV4 sparse-MLA, sparse-SWA, and indexer backends do so on SM100; elsewhere it is rejected at startup rather than degrading gracefully.[^vllm-adaptive] It is incompatible with `--enforce-eager`, LoRA, and pipeline parallelism, and rejects output logprobs because verification compacts logits after the forward pass.[^vllm-adaptive] In the benchmarked DeepSeek-V4 configuration `--kv-cache-dtype fp8` is additionally required, because the `fp8_ds_mla` layout rejects other KV dtypes — the source states this for that serving recipe, and does not say whether it binds every DSpark deployment.[^vllm-adaptive] **If any of LoRA, pipeline parallelism, or logprobs is in your serving contract, this option is closed and the concurrency-dependence above remains yours to tune manually.**

# Open questions

- The generalizable claim (acceptance decays with position; the memory-bound→compute-bound crossover moves with load) is measured here on one checkpoint and one hardware configuration. Where the crossover sits for GQA models on non-SM100 hardware is not established by this source.
- No absolute throughput or latency figures are published for the adaptive arm, so the size of the win over a well-tuned fixed `k` at a *known, stable* concurrency is unquantified — a deployment with steady load may lose nothing by tuning `k` once.
- Both sources are vLLM-project artifacts; no independent party has reproduced the Pareto result. Tier is `frontier` accordingly, and this concept is itself an instance of what [published-result reproducibility](published-result-reproducibility.md) warns about.

[^vllm-adaptive]: vLLM blog, "Adaptive Verification in vLLM: DSpark confidence-scheduled verification" (source id: vllm-adaptive), read at repo commit 1843cc4, post dated 2026-08-14. Acceptance rates, the memory-bound/compute-bound framing, the budget objective, benchmark configuration, and the full limitations list are stated there.
[^vllm-repo]: vllm-project/vllm commit 7f7a32c, "[Spec Decode] DSpark confidence-scheduled verification (#47808)", authored 2026-08-12 (source id: vllm-repo). Release containment checked against the repository's tags on 2026-08-17: `git tag --contains 7f7a32c` returns `v0.27.2rc0`, and the commit is not an ancestor of `v0.27.1`.
