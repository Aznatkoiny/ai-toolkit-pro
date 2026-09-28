---
type: Decision Rule
title: "A published speedup is only defined by its measurement boundary and its load regime"
description: >
  Three independent 2026-09 engineering reports each publish several different speedups for the
  same change, depending on where it was measured and under what load: a 5.05x kernel geomean
  alongside separately-reported serving effects of 2.9-4.5% and 6-19%, a KV-cache change whose
  decode gain is 26-30% at matched concurrency but 37-78% under capacity-driven load and whose
  TTFT moves in opposite directions between those two regimes, and a 3-30x tokenizer gain measured
  in a Rust crate with Python binding overhead excluded. All three state their conditions. Quoting
  any single number without its boundary and regime is the error.
tags: [benchmarks, performance, inference, serving, evaluation, kernels, evidence]
tier: modern-consensus
applies_to:
  - reading a published speedup from an engineering blog, release note, or kernel benchmark
  - deciding whether an optimization is worth integration effort
  - setting a performance expectation for a serving deployment from a component measurement
  - quoting a performance number to someone else
status: draft
stale_after: 2026-12-28
generated:
  by: expedition/weekly-2026-09-28
  at: 2026-09-28T00:36:57Z
sources:
  - id: trtllm-gvr-v2
    resource: https://raw.githubusercontent.com/NVIDIA/TensorRT-LLM/6752b2a32610996f9938ec0bb877eb4dd5f8bbb1/docs/source/blogs/tech_blog/blog29_GVR_V2_Self_Sampling_Exact_TopK_for_Sparse_Attention.md
    title: "GVR V2: Self-Sampling Exact Top-K for Sparse Attention (TensorRT-LLM tech blog 29)"
    author: NVIDIA TensorRT LLM Team
    last_modified: 2026-09-22
  - id: sglang-nvfp4-kv
    resource: https://raw.githubusercontent.com/lm-sys/lm-sys.github.io/722a68b/blog/2026-09-16-nvfp4-kv-cache.md
    title: "NVFP4 KV Cache (source of lmsys.org/blog/2026-09-16-nvfp4-kv-cache)"
    author: SGLang, Qwen, and NVIDIA teams
    last_modified: 2026-09-22
  - id: hf-tokenizers-v1
    resource: https://raw.githubusercontent.com/huggingface/blog/e363acf/tokenizers-v1.md
    title: "tokenizers v1 (source of huggingface.co/blog/tokenizers-v1)"
    author: Hugging Face (ArthurZ, sbrandeis, mcpotato, lysandre)
    last_modified: 2026-09-21
---

# Rule

**A speedup is not a scalar. It is a function of where you measured (kernel, phase, library, served request) and under what load regime (fixed concurrency, or letting freed capacity raise concurrency). Well-run reports publish several numbers for one change and name each condition. Your job is to find the number whose condition matches your deployment — not to carry the largest one, and not to assume the smallest is the honest one.** Three independent reports from one week make this concrete, and each states its conditions in its own text.

## One change, several honest numbers

**A kernel geomean and a serving delta measure different things, and the report says which.** NVIDIA's GVR V2 Top-K kernel reports "**5.05× geometric-mean speedup over TensorRT LLM radix CUDA**, with **1.46× over GVR V1**" over 9,746 workloads.[^trtllm-gvr-v2] Its methodology states that each case "repeats one captured row across 1 to 1,024 batch rows to measure kernel scaling. It does not represent heterogeneous serving concurrency," reporting "cold-L2 GPU kernel time, excluding compilation, input preparation, and Python overhead."[^trtllm-gvr-v2] Its serving figures are reported separately, as **two** distinct increments: "Adding V2 prefill to a deployment already using V2 decode improves serving throughput by **2.9–4.5%** on the tested long-input, batched workloads," and "For decode, PR #18410 reports **6–19% lower time per output token** on 8×B200 with TP8/EP8 and batch/concurrency 1."[^trtllm-gvr-v2]

**Read those two carefully, because neither is "the end-to-end effect of the 5.05×".** The 2.9–4.5% is explicitly the *incremental* benefit of adding the prefill change to a deployment that already has V2 decode — the post labels both figures "historical integration results" and says they "measure the incremental benefit of the prefill change."[^trtllm-gvr-v2] The decode figure is a different arm at batch/concurrency 1. The post then supplies the general rule better than any outside summary could: "**The serving benefit depends on Top-K's share of total execution time; the kernel comparisons above do not measure competing serving stacks.**"[^trtllm-gvr-v2] **That sentence is the concept.** A component speedup is bounded by that component's share of your execution time, and the report is telling you to go compute that share.

**A geomean also hides its own tail.** The minimum against GVR V1 is **0.689×**, which the post states as "V2 takes about 45% longer than V1 in the worst measured case," with a 99.57% win rate; one layer reaches 0.689× inside a shape whose average is 1.05×.[^trtllm-gvr-v2] The post marks these rather than hiding them. **Read the minimum alongside the mean.** Note also that its speedups "are geometric means over matched workloads from separate benchmark runs"[^trtllm-gvr-v2] — baselines measured in separate campaigns rather than interleaved, which admits drift in driver, clocks and thermals.

## The load regime can reverse the sign, not just the size

NVFP4 KV cache is the sharpest example, because the same change produces opposite-signed latency effects in two regimes the post measures separately.

- **At matched concurrency:** "NVFP4 KV improved peak-batch decode throughput by approximately 26–30% across these workloads,"[^sglang-nvfp4-kv] and "**at matched concurrency**, mean time to first token (TTFT) increased by only 0.20–0.40% with NVFP4 in these runs."[^sglang-nvfp4-kv]
- **Under capacity-driven load,** where the freed memory is spent on more resident requests: "achieved concurrency increased from 44 requests with FP8 KV to 70 with NVFP4 KV. At 160K, it increased from 10 to 15, and at 1M from one to two. Peak-batch decode throughput improved by 37.37%, 57.75%, and 78.46%, respectively."[^sglang-nvfp4-kv] And TTFT moves the *other* way: "**Under capacity-driven load, mean TTFT instead decreased by 0.74–10.72%.**"[^sglang-nvfp4-kv]

**So "does NVFP4 KV help or hurt TTFT?" has no answer without the regime.** The post explains the mechanism — "TTFT includes admission, prefill, and queueing, so this improvement should not be attributed solely to faster prefill computation. A larger resident cache allows more requests to make progress without waiting for another request to release its KV slots"[^sglang-nvfp4-kv] — and separately notes that prefill itself gains nothing, being compute-bound while only the KV dtype changed.[^sglang-nvfp4-kv] **The post also states this concept's own thesis against its own headline:** "The decode throughput gains above also should not be read as equivalent end-to-end speedups. With very long prompts, prefill can dominate total wall time even when decode becomes substantially faster."[^sglang-nvfp4-kv]

**The non-performance axis moves too.** Accuracy is consistently lower for NVFP4 than FP8 wherever a difference appears, and the largest reported gap is the most decision-relevant: on SWE-bench Verified, "NVFP4 resolved 381 of 500 tasks (76.20%), compared with 389 (77.80%) for FP8—a difference of 1.60 percentage points."[^sglang-nvfp4-kv] The reported gaps come from a deliberately incomplete configuration — "The experiments we performed did not make use of the per-tensor FP32 global scale of NVFP4 (we use 1.0 for simplicity). Proper calibration **may** reduce numeric overflow/underflow and **may** further close the accuracy gap"[^sglang-nvfp4-kv] — so whether calibration closes the gap is hedged by the source and unresolved, not established in either direction.

## The boundary can also be a language binding

tokenizers v1 "encodes text **3 to 30 times faster** than v0.23 with one thread on an Apple M4 Max. The low end is t5-base, the high end gpt2," scaling "at **76%** of linear across eight workers," across "the ten model families v1's encode path covers."[^hf-tokenizers-v1] The boundary is stated plainly: "Every figure in this post was measured against this crate. The Python bindings wrap the same code and are built from `bindings/python`, but they add per-call overhead that none of these measurements include."[^hf-tokenizers-v1] **So the published range describes the Rust crate, and any Python consumer's gain is bounded below that by an unmeasured per-call overhead.** (That most consumers reach this library through Python rather than Rust is this concept's assumption about typical usage, not a claim the post makes.) Two further conditions: the range is checkpoint-dependent, so "30×" describes one family at the top of a 10× spread; and the measured artifact is a release candidate — "A release candidate for v1 is on crates.io"[^hf-tokenizers-v1] — which by the sibling rule in [library-upgrade silent behavior drift](library-upgrade-silent-behavior-drift.md) is not a stable release.

## Hardware and model gates apply to all three

None of these numbers is portable across hardware. GVR V2's benchmarks are on **B200**, with production dispatch requiring datacenter Blackwell SM100/SM103, K ∈ {512, 1024, 2048} and specific indexer compression ratios.[^trtllm-gvr-v2] NVFP4's results are on Qwen3.8-27B on Blackwell-generation RTX PRO 6000 hardware.[^sglang-nvfp4-kv] The tokenizer figures are single-threaded on an Apple M4 Max.[^hf-tokenizers-v1] **A speedup without its accelerator named is not a number you can plan with.**

**What to do**

1. **Name the boundary and the regime before quoting any figure.** "5.05×" and "2.9–4.5%" are both true of GVR V2 and describe different measurements; neither is "the speedup".
2. **Compute your component's share of execution time.** The GVR V2 post states outright that the serving benefit depends on it. That share, not the published ratio, bounds your gain.
3. **Decide which regime you run in** — fixed concurrency, or spending freed capacity on more concurrency. NVFP4 changes the sign of the TTFT effect between them.
4. **Read the minimum and the spread, not only the geometric mean.** A 99.57% win rate still contained a case 45% slower.
5. **Check the binding, the release status, and the accelerator**, not just the core implementation.
6. **Price the non-performance axes** — accuracy, memory, hardware floor — before treating a speedup as free.

This is distinct from, and complementary to, two existing drafts. [Published-result reproducibility](published-result-reproducibility.md) concerns claims that may be false; **the claims here are true, carefully conditioned by their authors, and still do not transfer if you drop the conditions.** [Speculative-decoding concurrency](speculative-decoding-concurrency.md) makes the narrower version of this point for one technique — that a speedup without its concurrency is not actionable — and this concept generalizes the axis from concurrency to the measurement boundary and load regime together.

# Open questions

- **A general discount factor does not follow from these cases.** The gap between component and serving numbers is governed by that component's share of execution time in each specific pipeline. The rule is to compute the share, not to apply a constant — an earlier revision of this concept asserted a fixed ~100× dilution for GVR V2 by dividing its kernel geomean by its prefill increment, which the source's own framing does not support.
- No report here gives an end-to-end number for the configuration a reader is most likely to run. GVR V2's serving figures come from different pull requests than its benchmark (#18702/#18410 vs #19076) and are labelled "historical integration results"; its decode arm was measured at batch/concurrency 1, the least production-representative point.[^trtllm-gvr-v2] The NVFP4 post's headline throughput measurements (Qwen3.8-27B on one GPU) and its appendix reproduction commands (a 397B model on 8 GPUs, TP8) are different configurations, so there is no published recipe reproducing the headline numbers.
- Several supporting figures in all three posts live in images or embedded frames rather than in prose, so they are not verifiable from the sources as cited. This concept quotes only figures present in the text.
- GVR V2's exactness is argued rather than tested: the post has a section on how verification preserves exactness and states that "Exactness follows from full-row accounting and exact refinement or recovery," but publishes no correctness test or tolerance result.[^trtllm-gvr-v2]
- Whether the NVFP4 accuracy gap closes under proper global-scale calibration is explicitly hedged by the source and is the most decision-relevant open item for anyone considering 4-bit KV.
- All three sources are published by the teams that built the thing measured. Their unusually clear self-disclosure is evidence of good faith, not independent verification; no third party has reproduced any of these numbers.

[^trtllm-gvr-v2]: NVIDIA TensorRT-LLM tech blog 29, "GVR V2: Self-Sampling Exact Top-K for Sparse Attention", read at commit `6752b2a` (source id: trtllm-gvr-v2). The 5.05×/1.46× geomeans, the kernel-scaling and cold-L2 methodology notes, the 2.9–4.5% prefill increment, the 6–19% lower time-per-output-token decode figure, the "historical integration results" label, the "serving benefit depends on Top-K's share of total execution time" sentence, the 0.689× minimum with its 45% framing and 99.57% win rate, the separate-runs caveat, the SM100/SM103 and K-value gates, and the exactness argument are all stated there. The document carries no publication date of its own; 2026-09-22 is its commit date in the repository.
[^sglang-nvfp4-kv]: "NVFP4 KV Cache", read as the GitHub-hosted source of the lmsys.org post at commit `722a68b` (source id: sglang-nvfp4-kv). The 26–30% iso-concurrency decode figure, the iso-capacity concurrency increases and 37.37%/57.75%/78.46% figures, the matched-concurrency TTFT increase of 0.20–0.40%, the capacity-driven TTFT decrease of 0.74–10.72% with its queueing explanation, the compute-bound prefill explanation, the "should not be read as equivalent end-to-end speedups" caveat, the SWE-bench Verified 381/500 vs 389/500 result, and the unused per-tensor FP32 global scale in Limitations are stated there. The post is dated 2026-09-16 in its own front matter and was committed 2026-09-22; this concept uses the commit date as `last_modified`.
[^hf-tokenizers-v1]: "tokenizers v1", read as the GitHub-hosted source of the huggingface.co post at commit `e363acf` (source id: hf-tokenizers-v1). The 3–30× range with named endpoints and the ten-family scope, the 76%-of-linear scaling, the Python-binding exclusion, and the crates.io release-candidate status are stated there. The post carries no date in its front matter; 2026-09-21 is its commit date.
