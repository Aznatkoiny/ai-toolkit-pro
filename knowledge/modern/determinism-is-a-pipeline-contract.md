---
type: Decision Rule
title: "Determinism is a property of the whole reduction chain, not of a flag"
description: >
  vLLM now force-disables sequence parallelism and async TP under VLLM_BATCH_INVARIANT because
  their reduce-scatter path has a batch-dependent reduction order — meaning runs that combined
  those optimizations with the batch-invariance flag were non-deterministic while appearing
  configured for determinism. An independent RL result makes the same structural point: attention
  merges, cross-TP vocabulary merges, GEMM reductions and collectives form one numerical chain,
  and pinning any single one is insufficient. Verify determinism empirically; never infer it from
  a setting.
tags: [determinism, reproducibility, inference, serving, rl, numerics, batch-invariance]
tier: modern-consensus
applies_to:
  - requiring bitwise-reproducible inference output across differing batch composition
  - aligning training and rollout logprobs in an RL post-training loop
  - debugging results that change run to run with identical inputs and seeds
  - claiming or relying on a reproducibility guarantee in a serving deployment
status: draft
stale_after: 2026-12-28
generated:
  by: expedition/weekly-2026-09-28
  at: 2026-09-28T00:36:57Z
sources:
  - id: vllm-batch-inv-config
    resource: https://raw.githubusercontent.com/vllm-project/vllm/0c87a197b856a25670cc711456533e5ef9f94d9f/vllm/config/vllm.py
    title: "vLLM config/vllm.py — sequence parallelism / async TP disabled under VLLM_BATCH_INVARIANT"
    author: vLLM contributors
    last_modified: 2026-09-27
  - id: vllm-batch-inv-doc
    resource: https://raw.githubusercontent.com/vllm-project/vllm/0c87a197b856a25670cc711456533e5ef9f94d9f/docs/features/batch_invariance.md
    title: "vLLM docs — Batch invariance (beta)"
    author: vLLM contributors
    last_modified: 2026-09-27
  - id: rl-kernel-bitwise
    resource: https://raw.githubusercontent.com/vllm-project/vllm-project.github.io/f9aac4f/_posts/2026-09-14-rl-kernel-v0-1-0-train-rollout-bitwise-consistency.md
    title: "RL-Kernel v0.1.0: train–rollout bitwise consistency (source of the vLLM blog post)"
    author: RL-Kernel Team, vime Team, and AMD Team
    last_modified: 2026-09-24
---

# Rule

**A determinism setting constrains only the operations its implementers have made deterministic. Every other reduction in the pipeline remains free to vary, so enabling the flag and leaving a non-invariant optimization on yields non-determinism that looks configured away. Verify bitwise behaviour by measurement — differing batch composition, same input — and never infer it from a setting.**

**The concrete case.** As of 2026-09-27 vLLM detects `VLLM_BATCH_INVARIANT` together with sequence parallelism or async TP and turns them off, logging: "Disabling sequence parallelism and async TP (pass_config.enable_sp / fuse_gemm_comms) when VLLM_BATCH_INVARIANT is enabled: the reduce-scatter path is not batch-invariant (see vllm-project/vllm#56370)."[^vllm-batch-inv-config] The reason is stated in the adjacent comment: "Sequence parallelism / async TP rewrite all_reduce + rms_norm into a reduce-scatter whose reduction order depends on the batch, so they are not batch-invariant."[^vllm-batch-inv-config] **The retrospective consequence is the actionable part: before this change the two settings composed silently, so a deployment that set the batch-invariance flag and enabled SP or async TP was not batch-invariant, and nothing said so.** If you have reproducibility evidence gathered under that combination, it does not establish what you think it establishes.

**A reduction order is the mechanism, and it appears in more than one place.** The same file marks a second path non-invariant independently of the above: "The fused all-reduce + RMSNorm path is not batch-invariant," returning `False` when `VLLM_BATCH_INVARIANT` is set.[^vllm-batch-inv-config] The feature's documentation lists the class generally — batch invariance "disables certain optimizations that may introduce non-determinism (such as custom all-reduce operations in tensor parallel mode, and sequence parallelism / async TP, whose reduce-scatter path is not batch-invariant)."[^vllm-batch-inv-doc] **Read that list as the current inventory of known offenders, not as a closed set**: the documentation states that "batch invariance is currently in beta. Some features are still under active development."[^vllm-batch-inv-doc]

**Treat the fix as temporary.** The in-source comment is explicit that disabling is a holding action, not the design: "TODO: This is a stopgap that turns sequence parallelism / async TP off under batch invariance. Make the sequence-parallel reduce-scatter path batch-invariant instead so they can stay enabled (#56370)."[^vllm-batch-inv-config] So the performance cost of choosing determinism here is expected to fall, and **the current behaviour — silently losing two optimizations — will itself change.** Anyone who benchmarks the cost of batch invariance today is measuring a transient.

**The structural claim, from an independent direction.** An RL post-training result reaching bitwise train–rollout agreement frames the same problem as a contract over a node's whole numerical behaviour and concludes: "Attention's Split-KV merge, linear logprob's cross-TP vocabulary merge, GEMM's K-dimension reduction, and ROCm collectives are therefore parts of one numerical chain. The RL-Kernel strict path fixes these boundaries together; pinning down a single kernel or collective is not enough to guarantee bitwise-identical logprobs."[^rl-kernel-bitwise] Its reported result is narrow and specific: on "an end-to-end Qwen3-8B GRPO experiment on AMD Instinct MI300X, the vime + RL-Kernel strict path ran for 200 consecutive steps with mismatch_count = 0 and max_abs_diff = 0 throughout."[^rl-kernel-bitwise] **Two independent efforts — one a serving engine's config layer, one an RL training stack on different hardware — arrive at the same conclusion: determinism composes over the whole chain or not at all.** That convergence, not either result alone, is what earns this rule its tier.

**What to do**

1. **Test batch invariance, don't configure it.** Send the same request inside batches of different size and composition and compare outputs bitwise. That test is cheap and is the only thing that establishes the property.
2. **Re-validate after any change to parallelism or compilation.** TP degree, sequence parallelism, communication fusion, and graph-capture mode each sit on the reduction chain.
3. **Distrust prior reproducibility evidence collected across a version boundary** in a determinism feature that is labelled beta. Re-run it.
4. **Expect to pay throughput for determinism, and re-measure the price periodically** — here it is explicitly a stopgap whose cost is meant to shrink.
5. **In an RL loop, treat train-side and rollout-side logprobs as one numerical system.** Aligning one kernel while leaving the collectives or the vocabulary merge unpinned does not close the gap.

This is the systems-level counterpart to [published-result reproducibility](published-result-reproducibility.md): that concept concerns whether an external claim survives reproduction, this one whether your own stack can reproduce itself at all. It also sharpens [eval-harness version provenance](eval-harness-version-provenance.md) — a score that is not bitwise stable under batch composition has a noise floor that no harness bookkeeping will reveal.

# Conflict with a stable concept

The stable [scope boundary](../foundations/scope-boundary.md) lists "Reinforcement learning" among
the areas not covered by any stable concept, noting that qlib's RL execution paradigm is mentioned
in draft coverage "but RL methodology itself remains uncovered". This draft's `applies_to` includes
aligning training and rollout logprobs in an RL post-training loop, and one of its three sources is
an RL result. **The stable concept wins:** the advisor must still give the canonical OUT-OF-SCOPE
response for RL *methodology* questions — algorithm choice, reward design, GRPO or PPO variants,
credit assignment. What this draft covers is the numerical-reproducibility property of the
inference/training stack underneath such a loop, which is a serving-determinism question that
happens to bite hardest in RL. It is usable only at `Evidence: unverified`. Recorded here rather
than resolved; promotion would require the boundary to be revised deliberately.

# Open questions

- **How far outputs actually diverged under the previously-silent combination is unmeasured.** Neither source quantifies whether SP/async-TP under batch invariance produced a last-token difference or a trajectory-changing one, so the severity of that latent defect is unknown.
- **No throughput cost is published** for losing sequence parallelism and async TP, so the price of determinism in this configuration cannot be stated.
- The RL-Kernel result reports **no cost figure of any kind** — no tokens/s, step time, or overhead for the strict path — which is the number a builder needs to decide whether to adopt it. Its run is also a numerics test rather than a training result: at the reported scale it supports the bitwise claim and supports **no** claim about training quality, reward, or stability, and the post's own figures plot mismatch counts and logprob deltas rather than any downstream metric.
- The RL-Kernel evidence is one model on one accelerator family (MI300X), and its `date:` field (2026-09-24) disagrees with its filename (09-14); this concept uses the explicit `date:` field.[^rl-kernel-bitwise]
- Whether the list of non-batch-invariant paths in the vLLM documentation is complete is explicitly open — the feature is beta and under active development.[^vllm-batch-inv-doc] Absence from that list is not evidence of invariance.
- Both citations for the vLLM side are artifacts of one project, and the third source is published on that project's blog by other organizations. No fully independent party has audited either claim.

[^vllm-batch-inv-config]: vLLM `vllm/config/vllm.py` read at commit `0c87a19` (source id: vllm-batch-inv-config). The warning text, the SP/async-TP rationale comment, the "stopgap" TODO, and the separate fused all-reduce + RMSNorm guard all appear in that file.
[^vllm-batch-inv-doc]: vLLM `docs/features/batch_invariance.md` read at commit `0c87a19` (source id: vllm-batch-inv-doc). The beta admonition and the list of disabled optimizations are stated there.
[^rl-kernel-bitwise]: "RL-Kernel v0.1.0: train–rollout bitwise consistency", read as the GitHub-hosted source of the vLLM blog post at commit `f9aac4f` (source id: rl-kernel-bitwise), post `date:` field 2026-09-24. The numerical-chain conclusion and the 200-step Qwen3-8B GRPO result are stated there. The rendered blog URL was not reachable from this session, so the repository blob is the citation.
