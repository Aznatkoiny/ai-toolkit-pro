---
type: Decision Rule
title: "A quantization pipeline that reports success has not proven it calibrated"
description: >
  Calibration-based quantization (GPTQ, AWQ) fails silently when the calibration hook never fires:
  the run completes, the artifact loads, and the weights are bit-exact round-to-nearest. Keras
  shipped exactly this defect in every released version carrying GPTQ or AWQ, and the published
  benchmark numbers for that feature turned out to be RTN numbers. Before trusting a quantized
  artifact, check that its weights actually depend on the calibration data — quantize twice with
  disjoint calibration sets and compare hashes.
tags: [quantization, gptq, awq, keras, validation, silent-failure, deployment]
tier: frontier
applies_to:
  - quantizing a model with a calibration-based method (GPTQ, AWQ, or similar)
  - comparing a quantization implementation against a reference or against another framework
  - accepting a third-party quantized checkpoint into a deployment
  - reading a published quantization accuracy result
status: draft
stale_after: 2027-02-28
generated:
  by: expedition/weekly-2026-08-31
  at: 2026-08-31T00:00:00Z
sources:
  - id: keras-calib-fix
    resource: https://github.com/keras-team/keras/commit/37d6c4b6818a5346701ea833fc83d33395ce0b88
    title: "keras commit 37d6c4b6 — Fix GPTQ/AWQ calibration: dead hooks, zero-point range, group cache, and sequential Hessians (#23512)"
    author: Keras contributors
    last_modified: 2026-08-26
  - id: keras-awq-align
    resource: https://github.com/keras-team/keras/commit/6944627dd8bfeaad272e9aa4f968cc0f63beef76
    title: "keras commit 6944627d — Align AWQ with reference (mean stat, weight-aware scale, clipping) (#23478)"
    author: Keras contributors
    last_modified: 2026-08-21
  - id: keras-quantizer-sweep
    resource: https://github.com/keras-team/keras/commit/d0abc05616b81826278ee1574cf90f42127eb1f8
    title: "keras commit d0abc056 — Sweep quantizer correctness bugs: get() kwargs, g_idx loading, 2-bit GPTQ (#23470)"
    author: Keras contributors
    last_modified: 2026-08-20
  - id: keras-v3151-tree
    resource: https://github.com/keras-team/keras/tree/v3.15.1/keras/src/quantizers
    title: "keras/src/quantizers at released tag v3.15.1"
    author: Keras contributors
    last_modified: 2026-07-29
---

# Rule

**Treat "the quantization run completed" as evidence of nothing. Calibration-based methods degrade
to round-to-nearest when the calibration hook does not fire, and that degradation is invisible from
the outside: no exception, no warning, and an artifact that loads and generates plausible text.**
The Keras fix commit states the failure directly: `model.quantize("gptq"/"awq", config=...)` *"never
runs calibration"*, because the quantize flow switches every layer onto its quantized dtype policy
*before* the calibration loops start, after which `Operation.__call__` dispatches to
`layer.quantized_call` while the calibration context managers patch `layer.call`, *"which is never
invoked again."*[^keras-calib-fix] The consequences it enumerates are total, not partial:

> "The GPTQ Hessian stays all-zeros; the dead-feature guard replaces it with the identity, so error
> correction is a no-op and GPTQ silently degenerates to plain round-to-nearest (RTN).
> `activation_order=True` degenerates to the identity permutation."[^keras-calib-fix]

> "AWQ's activation magnitudes stay zero and are replaced by ones, so the 'activation-aware' scale
> search is activation-blind and the clip search is skipped (no stashed activation
> sample)."[^keras-calib-fix]

On why nothing surfaced it: *"Nothing fails loudly: an escape hatch (`is_gptq_calibrated` /
`is_awq_calibrated`) keeps calibration forwards numerically correct on the original fp kernel, so
quantization completes and produces plausible models."*[^keras-calib-fix] **The defect also survived
the project's own test suite** — the unit tests *"call `stream_hessians` / `stream_activations`
directly on layers that have not been policy-switched yet, where `layer.call` is still the dispatched
method"*, i.e. they exercised the calibration machinery in a configuration the real pipeline never
reaches.[^keras-calib-fix] A green test suite is not evidence either.

**Use the source's own validity check: quantize twice with disjoint calibration sets and compare
hashes.** The commit reports that pre-fix, *"quantizing with two disjoint calibration sets yields
byte-identical quantized variables (same MD5 over every kernel/scale/zero) for both GPTQ and AWQ;
post-fix the weights track the calibration data."*[^keras-calib-fix] **This is the strongest check
available and it needs no reference implementation** — if the calibration data cannot change the
output, calibration is not entering the computation, whatever the cause. A cheaper first screen is a
hook-call counter: the same commit records 0 calls pre-fix against 1152–23296 post-fix depending on
model and method.[^keras-calib-fix] Degenerate statistics are a third signal — an all-zero Hessian,
activation magnitudes uniformly one, or an identity permutation when `activation_order=True`.

**The published numbers for the feature were the numbers for the fallback.** The commit's most
consequential sentence for anyone reading a quantization benchmark: pre-fix GPTQ perplexity
*"(111.073) reproduces the 'native' number published in #21641 (111.106): the published GPTQ numbers
are RTN numbers."*[^keras-calib-fix] **A benchmark table can carry an algorithm's name for months
while measuring a different algorithm**, and nothing in the table's construction reveals it.

**Concretely, for anyone holding a Keras-quantized artifact today: the fix is in no release.** The
commit is contained in no tag as of 2026-08-31, and the newest releases (`v3.15.1` and `v3.12.4`,
both 2026-07-29) predate it; GPTQ and AWQ are nonetheless present in the released
tree.[^keras-calib-fix] [^keras-v3151-tree] The degeneration is provable, not probable, on the models
audited: pre-fix GPTQ is *"bit-exact RTN: 0/56.6M nibbles differ"* on GPT-2 and *"bit-exact RTN across
0/805,306,368 weight nibbles (48 Dense layers)"* on Llama-3.2 1B.[^keras-calib-fix]

**But read the direction of harm carefully, because it is asymmetric and counterintuitive.**

- **AWQ: a straight quality loss.** Activation-blind AWQ was clearly worse — quantization loss versus
  fp32 fell from +26.00% to +8.67% on Gemma-3 1B and from +16.80% to +11.42% on Llama-3.2 1B once
  the hooks fired.[^keras-calib-fix] If you have a Keras AWQ artifact, you left accuracy on the table.
- **GPTQ: your artifact is RTN, which on these models was *better* than naively restoring
  calibration.** The commit is explicit: *"restoring calibration does not by itself beat RTN at W4
  g128 on these small models."*[^keras-calib-fix] Hook-fixed GPTQ was worse than pre-fix RTN on all
  three audited models (Llama-3.2 1B: +60.40% versus RTN's +22.07% loss). Calibrated GPTQ only
  overtakes RTN after the *second* fix in the same commit — true-sequential Hessian re-estimation plus
  `activation_order=True` — reaching +9.9% against RTN's +22.1%.[^keras-calib-fix]

**So the actionable statement is not "your model is degraded" but "your model is not the algorithm
you configured, and any comparison you drew from it is void."** Re-run cross-framework comparisons;
do not adopt Keras GPTQ/AWQ for a production quantization pipeline on a released version yet.

**A second, independent failure class in the same commit: silently unrepresentable parameters.**
`compute_quantization_parameters` computed the unsigned asymmetric zero point as `round(-min/scale)`
without clamping the range to include zero, which *"for weight groups that are entirely negative (or
entirely positive with a narrow range) … produces zero points far outside `[0, 2^bits - 1]`
(observed up to 255 for 4-bit), which cannot be represented in any packed export format
(compressed-tensors, AutoGPTQ, AWQ) and means the quantized grid cannot represent
0."*[^keras-calib-fix] **Validate that an artifact round-trips through the packed export format you
intend to ship, not merely that it quantizes** — an in-memory model can hold parameters no
interchange format can carry.

**Divergence from a reference implementation is its own risk, separate from outright no-ops.** A
companion commit records three ways Keras AWQ had diverged from llm-awq/AutoAWQ: the activation
statistic was a running *max* of `|x|` where reference AWQ uses the per-channel *mean*; the scale
search dropped the weight-magnitude term; and there was no weight-clipping step at
all.[^keras-awq-align] A third commit found `keras.quantizers.get()` passing its kwargs dict
*positionally* into the resolved class, so *"passing real kwargs was broken entirely"*, and found
GPTQ packing only 4-bit weights — 2-bit and 3-bit were *"stored one value per uint8 byte, giving
zero storage advantage over 8-bit despite the lower precision"*, a defect worth a measured 4×
reduction once fixed.[^keras-quantizer-sweep] **A method name in a config field is not a guarantee
that the named algorithm ran, nor that a lower bit-width bought you anything.** Check that the
artifact's size actually fell.

# Open questions

- **The evidence base is real but narrow.** The quantification above rests on three models of 1.5B
  parameters or fewer (GPT-2, Gemma-3 1B, Llama-3.2 1B), one bit-width and group size (W4 g128), one
  corpus (wikitext-2), perplexity over 50 windows of 128 tokens, 128 calibration samples, single
  author, single run per configuration, with the harness in a linked
  gist.[^keras-calib-fix] No variance or repeated-seed data is reported. Whether the RTN-beats-naive-GPTQ
  ordering holds at larger scale or other bit-widths is explicitly left open by the source, which
  calls tracking that gap *"follow-up work."*[^keras-calib-fix]
- The AWQ alignment commit's own caveat limits its end-to-end numbers: *"the end-to-end toy model is
  only mildly quantization-stressed, so its KL/top-1 gains are modest and show per-seed variance; the
  per-layer reconstruction improvement is the stronger, monotone signal."*[^keras-awq-align] Its
  per-layer result — NEW ≤ OLD on 18/18 layers, mean error 1.102e-01 → 9.701e-02 — is the claim to
  rely on.
- No source states which release will carry the fix, and none offers guidance on repairing or
  detecting already-shipped artifacts beyond the checks described above.
- The evidence is one project's own commits. That the *class* of failure generalizes is an inference
  from the mechanism (a calibration hook decoupled from the dispatch path is not a Keras-specific
  construction), not something any source asserts; tier is `frontier` accordingly. The recommended
  checks are framework-agnostic, but their necessity elsewhere is unproven here.
- The regression is dated by its own commit to #21641 (2025-09-17), with AWQ inheriting the pattern
  in #21992.[^keras-calib-fix] The first release containing `keras/src/quantizers/gptq.py` postdates
  that, which is why this concept says "every released version carrying GPTQ or AWQ"; the upstream
  dating itself is the commit's claim, not independently checked here.

# Conflict with a stable concept

The stable [scope boundary](../foundations/scope-boundary.md) does not list quantization among either
its covered or its explicitly-uncovered areas, so this draft opens coverage in a region the boundary
is silent on rather than contradicting it. It is nonetheless adjacent to the boundary's
"LLM / foundation-model fine-tuning" exclusion, since post-training quantization is commonly part of
that pipeline. **The stable concept still governs:** fine-tuning methodology remains an OUT-OF-SCOPE
response, and this draft covers only the validation of a quantization artifact. Recorded here rather
than resolved.

# Relationship to other concepts

This is the implementation-side counterpart to
[published-result reproducibility](published-result-reproducibility.md): that concept warns against
trusting a benchmark claim before reproducing it, and this one supplies a mechanism by which a
reproduction can *silently* fail to run the algorithm it names — so the reproduction attempt itself
needs a validity check. The finding that published GPTQ numbers were RTN numbers is a worked instance
of the failure that concept anticipates.

[^keras-calib-fix]: keras commit 37d6c4b6, "Fix GPTQ/AWQ calibration: dead hooks, zero-point range, group cache, and sequential Hessians (#23512)", authored 2026-08-26 (source id: keras-calib-fix). All quotations verbatim from the commit body, read in full on 2026-08-31. Release containment verified the same day: `git tag --contains 37d6c4b6818a5346701ea833fc83d33395ce0b88` returns nothing; `git for-each-ref --sort=-creatordate refs/tags` gives `v3.15.1` and `v3.12.4` (both 2026-07-29) as newest. Benchmark protocol as stated in the body: "wikitext-2, seq len 128, 128 calibration samples, W4 g128, PPL over 50 test windows", three code states (pre-fix master 7a34a03db, hooks-fix only, full fix), on RunPod RTX 3090 (GPT-2) and A40 46GB (Gemma-3 1B, Llama-3.2 1B). GPT-2 PPL: fp32 109.983, pre-fix GPTQ 111.073 (0 hook calls), hooks-fix 112.277 (1152), full-fix 111.788. dPPL vs fp32: gemma3-1b GPTQ +6.99% pre-fix / +12.88% hooks-fix / +10.60% full-fix, AWQ +26.00% → +8.67%; llama3.2-1b GPTQ +22.07% / +60.40% / +48.50%, AWQ +16.80% → +11.42%. GPU acceptance table (A40, Llama-3.2 1B): RTN +22.1%, calibrated GPTQ with stale Hessians +46.3%, + true-sequential +27.7%, + `activation_order=True` +9.9%. An earlier version of this concept asserted that no source quantified the damage; that was false — the tables are in this commit body — and was corrected in the skeptic pass.
[^keras-awq-align]: keras commit 6944627d, "Align AWQ with reference (mean stat, weight-aware scale, clipping) (#23478)", authored 2026-08-21 (source id: keras-awq-align). Verified 2026-08-31: contained in no tag. Quantified evidence in its body: "NEW <= OLD on 18/18 layers. Mean error OLD=1.102e-01, NEW=9.701e-02 (ratio 0.880, ~12% lower). Per-layer NEW/OLD ratios span 0.688..0.985"; end-to-end "mean KL OLD=0.00278 NEW=0.00258 … mean top-1 OLD=0.800 NEW=0.850".
[^keras-quantizer-sweep]: keras commit d0abc056, "Sweep quantizer correctness bugs: get() kwargs, g_idx loading, 2-bit GPTQ (#23470)", authored 2026-08-20 (source id: keras-quantizer-sweep). Verified 2026-08-31: contained in no tag. The `keras.quantizers.get()` positional-kwargs defect, the 2-bit/3-bit packing waste, and the measured "65536 bytes … -> 16384 bytes … a 4x reduction" are stated in its body.
[^keras-v3151-tree]: `keras/src/quantizers/` at released tag `v3.15.1` (source id: keras-v3151-tree), tag dated 2026-07-29. Verified 2026-08-31 by `git ls-tree -r --name-only v3.15.1 keras/src/quantizers/`, which lists `gptq.py`, `gptq_core.py`, `gptq_config.py`, `awq.py`, `awq_core.py`, `awq_config.py` among others, and by confirming `stream_hessians` is defined at `v3.15.1:keras/src/quantizers/gptq_core.py` line 19.
