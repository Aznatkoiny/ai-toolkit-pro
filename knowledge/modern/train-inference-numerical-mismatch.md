---
type: Decision Rule
title: "Measure rollout-versus-trainer logprob divergence before blaming an RL algorithm"
description: >
  In an RL fine-tuning loop that uses one engine for rollouts and another for training,
  floating-point non-associativity makes the two engines evaluate different policies even with
  identical weights. A measured mean absolute logprob difference around 1e-2 is a systems defect,
  not an algorithm result. Instrument that divergence first; eliminating it is a debugging
  instrument with a measured ~25% throughput cost and no demonstrated reward gain.
tags: [reinforcement-learning, training, determinism, numerics, debugging, vllm, megatron]
tier: frontier
applies_to:
  - debugging instability, reward collapse, or heavy clipping in an RL fine-tuning run
  - attributing a change in RL results to an algorithm, reward, or environment change
  - deciding whether to pay for bitwise train-inference alignment in an RL stack
status: draft
stale_after: 2027-02-24
generated:
  by: expedition/weekly-2026-08-24
  at: 2026-08-24T00:00:00Z
sources:
  - id: isoexec
    resource: https://github.com/vllm-project/vllm-project.github.io/blob/c3a01c4a5807c8d900ae468897e45263373e534e/_posts/2026-08-21-isoexec.md
    title: "IsoExec: Unified Execution to Eliminate Trainer-Inference Mismatch in SkyRL (source of blog.vllm.ai)"
    author: Alexander Jiang and the SkyRL Team
    last_modified: 2026-08-21
---

# Rule

**When an RL fine-tuning run misbehaves, measure the per-token logprob difference between the
rollout engine and the trainer before changing the algorithm, the reward, or the environment.**
Synchronous on-policy RL assumes the sampling policy and the training policy are the same, but a
stack that samples with one engine (vLLM, SGLang) and trains with another (Megatron, FSDP) runs
different kernels, batch shapes, execution modes, and distributed layouts over the same weights.
Because floating-point addition is not associative, those differences change the reduction order
and therefore the token probabilities — the two engines evaluate *different policies* while
holding identical parameters.[^isoexec]

**A mean absolute divergence around 1e-2 is a defect, not a baseline.** On a single 8×H100 node
running synchronous DAPO training of `Qwen3.5-35B-A3B` on DAPO-Math-17k, the native SkyRL stack
measured a mean pre-update rollout-versus-training absolute logprob difference of
1.648 × 10⁻², standard deviation 4.035 × 10⁻², and an average per-step *maximum* of
5.073 over 50 steps.[^isoexec] A per-step maximum above 5 in log space is not a rounding artifact.
The same run under IsoExec measured 6.744 × 10⁻⁷, 6.821 × 10⁻⁷, and 7.358 × 10⁻⁶
respectively.[^isoexec]

**Know which parallelism axes can move the bits.** For forward-pass numerics with fixed inputs
and weights, data parallelism (batch partitioning, preserved by batch-invariant kernels) and
pipeline parallelism (whole layers moved without splitting their reductions, given fixed boundary
dtypes) are safe; tensor, expert, sequence, and context parallelism each restructure a reduction —
contraction splits, expert-output combination, all-reduce becoming reduce-scatter, and attention
split along the sequence dimension.[^isoexec] Changing a parallelism layout between rollout and
training is therefore a numerics change, and one worth checking before it is blamed on anything
else.

**Linear-attention architectures diverge by construction, not by accident.** Existing Gated
DeltaNet systems use a chunkwise-parallel form for training and prefill and a recurrent form for
decode; the two are mathematically identical but round differently. Comparing FLA's
chunkwise-parallel kernel against vLLM's fused recurrent kernel, the source measured a mean
per-element absolute difference of approximately 1.7 × 10⁻² with a maximum of 0.25.[^isoexec]
If your stack mixes those forms, expect divergence before you observe it.

**The naive fix is the expensive one.** Forcing the recurrent form everywhere removes GDN mismatch
but serializes in sequence length: per-layer, trainer forward+backward measured 4.42× and
rollout-engine prefill 4.31× against the native mixed implementation; forcing chunkwise everywhere
instead costs 36.6× on decode.[^isoexec] The source's chunkwise-parallel recurrent (CPR) form
measured 1.43× / 1.67× / 1.38× on trainer forward+backward, prefill, and decode
respectively.[^isoexec]

**Buy alignment for diagnosis, not for reward.** End-to-end, IsoExec measured 25.3% overhead per
full RL step (1224.6 s → 1534.0 s), from 31.3% on generation and 18.6% on policy
training.[^isoexec] **Over the same 50-step run the authors state they did not observe a
meaningful reward improvement from eliminating contract-covered mismatch.**[^isoexec] The
defensible reason to pay that cost today is that it makes an RL change attributable: with
divergence removed, a behavior change is your algorithm, harness, or environment rather than a
kernel. Treat a claim that alignment improves final reward as unestablished by this source.

**Conflict with a stable concept — recorded, not resolved.** The stable
[scope boundary](../foundations/scope-boundary.md) lists reinforcement learning among the areas the
catalog does not cover, and states that RL methodology remains uncovered. This concept sits inside
that excluded area. It covers only the *numerical integrity of an RL training stack* — a systems
diagnosis — and takes no position on RL algorithm choice, reward design, or when to use RL at all,
all of which stay OUT-OF-SCOPE. **The boundary above still governs**; the overlap is recorded here
rather than silently resolved.

# Open questions

- The corroborating evidence for mismatch causing *training* failure is cited second-hand by this
  source and was not verified by this expedition: a ByteDance VeXact study said to show mismatch
  destabilizing REINFORCE and GRPO runs, and a Fireworks report of a GLM-5.2 run at
  train–inference KL around 0.013 where clipping discarded roughly 45% of tokens and reward
  collapsed around step 20, against a stable bitwise-aligned run.[^isoexec] Both are named links in
  the post; neither was reachable from this session's network perimeter. **Do not cite the 45%
  clipping figure as established.**
- The measurement is one model (`Qwen3.5-35B-A3B`), one dataset, one node, one synchronous
  configuration, over 50 steps. Whether 1.6 × 10⁻² is typical of other stacks, or whether the
  divergence matters more in asynchronous RL where the policies genuinely differ, is not
  established here.
- 50 steps is short. The absence of a reward improvement is evidence about 50 steps, not about a
  full training run — the source frames it as such and does not claim the effect is zero.
- The overhead figure is measured against "the highest-throughput synchronous-RL configuration we
  evaluated," and the authors are the system's own developers, who have an interest in both the
  problem mattering and the overhead being small. Tier is `frontier` accordingly; see
  [published-result reproducibility](published-result-reproducibility.md).
- The contract's guarantee is scoped to "contract-covered" regions. What fraction of a real model's
  arithmetic is covered, and what divergence remains outside coverage, is not quantified in the
  source. Blackwell support, context-parallelism invariance, sparse attention, and block-FP8 MoE
  are listed as not yet done.[^isoexec]

[^isoexec]: vLLM blog, "IsoExec: Unified Execution to Eliminate Trainer-Inference Mismatch in SkyRL" (source id: isoexec), read at repo commit c3a01c4, post dated 2026-08-21. The non-associativity framing, the parallelism-axis classification, the FLA-versus-vLLM GDN kernel difference, the per-layer CPR cost table, the 50-step logprob-difference statistics, the step-timing table, the statement that no meaningful reward improvement was observed, the second-hand VeXact and Fireworks summaries, and the next-steps list are all stated there.
