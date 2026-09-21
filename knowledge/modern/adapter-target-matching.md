---
type: Decision Rule
title: "A non-first adapter matching no target_module was a silent no-op — assert the match"
description: >
  PEFT accepted, without error, a SECOND or later adapter whose target_modules matched no module,
  producing a model that trained zero parameters; a first adapter always raised. PEFT v0.21.0 turns
  both cases into an exception, but the underlying hazard is permanent: target_modules are matched
  by string, and upstream renames of attention submodules invalidate a working recipe. Assert the
  targeted-module count before training.
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
    title: "huggingface/peft commit 6a687e9 — ENH Raise when a non-first adapter matches nothing (#3534)"
    author: Hugging Face PEFT contributors (Singaraj B, PR #3534)
    last_modified: 2026-08-18
  - id: peft-docs
    resource: https://github.com/huggingface/peft/blob/v0.21.0/docs/source/package_reference/lora.md
    title: "peft docs/source/package_reference/lora.md at tag v0.21.0 — shipped ViT-family target_modules example"
    author: Hugging Face PEFT contributors
    last_modified: 2026-09-15
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

**Know what the assertion can and cannot catch.** `targeted_module_names` is a *cumulative,
tuner-level* list, and from v0.21.0 it is de-duplicated.[^peft-nomatch] For the multi-adapter case
below, a count alone therefore cannot separate "adapter 2 matched the same modules as adapter 1"
from "adapter 2 matched nothing". On v0.21.0+ rely on the raised `NoMatchingPeftModuleError` for
the zero-match case and use the count to catch *partial* matches; on older PEFT the count is your
only signal, and you should compare the list before and after adding each adapter.

**PEFT accepted the zero-match case silently for non-first adapters.** Until v0.21.0, PEFT raised
only when the *first* adapter's `target_modules` matched nothing; subsequent adapters matching
nothing were accepted, yielding a model with zero trainable adapter parameters. The maintainers
commit message states it directly: *"So far, PEFT would raise an error when an adapter is created (get_peft_model,
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
**Consequence: any `target_modules` list naming `"query"`, `"key"` or `"value"` will match nothing
on these models after this lands** — and that includes the pattern PEFT's own LoRA documentation
ships, `target_modules=["query", "value"]`, which the same page describes as the default: *"The
default LoRA settings in PEFT add trainable weights to the query and value layers of each attention
block."*[^peft-docs] Pretrained *weight* loading is handled: the same commit adds a new
`"Dinov2Model"` conversion entry (and an identical `"Dinov2WithRegistersModel"` one) with
`WeightRenaming("attention.attention.query", "attention.q_proj")` and siblings, and registers
`Dinov2Backbone` and `Dinov2WithRegistersBackbone` against them.[^tf-dino] **Nothing in that commit
remaps a PEFT config**, so user-authored adapter checkpoints and `target_modules` strings are not
carried across; that gap is this concept's inference from the diff, not a statement by the source.

**Upgrade order decides whether you get an outage or a silent loss.** Because the PEFT guard and the
`transformers` rename are independent, a DINOv2 adapter recipe naming the old submodules fails
differently depending on which you upgrade first. **With new `transformers` and old PEFT, a single
adapter still raises — that case always did — but a second or later adapter trains zero parameters
silently. With new PEFT, both raise.** **Prefer the version pair that raises.**
Per [release-containment discipline](release-containment-discipline.md), the rename is on `main`
and in no tag as of 2026-09-21 (newest is `v5.17.0`), so this is a migration window, not yet a
break.[^tf-dino]

# Open questions

- Whether adapter *checkpoints* trained against the old DINOv2 module names can be mechanically
  remapped is not addressed by any source read here. The conversion mapping added in the commit
  covers base-model checkpoint keys only.
- **The rename reaches beyond the eleven families whose modeling code changed.** `Dinov2Backbone`
  and `Dinov2WithRegistersBackbone` gain conversion entries, and the DepthAnything integration
  test's tolerance was loosened in the same commit — so any model consuming a DINOv2 `AutoBackbone`
  inherits the new submodule names without appearing in the list.[^tf-dino] The rename is also
  described as part of a larger vision-model refactor, so further families may follow; this concept
  does not predict which.
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

[^peft-nomatch]: huggingface/peft commit 6a687e9, "ENH Raise when a non-first adapter matches nothing (#3534)", authored 2026-08-18 by Singaraj B (source id: peft-nomatch). The first and third quotations are from the commit message; the second is the `NoMatchingPeftModuleError` docstring in `src/peft/utils/error.py`, a file created by this commit and present at tag `v0.21.0`, where the class subclasses both `PeftError` and `ValueError`. The mechanism was confirmed in the diff of `src/peft/tuners/tuners_utils.py`: the pre-commit zero-match guard tested the tuner-level cumulative `targeted_module_names`, so once adapter #1 populated it, a later non-matching adapter fell through both the raise branch and the "no module was matched" warning — hence "silently".
[^peft-docs]: peft `docs/source/package_reference/lora.md` at tag `v0.21.0` (source id: peft-docs), read 2026-09-21. `target_modules=["query", "value"]` appears at line 55, and the "default LoRA settings" sentence at line 257. Cited to establish what PEFT itself ships as the ViT-family example; **no source read here names a DINOv2-specific recipe**, and an earlier version of this draft asserted one without a source. Only two places in the repo at that tag use all three of query/key/value, neither DINOv2-specific.
[^peft-021]: huggingface/peft release v0.21.0 (source id: peft-021), 2026-09-15. Tag existence and SHA confirmed by `git ls-remote --tags` on 2026-09-21: `v0.21.0` → peeled `9dc6fa2d`, previous tag `v0.20.0` → peeled `a5526d27`. Containment of 6a687e9 in the `v0.20.0..v0.21.0` range was established during this expedition's sweep.
[^tf-dino]: huggingface/transformers commit f2f6074, "🚨 🚨Bring some dinos to modern standards (#46266)", 2026-09-15 (source id: tf-dino). The module renames, the eleven-family list (matching exactly the eleven directories under `src/transformers/models/` touched by the commit), the new `Dinov2Model`/`Dinov2WithRegistersModel` conversion entries, the `_MODEL_TO_CONVERSION_PATTERN` backbone registrations, and the loosened DepthAnything test tolerance are all read from the diff at that SHA. `git tag --contains` returned empty during the sweep; newest tag `v5.17.0` (peeled `856157a2`) confirmed by `git ls-remote --tags` on 2026-09-21.
