---
type: Decision Rule
title: "A sharded training run that does not crash is not evidence that it is correct"
description: >
  Expert-, context-, and data-parallel training paths fail silently far more often than they fail
  loudly: gradients go missing, stricter attention masks degrade to full causal, and auxiliary
  queries absorb the supervision meant for inference queries. Numerically validate any new
  parallelism configuration against a single-device reference before trusting a run, and re-validate
  after every framework upgrade that touches the sharding path.
tags: [distributed-training, expert-parallelism, context-parallelism, moe, correctness, validation]
tier: modern-consensus
applies_to:
  - enabling or changing expert parallelism, context parallelism, or a device mesh on a training run
  - upgrading a training framework version that touches sharding, attention, or loss paths
  - deciding whether a completed distributed fine-tune can be trusted or must be re-run
  - reviewing a training result whose only evidence of correctness is "the loss went down"
status: draft
stale_after: 2027-03-14
generated:
  by: expedition/weekly-2026-09-14
  at: 2026-09-14T00:00:00Z
sources:
  - id: tr-48205
    resource: https://github.com/huggingface/transformers/pull/48205
    title: "huggingface/transformers PR #48205 — fix expert-parallel MoE gradients (commit 2ca0705f7d4098dd6ae9401a058003d226675722)"
    author: huggingface/transformers contributors
    last_modified: 2026-09-08
  - id: tr-48689
    resource: https://github.com/huggingface/transformers/pull/48689
    title: "huggingface/transformers PR #48689 — residual sentinel-slot router-gradient fix (commit 67f508552c799423fa1d59cb8d0e9b2fb46488da)"
    author: huggingface/transformers contributors
    last_modified: 2026-09-11
  - id: tr-48442
    resource: https://github.com/huggingface/transformers/pull/48442
    title: "huggingface/transformers PR #48442 — add supports_context_parallel gate (commit 8eaf75f84e0ef68ccdaac14b739ace53a962bbee)"
    author: huggingface/transformers contributors
    last_modified: 2026-09-07
  - id: tr-48528
    resource: https://github.com/huggingface/transformers/pull/48528
    title: "huggingface/transformers PR #48528 — exclude denoising queries from D-FINE/RT-DETR main loss (commit 846bdfdde9c954cff7f46b7e388877c5ca1d75ea)"
    author: huggingface/transformers contributors
    last_modified: 2026-09-11
  - id: vllm-m3-mi355x
    resource: https://github.com/vllm-project/vllm-project.github.io/blob/ee2f6ddb875ae2adb3803d9c81d0733d483be572/_posts/2026-09-10-minimax-m3-mi355x.md
    title: "Optimizing MiniMax M3 on AMD MI355X (source of blog.vllm.ai)"
    author: AMD and Embedded LLM teams, published by vLLM Project
    last_modified: 2026-09-10
---

# Rule

**Treat every new parallelism configuration as unvalidated until its gradients have been compared
numerically against a single-device reference. A loss curve that descends is not that evidence.**
In the week of 2026-09-07 alone, four distinct silent-correctness defects were fixed in one
training library, each of which produced a run that trained without crashing and without being
correct.[^tr-48205][^tr-48689][^tr-48442][^tr-48528]

**The failure mode to design against is a missing gradient contribution, not a crash.** Under
expert parallelism, `torch._grouped_mm` left sentinel token-expert rows uninitialized, and the
router hook never summed per-rank partial score gradients — so gate weights and every parameter
upstream of each MoE block received gradients missing all remote-expert contributions.[^tr-48205]
The reported symptom at one end of the range is loud (`nan grad_norm` at step 2, loss collapsing
to 0), but the diagnostic that actually establishes the scope is the comparison: against a
single-GPU fp32 reference on OLMoE-1B-7B, **only 3 of 179 parameters agreed**, with relative
max-absolute errors of 0.3–2.5, described as 10–100× the noise floor; after the fix, 179/179 agreed
at a maximum relative error of 2.7e-5.[^tr-48205] **That comparison — not the loss curve — is the
test this rule asks you to run.**

**Assume one fix is not the whole bug.** A residual defect in the same path, where sentinel slots
clamped into a real expert still collected router gradient, was fixed three days later in a separate
change.[^tr-48689] A configuration that was verified against the first fix was still wrong under the
second.

**Parallelism can silently change model semantics, not just numerics.** A `supports_context_parallel`
property was added that returns `False` for any model whose `config.layer_types` contains a
non-`full_attention` layer (sliding-window, chunked), and for pre-`layer_types` models whose
`config.sliding_window` is set.[^tr-48442] The stated hazard is that under context parallelism
"the per-layer mask is dropped, so a layer using a stricter mask (sliding-window or chunked
attention) would silently train as full causal instead".[^tr-48442] **If you enabled context
parallelism on a sliding-window model family and it appeared to work, you were training a different
model than the one you configured.** Critically, this change *adds a gate; it does not enforce one*
— no in-window commit was found making the Trainer or the context-parallel entry point check the
property, so as of 2026-09-14 this remains a property you must query yourself.[^tr-48442]

**The same class of defect appears outside parallelism, wherever an auxiliary path shares a tensor
with the real one.** In D-FINE, RT-DETR and RT-DETRv2, the Hungarian-matched main loss was built
from the last decoder layer's full `logits`/`pred_boxes`, which during training with
`num_denoising > 0` still contain the contrastive-denoising queries; they were split off only for
the auxiliary and `dn_*` terms.[^tr-48528] The consequence, quoted from the change: "the matcher
assigned most targets to them and the normal queries of the inference layer received almost no
positive supervision."[^tr-48528] Denoising is on by default in the reference configs, so detectors
fine-tuned this way were trained with their inference path barely supervised — again, without any
error.[^tr-48528]

**This is not one library's problem.** Independent performance work on a different stack (MiniMax M3
on AMD MI355X, vLLM/ROCm) reports two silent correctness breaks found only because a correctness
gate was run beside each performance gate: an FP8 KV-cache view on FNUZ ROCm scored 0.0099 strict-match
on GSM8K unpatched against 0.9575 patched, and a bad expert-parallel mask gave cosine similarity 0.527
against a reference 1.0.[^vllm-m3-mi355x] **Put a correctness gate beside every performance gate** is
that post's own stated practice, and it is the generalizable form of this rule.[^vllm-m3-mi355x]

**Operational consequence.** If you ran an expert-parallel MoE fine-tune on `transformers` before
2026-09-08, or a context-parallel run on a sliding-window model, or a D-FINE/RT-DETR fine-tune with
denoising enabled, the correct default is to re-validate and, where validation fails, re-run — not to
assume the result was merely slower than it could have been.[^tr-48205][^tr-48442][^tr-48528]

# Open questions

- All four `transformers` measurements are the respective commit authors' own, quoted from commit
  messages; none has been independently reproduced here or, as far as these sources show, by any third
  party. The *existence and direction* of each defect is established by the merged diff; the precise
  magnitudes (3/179, 2.7e-5, 0.0099 vs 0.9575, 0.527) are author-reported.
- The 179-parameter comparison is reported for one model (OLMoE-1B-7B) at one precision (single-GPU
  fp32 reference). How large the gradient error is for other MoE architectures, or at bf16 reference
  precision, is not established by these sources.
- No source here quantifies how much final model quality actually degraded in an affected run. "The
  gradients were wrong" is established; "the resulting checkpoint is unusable" is an inference, and
  the honest position is that it is unknown without re-running.
- The `supports_context_parallel` property reasons about the text tower only (it reads
  `config.get_text_config()`), so its verdict for multimodal models covers less than the name
  suggests.[^tr-48442]
- These are the defects that were *found and fixed* in one week. The rate at which they are being
  found is evidence that others remain unfound; it is not evidence that this particular library is
  worse than its alternatives, and this concept should not be read as a comparative judgement between
  frameworks.

# Conflict with a stable concept

The stable [scope boundary](../foundations/scope-boundary.md) lists "LLM / foundation-model
fine-tuning (LoRA, PEFT, instruction tuning)" as not covered by any stable concept, and this draft
speaks directly to validating MoE and long-context *fine-tuning* runs. **The stable concept wins:**
the advisor must still give the canonical OUT-OF-SCOPE response for fine-tuning methodology
questions. This draft covers only the validation discipline applied to a distributed run — a
question about whether a training result can be trusted, not about how to tune. It is usable only at
`Evidence: unverified`. Recorded here rather than resolved; promotion would require the boundary to
be revised deliberately.

This concept also strengthens, rather than conflicts with, the stable
[evaluation protocol by size](../foundations/evaluation-protocol-by-size.md): that concept governs
how you estimate generalization from a correct training run, and says nothing about establishing
that the run was correct in the first place. The two are sequential, not alternative.

[^tr-48205]: huggingface/transformers PR #48205 (source id: tr-48205), merged 2026-09-08, commit `2ca0705`. The uninitialized sentinel rows, the unsummed per-rank router-score gradients, the `nan grad_norm` symptom, and the 3/179 → 179/179 single-GPU fp32 comparison with its error magnitudes are stated in the commit message; the code change spans `integrations/moe.py`, `distributed/tensor_parallel.py`, `trainer.py`, and `trainer_optimizer.py`. Date from `git log -1 --format=%ci` on a local clone.
[^tr-48689]: huggingface/transformers PR #48689 (source id: tr-48689), merged 2026-09-11, commit `67f5085`. A separate residual defect — sentinel slots clamped into a real expert still collecting router gradient — establishing that #48205 alone was not sufficient. Date from `git log`.
[^tr-48442]: huggingface/transformers PR #48442 (source id: tr-48442), merged 2026-09-07, commit `8eaf75f`. Adds `PreTrainedModel.supports_context_parallel` (24 added lines in `modeling_utils.py`) plus a `_supports_context_parallel` class flag for models context parallelism can never express (attention sinks); the quoted "silently train as full causal" hazard and the linear-attention exclusion are from the added docstring. That no in-window commit enforces the gate was established by searching the window's commits, and is an absence-of-evidence finding rather than a statement in the source. Date from `git log`.
[^tr-48528]: huggingface/transformers PR #48528 (source id: tr-48528), merged 2026-09-11, commit `846bdfd`. Five added lines each in `loss/loss_d_fine.py` and `loss/loss_rt_detr.py` plus regression tests; the quoted sentence about the matcher and the scope limit (affects training with `num_denoising > 0` only; inference unchanged) are from the commit. Date from `git log`.
[^vllm-m3-mi355x]: vLLM blog, "Optimizing MiniMax M3 on AMD MI355X" (source id: vllm-m3-mi355x), read at repo commit `ee2f6dd`, post dated 2026-09-10. The FP8-KV-view GSM8K figures, the expert-parallel mask cosine-similarity figure, and the practice of pairing a correctness gate with every performance gate are stated there. Vendor-authored (AMD and Embedded LLM); see the performance-attribution concept for this post's other caveats.
