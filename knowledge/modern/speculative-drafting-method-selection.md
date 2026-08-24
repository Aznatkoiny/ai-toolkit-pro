---
type: Decision Rule
title: "A speculative drafting method is chosen per target model and workload, never inherited"
description: >
  Across five drafting methods measured on nine target models, the ranking of methods and the
  best proposal length change between workloads and even between two models in the same family,
  and some configurations fall below the non-speculative baseline. Treat the method and
  num_speculative_tokens as a benchmark result for your own target, checkpoint, and workload —
  not as a property of the method or of the model family.
tags: [inference, serving, speculative-decoding, vllm, throughput, model-selection, benchmarking]
tier: frontier
applies_to:
  - choosing between native MTP, EAGLE-3, DFlash, and DSpark for an LLM inference server
  - reading a speculative-decoding speedup table from a vendor blog post
  - deciding whether to reuse an inference configuration across models in one family
status: draft
stale_after: 2026-11-24
generated:
  by: expedition/weekly-2026-08-24
  at: 2026-08-24T00:00:00Z
sources:
  - id: amd-specdec
    resource: https://github.com/vllm-project/vllm-project.github.io/blob/d5bdc6fa151b5a8fac5d3948693f658e1a519f61/_posts/2026-08-23-speculative-decoding-amd-gpus.md
    title: "Exploring Speculative Decoding in vLLM on AMD GPUs (source of blog.vllm.ai)"
    author: AMD and Embedded LLM
    last_modified: 2026-08-23
  - id: transformers-5151
    resource: https://github.com/huggingface/transformers/releases/tag/v5.15.1
    title: "huggingface/transformers release v5.15.1"
    author: Hugging Face
    last_modified: 2026-08-19
---

# Rule

**Do not carry a speculative-decoding method or proposal length across target models. Benchmark
the (target model, draft checkpoint, workload) tuple you actually serve, because the ranking
between methods is not stable — not even inside one model family.** In a sweep of five drafting
methods (native MTP, Gemma 4 MTP, EAGLE-3, DFlash, DSpark) over nine target models, for
`Qwen3.6-27B` the maximum measured native-MTP throughput ratio exceeded the maximum measured
DFlash ratio, while for `Qwen3.6-35B-A3B` the ordering reversed: DFlash measured 1.77×–2.06×
against native MTP's 1.28×–1.49×.[^amd-specdec] The source draws the same conclusion explicitly —
"results can vary between models in the same family."[^amd-specdec]

**Speculation is not guaranteed to be a win.** For `Qwen3-8B`, EAGLE-3 measured above baseline on
GSM8K, HumanEval, and MBPP, but its largest measured MATH500 value remained *below* the
non-speculative baseline; DSpark on the same target ranged from 1.15× (MATH500) to 1.63×
(GSM8K).[^amd-specdec] A method that pays for itself on one workload can cost you on another
against the same target.

**The best proposal length is a workload variable, not a checkpoint constant.** For
`Qwen3.5-27B` with native MTP, the largest measured throughput occurred at N=5 on GSM8K and
MATH500, N=4 on HumanEval and MBPP, and N=3 on MT-Bench.[^amd-specdec] For `Qwen3.5-122B-A10B`
the largest values across the four reasoning and code datasets occurred at N=7.[^amd-specdec]
Checkpoint recommendations set a starting point and a ceiling, not an answer: a DFlash checkpoint
trained with `block_size = 16` supports at most `num_speculative_tokens = 15` (the first position
is the confirmed anchor), and the source advises testing N = 3, 7, 11, 15 rather than defaulting
to the maximum.[^amd-specdec]

**Acceptance rate is not a proxy for throughput, in either direction.** The source states that a
method may show higher throughput than baseline even with a lower acceptance rate when draft
generation is inexpensive, and that a high acceptance rate need not correspond to higher
throughput when the draft component adds overhead.[^amd-specdec] Select on end-to-end throughput
(or whichever serving metric your contract names) and use per-position acceptance only as a
diagnostic for shortening the proposal.[^amd-specdec]

**Every ratio in this source is measured at an unreported concurrency.** No request rate,
concurrency level, or client-side batch setting appears anywhere in the post, its serve commands,
or its disclaimer; the post's own Future work section lists "broader evaluation across concurrency
levels, prompt and output lengths, batch sizes, and sampling settings" as work not yet
done.[^amd-specdec] Under
[speculative-decoding concurrency dependence](speculative-decoding-concurrency.md) that makes
these numbers a single point on a curve whose shape is the deciding factor for a loaded server.
**Do not plan capacity from them.**

**The tooling is still being corrected under you.** `transformers` v5.15.1 (2026-08-19) is a patch
release whose stated purpose was to solve "a few issues with DFlash and MTP candidate generators";
its commits include a DFlash candidate-token device mismatch under `device_map="auto"` (#47877),
an MTP config failure when `mlp_layer_types` is absent (#48015), and alignment of logit
distributions for `CandidateGenerator`s using sampling (#48007).[^transformers-5151] Pin your
stack and re-measure after upgrading rather than assuming a sweep transfers across versions.

**Scope note.** This concept covers method and proposal-length *selection*. Speculator training is
out of scope here and remains uncovered by any concept in this catalog; the source sketches a
workflow but states it "does not cover speculator training in depth."[^amd-specdec]

# Open questions

- **The source's own software stack is internally inconsistent with the features it benchmarks.**
  The disclaimer reports `vLLM 0.23.1rc1.dev1120+g0f0f28b53`, yet the post benchmarks DSpark,
  whose vLLM implementation landed on 2026-08-12 and is recorded by
  [speculative-decoding concurrency dependence](speculative-decoding-concurrency.md) as first
  contained in tag `v0.27.2rc0`. A `0.23.1` build could not contain it. The discrepancy is
  unexplained in the source and is **flagged, not resolved**; until it is, treat the version string
  as unreliable rather than the measurements as invalid.
- **An internal contradiction in the reported maxima.** For `gemma-4-26B-A4B-it`, the Main
  observations section gives Gemma 4 MTP maxima of 2.74× (GSM8K) and 2.62× (MBPP), while the
  Summary cites "2.83× for Gemma 4 MTP on the same target."[^amd-specdec] No dataset is named for
  the 2.83× figure. Flagged, unresolved.
- All measurements are on AMD Instinct MI300X (gfx942) and MI355X (gfx950) under ROCm/HIP
  7.2.53211, by AMD and Embedded LLM.[^amd-specdec] Whether the same method rankings hold on NVIDIA
  hardware is not established by this source, and the authors have an interest in the platform
  performing well. Tier is `frontier` accordingly, and the concept is itself an instance of what
  [published-result reproducibility](published-result-reproducibility.md) warns about.
- The sweep is coverage-sparse: the experiment-coverage table spans nine target models × five
  methods, and only 21 of those 45 cells carry measurements.[^amd-specdec] The family-inversion
  result rests on the two Qwen3.6 rows, where only
  native MTP and DFlash were measured — no EAGLE-3 or DSpark arm exists to say whether the
  inversion is method-specific or general.
- No non-learned baselines (n-gram speculation, suffix decoding) were measured; the source names
  them as future work.[^amd-specdec] For code-editing and agentic loops with repeated token
  patterns, the comparison a builder most needs is therefore missing.

[^amd-specdec]: vLLM blog, "Exploring Speculative Decoding in vLLM on AMD GPUs" (source id: amd-specdec), read at repo commit d5bdc6f, post dated 2026-08-23. All throughput ratios, per-model proposal lengths, the block-size/`num_speculative_tokens` relation, the acceptance-vs-throughput statements, the experiment-coverage table, the Future work list, and the hardware/software disclaimer are stated there. The absence of a concurrency or request-rate setting is an absence in that source, verified across its Experimental setup, Tuning considerations, Appendix serve commands, and Disclaimer sections.
[^transformers-5151]: huggingface/transformers release v5.15.1 (source id: transformers-5151), dated 2026-08-19. The quoted release summary and the five listed commits, including #47877, #48007, and #48015, are stated on that release page.
