---
type: Decision Rule
title: "The dangerous defects in the training stack are the ones that do not raise"
description: >
  Five fixes across four repositories in one ten-day window addressed defects that raised no error
  and produced normal-looking output while corrupting gradients, weights, or calibration sampling.
  Treat "the run finished and the loss went down" as no evidence of correctness; instrument below
  the loss, read every new refusal in a dependency as a bug report about your past runs, and check
  whether the fix is in a release at all — as of 2026-09-07, none of these is.
tags: [training, qat, quantization, parallelism, peft, correctness, dependency-management]
tier: frontier
applies_to:
  - upgrading or pinning a training-stack dependency (torch, torchao, accelerate, peft, keras)
  - auditing a finished training run whose evaluation numbers came out lower than expected
  - designing the regression tests for a quantization, parallelism, or adapter code path
  - deciding whether an old checkpoint or an A/B quantization comparison can still be trusted
status: draft
stale_after: 2027-03-07
generated:
  by: expedition/weekly-2026-09-07
  at: 2026-09-07T00:00:00Z
sources:
  - id: ao-clamp-ste
    resource: https://github.com/pytorch/ao/commit/4740af75142b2d98857bc661a295c8723a08d080
    title: "pytorch/ao commit 4740af7 — Restore straight-through estimator at the fake-quant clamp boundary (#4806)"
    author: Zhiwen Owen Jiang
    last_modified: 2026-08-25
  - id: ao-bias-grad
    resource: https://github.com/pytorch/ao/commit/fa7b7eb75dd3a44e661a7be98456a5d452e5355a
    title: "pytorch/ao commit fa7b7eb — Fix NVFP4/MX QAT backward dropping the bias gradient (#4817)"
    author: Jeremy Schoemaker
    last_modified: 2026-08-24
  - id: accelerate-cp-refuse
    resource: https://github.com/huggingface/accelerate/commit/bd204169b4412c059d40318c455fe8a826374bd1
    title: "huggingface/accelerate commit bd20416 — Refuse context parallelism for models with sliding-window or chunked attention layers (#4177)"
    author: Quentin Gallouédec (Hugging Face)
    last_modified: 2026-08-31
  - id: peft-hotswap-merged
    resource: https://github.com/huggingface/peft/commit/871cad819e5da703216a97e60a6e126d3147bee5
    title: "huggingface/peft commit 871cad8 — FIX Refuse to hot-swap adapters while they are merged (#3590)"
    author: Sravan Jangam
    last_modified: 2026-09-02
  - id: keras-calib-seed
    resource: https://github.com/keras-team/keras/commit/37e91d59b957b57b9961d97bd120499ddfb36841
    title: "keras-team/keras commit 37e91d5 — Fix calibration memory, AWQ staging, and sampling reproducibility (#23514)"
    author: Jyotinder Singh
    last_modified: 2026-08-26
  - id: trl-long-context
    resource: https://github.com/huggingface/trl/blob/5dd51e4d8caf495dc4cbddcddef4c659ad8174b9/docs/source/long_context_training.md
    title: "huggingface/trl — Training Beyond 1M Tokens (docs/source/long_context_training.md at 5dd51e4)"
    author: Quentin Gallouédec (Hugging Face)
    last_modified: 2026-09-03
---

# Rule

**A run that raised no exception and produced normal-looking output is not evidence that the run was
correct.** In the ten days from 2026-08-24 to 2026-09-02, five fixes landed across four repositories
— `pytorch/ao` (twice), `huggingface/accelerate`, `huggingface/peft` and `keras-team/keras` — for
defects sharing one signature: *nothing raised, the output looked ordinary, and the result
underneath was wrong.* The class deserves its own rule because the usual defence — the job crashed,
so I fixed it — never fires.

## The five, and what each broke while looking fine

- **A gradient silently zeroed by an upstream autograd change.** A PyTorch change to `clamp`'s
  boundary subgradient — `where(self >= min, grad, 0)` became `where(self > min, grad, 0)` — is
  measure-zero for ordinary float tensors but not for fake quantization, which clamps *rounded*
  values against *integer* bounds, so "every saturated element is exactly equal to quant_min or
  quant_max". The gradient is therefore zeroed "across the whole saturated tail, silently disabling
  the straight-through estimator that QAT depends on. There is no error -- training simply diverges
  thousands of steps later."[^ao-clamp-ste]
- **A gradient never returned at all.** The NVFP4 and MX QAT autograd functions consumed `bias` in
  the forward and returned `None` in its gradient slot, so "linear.bias.grad stays None and the
  optimizer never updates any bias for the entire QAT run, silently degrading
  accuracy."[^ao-bias-grad]
- **An attention mask silently dropped.** Context parallelism "can only express full causal
  attention: the per-layer mask has to be dropped, so those layers would silently be trained with
  full causal attention instead" — which is why accelerate now refuses sliding-window and
  chunked-attention models up front.[^accelerate-cp-refuse]
- **Base weights silently corrupted by an ordinary serving operation.** Hot-swapping a LoRA adapter
  that was still merged left the old adapter effectively active, and "a later unmerge subtracted the
  NEW delta from a base containing the OLD delta, silently corrupting the model."[^peft-hotswap-merged]
- **A seed argument that did not actually fix the sampling.** Keras derived its calibration sampling
  offset from `hash(("gptq-calib", seed))`; Python randomizes string hashing per process, "so the
  offset - and with it the calibration windows and every downstream quantization result - changed on
  every run despite the fixed `seed` argument, and the code comment claiming a deterministic offset
  was wrong." Two byte-identical `model.quantize("gptq")` invocations produced perplexities of 35.02
  and 39.70, "a 4.7 PPL spread from sampling alone", which "silently confounds any A/B comparison of
  quantization changes made across separate processes."[^keras-calib-seed]

**The signature is not uniform in where it bites.** Three are training-loop defects, one is a
serving-time operation, and one confounds a post-training quantization comparison. What they share
is the absence of a signal, not a common subsystem.

## What to do about it

**1. Read a new refusal in a dependency as a bug report about your past runs.** Two of the five
fixes are a new `ValueError` where the code previously proceeded (accelerate raises twice; peft
once). When an upgrade starts refusing a configuration you have been running, the question is not
"how do I get past this" but "what did the runs I already shipped actually compute". Concretely: a
context-parallel run on a sliding-window or chunked-attention model may have been trained with the
wrong mask, if it went through accelerate's mask-dropping hook;[^accelerate-cp-refuse] the excluded
families are named elsewhere as "OpenAI GPT-OSS, Gemma 3 and 4, Qwen3.5 and later";[^trl-long-context]
an NVFP4/MX QAT run with `bias=True` linears never updated a bias;[^ao-bias-grad] a server that
merged an adapter, hot-swapped it, and later unmerged has corrupted base weights — one that merged
and hot-swapped without unmerging has been serving the old adapter.[^peft-hotswap-merged]

**2. Check whether the fix is in a release before you plan around it. Today, none of them is.** As
of 2026-09-07 the newest tagged release of each library predates its fix: torchao v0.18.0
(2026-07-31), accelerate v1.14.0 (2026-06-11), peft v0.20.0 (2026-07-28), keras v3.15.1
(2026-07-29).[^releases-checked] Two consequences: every released version in service today carries
these defects, and the protective refusals in point 1 are reachable only from `main`.

**3. Instrument one level below the loss, and keep the discriminator cheap enough to bisect with.**
The clamp defect was root-caused "by a 9-run bisect" whose discriminator was *the number of logged
steps with gradient norm above 1.0 over steps 1400–1700* (n=31) on a fixed 1B QAT job — 0 excursions
with a maximum around 0.03 on good revisions, against 1 to 7 excursions with maxima from 2.9 to 29.3
on bad ones.[^ao-clamp-ste] The transferable part is the shape: a scalar computed from gradient
norms over a fixed step window, comparable across revisions, is what makes a silent numerical
regression bisectable. A loss curve is not, because the divergence appears thousands of steps later.

**4. Put the boundary configuration in the test matrix, or the tests cannot see the bug.** The bias
defect survived because "the existing regression tests use bias=False models so they cannot catch
this."[^ao-bias-grad] For quantization and parallelism code the risky configurations — `bias=True`,
a saturated tail, a non-full-attention layer type, an already-merged adapter, a second process — are
exactly the ones a minimal test omits. The Keras fix makes the same point from the other side: its
golden-value tests hold only because the offset is now process-stable, whereas "the old hash-based
offset only reproduces them under one specific PYTHONHASHSEED by coincidence."[^keras-calib-seed]

**5. Treat cross-process A/B comparisons as suspect until the sampling is pinned.** A fixed `seed`
argument is not the same as a reproducible pipeline, and the gap is invisible: the Keras defect
produced a 4.7 PPL spread with identical inputs and no error.[^keras-calib-seed]

**6. Note what forward-value equality does *not* prove.** The clamp fix leaves forward values
"bit-identical; only the boundary gradient differs."[^ao-clamp-ste] Comparing a forward pass is
therefore not a test for this class of defect at all.

# Open questions

- **Tier.** This concept is filed `frontier`, not `modern-consensus`, and deliberately: the
  catalog's vocabulary defines `modern-consensus` as multiple independent sources *agreeing on a
  claim*, and no two of these sources agree on anything. Five independent authors each attest a
  different instance, and the generalization from those instances to a rule is the expedition's, not
  any source's. Nothing here has been replicated by another party.
- **Ten days is a window, not a rate.** Whether this density reflects a real increase in silent
  defects as quantized and sequence-parallel training spreads, or simply a week when several
  maintainers happened to look, cannot be decided from five commits. Do not cite this concept as
  evidence that the stack is getting worse.
- **The accelerate case carries a nuance the source itself records** and this concept does not
  resolve: a code comment states that without accelerate's mask-dropping hook "torch raises a shape
  error for such models, so nothing that works today starts failing here."[^accelerate-cp-refuse]
  How many real runs went through that hook and were mis-masked is not established by any source
  here, which is why point 1 says *may have been*.
- **Two of the five come from the same repository** (`pytorch/ao`), so the count of independent
  observations is four, not five.
- No source quantifies how much accuracy was actually lost in the wild. "Silently degrading
  accuracy" is a committer's characterization, not a measurement. The one measured harm is the
  Keras 4.7 PPL sampling spread, which is a reproducibility spread rather than a quality
  loss.[^keras-calib-seed]
- Affiliations are given only where the commit itself evidences them; two authors' organizational
  affiliations could not be established from the artifacts and are left unstated.

# Conflict with a stable concept

The stable [scope boundary](../foundations/scope-boundary.md) lists "LLM / foundation-model
fine-tuning (LoRA, PEFT, instruction tuning)" as covered by no stable concept, and several instances
here sit inside that area: the PEFT adapter hot-swap is LoRA, the clamp bisect subject is a "QAT
LoRA SFT job", and the context-parallelism case is LLM fine-tuning. **The stable concept wins:**
fine-tuning *methodology* questions still get the canonical OUT-OF-SCOPE response. What this draft
adds is a verification-discipline rule evidenced partly from that area, usable only at
`Evidence: unverified`. Recorded here rather than resolved.

# Related

- [Published-result reproducibility](published-result-reproducibility.md) — the same skepticism
  applied to someone else's numbers; this concept applies it to your own run.
- [Long-context SFT memory ladder](long-context-sft-memory-ladder.md) — the context-parallelism
  refusal above is a precondition of that pattern.
- [An engine upgrade re-derives your defaults](upgrade-default-rederivation.md) — the deployment-side
  counterpart of the loud-versus-silent distinction.

[^ao-clamp-ste]: pytorch/ao commit 4740af7, "Restore straight-through estimator at the fake-quant clamp boundary (#4806)", committer date 2026-08-25 (source id: ao-clamp-ste). The subgradient change, the measure-zero argument, the STE consequence, the bit-identical forward, and the bisect table are all in the commit message. The message says "9-run bisect" over a table of seven rows, one marked "(x2)". The upstream change it names is PR #191142; that bound applies to this defect only. Verified by fetching the commit at that SHA on 2026-09-07.
[^ao-bias-grad]: pytorch/ao commit fa7b7eb, "Fix NVFP4/MX QAT backward dropping the bias gradient (#4817)", committer date 2026-08-24 (source id: ao-bias-grad). Affects `torchao/prototype/qat/nvfp4.py` and `torchao/prototype/qat/mx.py`; the fix returns `grad_output.sum(0)` in the bias slot. Nothing in the source bounds when the defect was introduced. Verified by fetching the commit at that SHA on 2026-09-07.
[^accelerate-cp-refuse]: huggingface/accelerate commit bd20416, "Refuse context parallelism for models with sliding-window or chunked attention layers (#4177)", committer date 2026-08-31 (source id: accelerate-cp-refuse). The quoted text is the `ValueError` raised in `_attach_context_parallel_hooks` and the comment above it in `src/accelerate/big_modeling.py`; the same commit adds a second refusal for linear-attention layers under Ulysses sequence parallelism, whose docstring notes the resulting "gradients wrong in a way a loss curve does not show". The commit names no model families. Verified by checking out that SHA on 2026-09-07.
[^peft-hotswap-merged]: huggingface/peft commit 871cad8, "FIX Refuse to hot-swap adapters while they are merged (#3590)", committer date 2026-09-02 (source id: peft-hotswap-merged). Quote from the commit message; the fix raises `ValueError` pointing to `unmerge_adapter()`. Verified by fetching the commit at that SHA on 2026-09-07.
[^keras-calib-seed]: keras-team/keras commit 37e91d5, "Fix calibration memory, AWQ staging, and sampling reproducibility (#23514)", committer date 2026-08-26 (source id: keras-calib-seed). All quoted text and the 35.02/39.70 perplexities (Llama-3.2 1B, wikitext-2 W4 g128, RTX PRO 4500) are in the commit message. The same commit also extends execution-order staged calibration from GPTQ to AWQ, whose measured effect it reports as quality-neutral on that model (29.67 single-sweep vs 29.78 staged, "within the run-to-run spread") at +18% calibration wall time — a principled fix with no demonstrated harm, which is why the sampling defect rather than the staging one is used above. Verified by fetching the commit at that SHA on 2026-09-07.
[^trl-long-context]: huggingface/trl, "Training Beyond 1M Tokens", `docs/source/long_context_training.md` at commit 5dd51e4, dated 2026-09-03 (source id: trl-long-context). Cited here only for the list of model families accelerate's refusal excludes, which the accelerate commit itself does not name. Verified by fetching the file at that SHA on 2026-09-07.
[^releases-checked]: Release containment checked on 2026-09-07 against each repository's newest tag by fetching the fixed file at that tag: torchao v0.18.0 (2026-07-31) contains no `_ClampSTE`; accelerate v1.14.0 (2026-06-11) contains `_attach_context_parallel_hooks` without the refusal string; peft v0.20.0 (2026-07-28) has no `unmerge_adapter` guard in `hotswap.py`; keras v3.15.1 (2026-07-29) still carries the pre-fix `hash(("gptq-calib", seed))` in `keras/src/quantizers/gptq_core.py`. Each fix is `main`-only as of this date. This is the expedition's own check, not a claim made by any source.
