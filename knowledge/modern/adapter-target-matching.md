---
type: Decision Rule
title: "An adapter whose target_modules match nothing is a silent no-op — assert the match, do not trust it"
description: >
  PEFT accepted, without error, a non-first adapter whose target_modules matched no module, producing
  a model that trained zero parameters. PEFT v0.21.0 turns that case into an exception, but the
  underlying hazard is permanent: target_modules are matched by string, and upstream renames of
  attention submodules silently invalidate a working recipe. Assert the targeted-module count before
  training.
tags: [peft, lora, adapters, fine-tuning, migration, silent-failure, transformers]
tier: frontier
applies_to:
  - configuring target_modules for a LoRA or other PEFT adapter
  - adding a second or subsequent adapter to an existing PEFT model
  - upgrading transformers or peft in a pipeline that trains adapters
status: draft
stale_after: 2027-03-21
generated:
  by: expedition/weekly-2026-09-21
  at: 2026-09-21T00:00:00Z
sources:
  - id: peft-nomatch
    resource: https://github.com/huggingface/peft/commit/6a687e9fbab4f4380881b9cb8af73d63d5e32b13
    title: "huggingface/peft commit 6a687e9 — raise when a non-first adapter matches no module (#3534)"
    author: Hugging Face PEFT contributors (BenjaminBossan)
    last_modified: 2026-08-18
  - id: peft-021
    resource: https://github.com/huggingface/peft/releases/tag/v0.21.0
    title: "huggingface/peft release v0.21.0"
    author: Hugging Face PEFT contributors
    last_modified: 2026-09-15
  - id: tf-dino
    resource: https://github.com/huggingface/transformers/commit/f2f6074bf545e01a1f93ee7c8fd9356ad8fc85ab
    title: "transformers commit f2f6074 — Bring some dinos to modern standards (#46266)"
    author: Hugging Face contributors
    last_modified: 2026-09-15
---

# Rule

**Before a training run starts, assert that your adapter actually attached to the modules you
intended — `assert len(peft_model.targeted_module_names) == expected` — and fail the job if it did
not.** `target_modules` is a *string-matching* interface against module names you do not control,
so any upstream rename converts a working recipe into a run that trains nothing while reporting
normal loss curves.

**PEFT accepted the zero-match case silently for non-first adapters.** Until v0.21.0, PEFT raised
only when the *first* adapter's `target_modules` matched nothing; subsequent adapters matching
nothing were accepted, yielding a model with zero trainable adapter parameters. The maintainers
state it directly: *"So far, PEFT would raise an error when an adapter is created (get_peft_model,
model.add_adapter) that doesn't match any module. However, this is only true for the first adapter
being added, subsequent adapters would not raise if they don't match anything. This is not what a
user would expect, so now this case raises an error."*[^peft-nomatch] The new
`NoMatchingPeftModuleError` deliberately subclasses `ValueError` *"for backwards compatibility with
code that intercepted the generic error raised previously"*.[^peft-nomatch] **The guard ships in
`v0.21.0` (2026-09-15); on any earlier PEFT the silent no-op is live.**[^peft-021]

**The same release changes two attributes you may be asserting on.** `targeted_module_names` and
`targeted_parameter_names` *"are now changed to no longer contain duplicates. Instead, they are
lists of unique strings in insertion order."*[^peft-nomatch] **If you already count targeted modules
as a guard, your expected number may change on upgrade** — which is a reason to re-derive the
expectation, not to drop the assertion.

**Upstream attention renames are the live trigger, and one is queued right now.** `transformers`
restructured the DINOv2 family's attention modules: `Dinov2SelfAttention` and `Dinov2SelfOutput` are
replaced by a single `Dinov2Attention` whose submodules are `q_proj`, `k_proj`, `v_proj`,
`o_proj`.[^tf-dino] The change touches `dinov2`, `dinov2_with_registers`, `dinov3_vit`, `eomt`,
`eomt_dinov3`, `pixio`, `radio`, `rf_detr`, `sapiens2`, `tipsv2` and `videomt`.[^tf-dino]
**Consequence: the canonical DINOv2 LoRA recipe `target_modules=["query", "key", "value"]` — the
pattern copied across ViT-family examples — will match nothing after this ships.** Pretrained
*weight* loading is handled, because the same commit adds checkpoint-key remapping (for RADIO,
`WeightConverter(source_patterns="attn.qkv", target_patterns=["attention.q_proj",
"attention.k_proj", "attention.v_proj"])`).[^tf-dino] **Nothing in that commit remaps a PEFT
config**, so user-authored adapter checkpoints and `target_modules` strings are not carried across;
that gap is this concept's inference from the diff, not a statement by the source.

**Upgrade order decides whether you get an outage or a silent loss.** Because the PEFT guard and the
`transformers` rename are independent, a DINOv2 adapter recipe pinned to `["query","key","value"]`
fails differently depending on which you upgrade first: with new `transformers` and old PEFT it can
train zero parameters silently; with new PEFT it raises. **Prefer the version pair that raises.**
Per [release-containment discipline](release-containment-discipline.md), the rename is on `main`
and in no tag as of 2026-09-21 (newest is `v5.17.0`), so this is a migration window, not yet a
break.[^tf-dino]

# Open questions

- Whether adapter *checkpoints* trained against the old DINOv2 module names can be mechanically
  remapped is not addressed by any source read here. The conversion mapping added in the commit
  covers base-model checkpoint keys only.
- The blast radius beyond the eleven listed model families is unknown. The rename is described as
  part of a larger vision-model refactor, so further families may follow; this concept does not
  predict which.
- Both sources are Hugging Face artifacts covering two of its own libraries. They are separate
  projects with separate maintainers, but not independent organizations, so tier is `frontier`
  rather than `modern-consensus`.
- The claim that adapters silently training zero parameters is a *common* production failure, rather
  than merely a possible one, is not established by any source here. PEFT's maintainers call the old
  behavior "not what a user would expect", which is weaker evidence than an incident count.

# Conflict with a stable concept

The stable [scope boundary](../foundations/scope-boundary.md) lists "LLM / foundation-model
fine-tuning (LoRA, PEFT, instruction tuning)" as covered by no stable concept, and this draft is
squarely about PEFT adapter configuration. **The stable concept wins:** the advisor must still give
the canonical OUT-OF-SCOPE response for fine-tuning *methodology* questions — which adapter rank to
choose, which modules are worth adapting, whether LoRA suits a task. This draft covers only the
*mechanical correctness* check that a configured adapter attached at all, and only at
`Evidence: unverified`. Recorded here rather than resolved; promotion would require the boundary to
be revised deliberately. This is the same boundary tension already recorded in
[open-weight model-selection signals](open-weight-model-selection-signals.md).

[^peft-nomatch]: huggingface/peft commit 6a687e9, "(#3534)", authored 2026-08-18 (source id: peft-nomatch). The quoted paragraphs are from the commit message; `NoMatchingPeftModuleError` and its `PeftError`/`ValueError` bases are defined in `src/peft/utils/error.py` at tag `v0.21.0`.
[^peft-021]: huggingface/peft release v0.21.0 (source id: peft-021), 2026-09-15. Tag existence and SHA confirmed by `git ls-remote --tags` on 2026-09-21: `v0.21.0` → peeled `9dc6fa2d`, previous tag `v0.20.0` → peeled `a5526d27`. Containment of 6a687e9 in the `v0.20.0..v0.21.0` range was established during this expedition's sweep.
[^tf-dino]: huggingface/transformers commit f2f6074, "🚨 🚨Bring some dinos to modern standards (#46266)", 2026-09-15 (source id: tf-dino). The module renames, the affected-model list, and the `WeightConverter` remapping are read from the diff at that SHA. `git tag --contains` returned empty during the sweep; newest tag `v5.17.0` (peeled `856157a2`) confirmed by `git ls-remote --tags` on 2026-09-21.
