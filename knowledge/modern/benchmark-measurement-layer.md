---
type: Decision Rule
title: "Ask which layer of the stack a speedup was measured at before believing it applies to yours"
description: >
  Three independent 2026-09 engineering reports publish large component-level speedups whose
  end-to-end effect is far smaller or not measured at all: a 5.05x kernel geomean that yields
  2.9-4.5% serving throughput, a 26-30% decode gain alongside a near-zero prefill effect and a
  small accuracy loss, and a 3-30x tokenizer gain measured in a Rust crate with the Python binding
  overhead explicitly excluded. Each discloses the gap honestly, and each headline travels without
  it. Locate the measurement boundary, then discount to your own bottleneck.
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

**Before you act on a published speedup, find the boundary it was measured across — a kernel, a phase, a library crate, or a served request — and ask what fraction of your own latency sits inside that boundary. Amdahl's law is doing the work here, and the honest reports tell you the answer if you read past the headline.** Three independent 2026-09 reports make the gap explicit and quantified.

**The clearest case: two orders of magnitude between the kernel number and the serving number.** NVIDIA's GVR V2 Top-K kernel for sparse attention reports "**5.05× geometric-mean speedup over TensorRT LLM radix CUDA**, with **1.46× over GVR V1**" over 9,746 workloads.[^trtllm-gvr-v2] The same post states the end-to-end figure: "Adding V2 prefill to a deployment already using V2 decode improves serving throughput by **2.9–4.5%** on the tested long-input, batched workloads."[^trtllm-gvr-v2] **Both numbers are correct and they describe different things.** The post says so in its methodology: each benchmark case "repeats one captured row across 1 to 1,024 batch rows to measure kernel scaling. It does not represent heterogeneous serving concurrency," and reports "cold-L2 GPU kernel time, excluding compilation, input preparation, and Python overhead."[^trtllm-gvr-v2] **Anyone quoting 5.05× as a serving expectation is wrong by roughly 100×, using the source's own figures.**

Two further cautions from the same report, both self-disclosed and both easy to lose. Its speedups "are geometric means over matched workloads from separate benchmark runs"[^trtllm-gvr-v2] — baselines measured in separate campaigns rather than interleaved, which admits drift in driver, clocks and thermals. And a geometric mean conceals regressions: the minimum against GVR V1 is **0.689×**, which the post spells out as "V2 takes about 45% longer than V1 in the worst measured case," with a 99.57% win rate; one layer hits 0.689× inside a shape whose average is 1.05×.[^trtllm-gvr-v2] **Credit where due — the report marks these rather than hiding them. Read the minimum, not only the mean.**

**A phase-level gain is not a request-level gain.** For NVFP4 KV cache, "NVFP4 KV improved peak-batch decode throughput by approximately 26–30% across these workloads,"[^sglang-nvfp4-kv] while prefill is untouched by construction: "the prefill phase is compute-bound. Since our recipe only changes the KV data type to NVFP4 and the compute data type remains unchanged, prefill attention itself does not show a performance gain," with "mean time to first token (TTFT) increased by only 0.20–0.40%."[^sglang-nvfp4-kv] **So the benefit lands entirely on decode.** For a short-output, long-prompt workload — much agentic and RAG traffic — the prefill-dominated request sees close to none of the 26–30%, and pays the small TTFT cost. **The decision rule is to weight a phase-level speedup by that phase's share of your own request profile**, which the source cannot know.

**A library-level gain is not an application-level gain.** tokenizers v1 "encodes text **3 to 30 times faster** than v0.23 with one thread on an Apple M4 Max. The low end is t5-base, the high end gpt2," scaling "at **76%** of linear across eight workers."[^hf-tokenizers-v1] The exclusion that decides whether this reaches you is stated near the end: "Every figure in this post was measured against this crate. The Python bindings wrap the same code and are built from `bindings/python`, but they add per-call overhead that none of these measurements include."[^hf-tokenizers-v1] **Most consumers of this library reach it through Python, so the published range is an upper bound on a path most readers do not use.** Note too that the range is wide and checkpoint-dependent: quoting "30×" describes one family at the top of a 10× spread.

**Speed is not the only axis that moves.** The NVFP4 accuracy cost is small but consistently in one direction, and it is measured under a deliberately incomplete configuration — the post's limitations state: "The experiments we performed did not make use of the per-tensor FP32 global scale of NVFP4 (we use 1.0 for simplicity). Proper calibration may reduce numeric overflow/underflow and may further close the accuracy gap between NVFP4 and FP8 KV."[^sglang-nvfp4-kv] **So the reported accuracy gap is an upper bound on a half-calibrated recipe, not a property of the format.** Either way, a capacity or throughput win that carries an accuracy term is a trade, and the trade has to be priced on your task.

**What to do**

1. **Identify the boundary.** Kernel time, phase time, library time, or end-to-end served request — then ask what share of your latency lies inside it. A component speedup is capped by that share.
2. **Demand the end-to-end number, and prefer the one the authors themselves publish.** In all three reports here it exists and is much smaller.
3. **Read the minimum and the spread, not the geometric mean.** A 99.57% win rate still contained a 31% regression.
4. **Check whether baselines were interleaved.** "Separate benchmark runs" is a disclosed confound worth a re-measurement on your own hardware.
5. **Check the binding and the deployment path**, not just the core implementation.
6. **Price the non-performance axis** — accuracy, memory, hardware floor — before treating the speedup as free.

This is distinct from, and complementary to, two existing drafts. [Published-result reproducibility](published-result-reproducibility.md) concerns claims that may be false; **the claims here are true, honestly reported, and still do not transfer.** [Speculative-decoding concurrency](speculative-decoding-concurrency.md) makes the narrower version of this point for one technique — that a speedup without its concurrency is not actionable — and this concept generalizes the axis from concurrency to the measurement boundary itself.

# Open questions

- **None of these reports gives an end-to-end number for the configuration a reader is most likely to run.** GVR V2's serving figures come from different pull requests than its benchmark and are labelled "historical integration results"; its decode serving gain was measured at batch/concurrency 1, the least production-representative point.[^trtllm-gvr-v2] The NVFP4 post's headline throughput numbers and its published reproduction commands are for different model and GPU-count configurations, per this expedition's reading of that post.
- **A general discount factor does not follow from three cases.** The ~100× gap for GVR V2 is specific to how small a share Top-K selection holds in that pipeline; the rule is to compute the share, not to apply a constant.
- The tokenizers post's decode and cross-library comparisons, and the NVFP4 post's concurrency curves, live in images or embedded frames rather than in text, so several supporting claims in both are not verifiable from the sources as cited. This concept therefore quotes only figures present in the prose.
- The exactness of GVR V2's selection is asserted ("the Guess–Verify–Refine exactness contract remains") without a correctness test or tolerance result in the post, so the accuracy-neutrality of that particular speedup rests on the authors' assertion.
- All three sources are published by the teams that built the thing being measured. That they disclose their own gaps as clearly as they do is evidence of good faith, not independent verification, and no third party has reproduced any of these numbers.
- Whether the NVFP4 accuracy gap closes under proper global-scale calibration is explicitly unresolved by the source and is the single most decision-relevant open item for anyone considering 4-bit KV.

[^trtllm-gvr-v2]: NVIDIA TensorRT-LLM tech blog 29, "GVR V2: Self-Sampling Exact Top-K for Sparse Attention", read at commit `6752b2a` (source id: trtllm-gvr-v2). The 5.05×/1.46× geomeans, the 2.9–4.5% serving figure, the "does not represent heterogeneous serving concurrency" methodology note, the "separate benchmark runs" pairing caveat, and the 0.689× minimum with 99.57% win rate are all stated there. The document carries no publication date of its own; 2026-09-22 is its commit date in the repository.
[^sglang-nvfp4-kv]: "NVFP4 KV Cache", read as the GitHub-hosted source of the lmsys.org post at commit `722a68b` (source id: sglang-nvfp4-kv). The 26–30% decode figure, the compute-bound prefill explanation with 0.20–0.40% TTFT, and the unused per-tensor FP32 global scale in Limitations are stated there. The post is dated 2026-09-16 in its own front matter and was committed 2026-09-22; this concept uses the commit date as `last_modified`.
[^hf-tokenizers-v1]: "tokenizers v1", read as the GitHub-hosted source of the huggingface.co post at commit `e363acf` (source id: hf-tokenizers-v1). The 3–30× range with named endpoints, the 76%-of-linear scaling, and the Python-binding exclusion are stated there. The post carries no date in its front matter; 2026-09-21 is its commit date.
