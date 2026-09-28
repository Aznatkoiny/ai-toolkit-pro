---
type: Decision Rule
title: "A benchmark score is a property of the harness version, not only of the model"
description: >
  In a single week, four independent scoring defects were corrected in mainstream open eval
  tooling: a text-F1 scorer that ignored token multiplicity, an aggregation that charged judge
  failures to the model under test, samples cancelled from outside being scored as completed
  successes, and two benchmark rows that are unanswerable by construction. Record the harness
  version, config and judge model beside every score; a score without them is not comparable to
  anything, including your own earlier runs.
tags: [evaluation, benchmarks, reproducibility, tooling, provenance, scoring]
tier: modern-consensus
applies_to:
  - comparing a measured score against a number published in a paper or model card
  - comparing two models scored at different times, or on different harness versions
  - deciding whether an eval result is trustworthy enough to gate a release or a model swap
  - building an internal eval suite on top of a third-party harness
status: draft
stale_after: 2027-03-28
generated:
  by: expedition/weekly-2026-09-28
  at: 2026-09-28T00:36:57Z
sources:
  - id: inspect-ai-changelog
    resource: https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_ai/d01e09c19ff13a3e9f3870173d3747a5b0427f3c/CHANGELOG.md
    title: "Inspect AI CHANGELOG (releases 0.3.253, 0.3.269, 0.3.270)"
    author: Inspect AI maintainers (UK AI Security Institute / Meridian Labs)
    last_modified: 2026-09-25
  - id: inspect-ai-f1-src
    resource: https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_ai/main/src/inspect_ai/scorer/_classification.py
    title: "Inspect AI f1() scorer implementation (multiset token counting)"
    author: Inspect AI maintainers
    last_modified: 2026-09-26
  - id: inspect-evals-paperbench
    resource: https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_evals/dbd3dd25e81d5f5fc4d19860b496a34176da6c61/src/inspect_evals/paperbench/README.md
    title: "Inspect Evals PaperBench README — scoring deviation and graded_weight_fraction"
    author: UK AI Security Institute (inspect_evals)
    last_modified: 2026-09-24
  - id: inspect-evals-bbh
    resource: https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_evals/dbd3dd25e81d5f5fc4d19860b496a34176da6c61/src/inspect_evals/bbh/README.md
    title: "Inspect Evals BIG-Bench Hard README — Known dataset issues"
    author: UK AI Security Institute (inspect_evals)
    last_modified: 2026-09-25
---

# Rule

**Treat an eval score as a measurement made by a specific version of a specific harness under a specific config, and record all three beside the number. A score carried without its harness version is not comparable to a published number, to another model, or to your own run from last month.** The week of 2026-09-21 supplies four independent demonstrations from mainstream open tooling, each with an exact version boundary.

**A scorer can reward the failure mode you are trying to measure.** Inspect AI's `f1()` normalized both answer and target into a Python `set`, discarding token multiplicity, so a padded or repetitive answer paid no precision cost: the changelog's own example is that `"Paris Paris Paris Paris Paris"` scored a perfect 1.0 against the target `"Paris"`.[^inspect-ai-changelog] Release 0.3.270 counts with a `Counter` and intersects multisets, matching SQuAD F1 — the shipped implementation derives precision and recall from `sum(...values())` rather than `len(...)`.[^inspect-ai-f1-src] The changelog states plainly that "scores can rise or fall for answers or targets containing repeated words."[^inspect-ai-changelog] **The hazard is that the inflation is model-dependent:** it accrues to verbose, repetition-prone outputs, so it can distort a *ranking* between two models and not merely shift a level. That ranking consequence is an inference from the mechanism, not a claim the source makes.

**This is a recurring class in the same tool, not a one-off.** The same defect — a text scorer comparing unordered sets and so collapsing duplicates — was corrected in `exact()` six weeks earlier, in 0.3.253 (08 August 2026), where "world hello" had scored as an exact match for "hello world"; that entry also warns that `exact()` scores "may decrease on existing evals where answers matched only via word reordering or duplicate collapse."[^inspect-ai-changelog] **Two scorers in one library, two releases apart, with the same root cause. Do not assume the string-matching layer of a harness is settled.**

**Judge failures can be charged to the model under test.** In Inspect Evals' PaperBench, a rubric criterion the judge could not grade scored `0.0` — indistinguishable from a criterion the reproduction genuinely failed. Ungraded criteria are now dropped from both sides of the weighted average, and a new `graded_weight_fraction` metric reports "the share of the rubric weight those criteria represent," which "is 1.0 when every criterion was graded."[^inspect-evals-paperbench] **Read the new metric, because the fix carries its own bias in the opposite direction**, as the README states: "Leaving ungraded criteria out of the divisor raises the reported score if the judge fails more often on criteria the reproduction did not meet. Read `graded_weight_fraction` alongside `score` for this reason."[^inspect-evals-paperbench] Note also what this does to cross-implementation comparison: the reference implementation "averages over every child, including those whose grading failed," so "scores produced by this implementation are therefore not directly comparable with published PaperBench numbers when the judge fails to grade any criterion."[^inspect-evals-paperbench] Fixing the aggregation made it *diverge* from the published numbers — so a PaperBench figure now needs the harness version as well as the judge model.

**Name the judge model, always.** The PaperBench README instructs that "to compare results across different solver models, use the same judge model for scoring," that the original paper used `openai/o3-mini-2025-01-31`, and that "a run should record the judge model used."[^inspect-evals-paperbench] A judged benchmark number quoted without its judge is not a measurement of the model.

**Infrastructure failures can be scored as model outcomes.** Release 0.3.269 records that "samples whose solver is cut off by a cancellation that inspect did not issue are now recorded as sample errors instead of being scored as completed."[^inspect-ai-changelog] Before that boundary, an externally killed sample entered scoring as a completed run. **The direction of the resulting bias depends on how often foreign cancellations occurred in your environment, which none of these sources quantifies** — it is plausibly negligible for short tasks and material for long-horizon agentic runs, where cancellations are more common, but that contrast is an inference and is not established by the source.

**Some benchmark rows cannot be answered at all, and some published gold labels are known to be wrong and kept anyway.** BIG-Bench Hard's `ruin_names` rows 100 and 145 have "their options split on the commas inside the candidate names, so the lettered options are fragments and the target is a full name that is not among them"; they "cannot be scored by option letter and are excluded," leaving `ruin_names` to run 248 items, and the defect is present in the mirror the port loads.[^inspect-evals-bbh] Separately, row 41 (`'frank kappa'`) "has the unchanged input as its gold answer, which contradicts the task definition," and the README states the row "is kept as published."[^inspect-evals-bbh] **That second item is the more useful one: a known-wrong label deliberately retained for comparability.** It means a BBH number contains a small, documented quantity of noise by design — so a sub-percentage-point difference on BBH is not a difference. On the suite's size: the README describes 27 tasks, "most containing 250 samples," totalling 6,511 published samples;[^inspect-evals-bbh] with the two unanswerable rows excluded, 6,509 are loaded. A per-subtask count of 250 is not the suite total, and a documented sample count is itself a thing to check.

**What to do**

1. **Pin the harness.** Record the exact harness version alongside every score you keep, and pin it in the environment that produces release-gating numbers. A harness upgrade is a re-baseline event.
2. **Record the config that decides the number:** judge model, subset, metric variant, and dataset revision. Several of the above change silently with defaults.
3. **Never compare across a version boundary without re-running the baseline.** Four of these changes move scores; two move them in a direction the source declines to predict.
4. **Treat a small delta as noise unless you know the harness's own defect budget.** Known-wrong retained labels and excluded rows put a floor under what a score can resolve.
5. **Read the aggregation, not just the metric name.** "F1" and "weighted rubric average" each named two materially different computations inside one week.

This is the tooling-facing companion to [published-result reproducibility](published-result-reproducibility.md): that concept says a published claim is an unverified hypothesis until reproduced; this one says your own reproduction is itself a measurement whose instrument has a version. It reinforces, and does not alter, the routing in [evaluation protocol by size](../foundations/evaluation-protocol-by-size.md), which governs how to *split* data rather than how to score it.

# Open questions

- **No magnitude is established for any of the four.** Not one source re-scores a published number under the corrected code, so the size of the effect on any real leaderboard figure is unknown. The `f1()` and PaperBench entries state only that scores may move "in either direction."[^inspect-ai-changelog][^inspect-evals-paperbench] Treat the direction of each correction as known and the magnitude as unmeasured.
- The ranking-distortion argument for `f1()` (that it favours verbose models specifically) follows from the mechanism but is asserted by neither the changelog nor the source file. It needs a controlled re-run of one suite across the 0.3.270 boundary to become evidence.
- How widely `f1()` was used as a primary metric is unknown, so the blast radius of that correction cannot be estimated from these sources.
- The frequency of externally-issued cancellations in practice is unstated, so whether that defect ever materially moved a published agentic number is open. The commit for it also leaves a residual "pre-scoring cancellation window" unaddressed, per the 0.3.269 entry's surrounding context.
- All four findings come from two repositories in one organizational family (Inspect AI and Inspect Evals). That they surfaced together may reflect an unusually active audit in that ecosystem rather than a uniform rate of defects across eval tooling generally. **This concept's `modern-consensus` tier rests on four independent defects, not on four independent vendors** — a genuine limitation of the evidence, and the reason a reader should not conclude that other harnesses are cleaner.

[^inspect-ai-changelog]: Inspect AI `CHANGELOG.md` read at commit `d01e09c` (source id: inspect-ai-changelog). Release 0.3.270 (25 September 2026) carries the `f1()` multiset entry; 0.3.269 (25 September 2026) the foreign-cancellation entry; 0.3.253 (08 August 2026) the `exact()` word-order entry. Note a date inconsistency in the material behind this entry: the underlying `f1()` change is reported elsewhere as committed 2026-09-26, one day after the release date the changelog gives for 0.3.270. This concept cites the changelog's own dates and does not assert a commit date.
[^inspect-ai-f1-src]: Inspect AI `src/inspect_ai/scorer/_classification.py` (source id: inspect-ai-f1-src), read 2026-09-28 at branch `main`. `_to_word_counts()` returns `Counter[str]`; `_f1()` intersects multisets and divides by `sum(...values())`. Fetched at a branch ref rather than a commit SHA, so this file's content is the state on 2026-09-28 and may move.
[^inspect-evals-paperbench]: Inspect Evals `src/inspect_evals/paperbench/README.md` read at commit `dbd3dd2` (source id: inspect-evals-paperbench). The `graded_weight_fraction` definition, the residual-bias warning, the non-comparability statement, and the judge-model instruction are all stated there.
[^inspect-evals-bbh]: Inspect Evals `src/inspect_evals/bbh/README.md` read at commit `dbd3dd2` (source id: inspect-evals-bbh). The "Known dataset issues" section states the two excluded `ruin_names` rows, the 248-item run, and the retained `frank kappa` gold-label dispute; the task description states 27 tasks and 6,511 total published samples.
