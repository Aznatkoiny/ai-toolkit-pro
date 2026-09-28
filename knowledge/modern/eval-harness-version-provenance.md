---
type: Decision Rule
title: "A benchmark score is a property of the harness version, not only of the model"
description: >
  In a single week, three scoring defects were corrected in mainstream open eval tooling and one
  upstream dataset defect was documented: a text-F1 scorer that ignored token multiplicity, an
  aggregation that charged judge failures to the model under test, samples cancelled from outside
  being scored as completed successes, and two benchmark rows unanswerable by construction. Record
  the harness version, config and judge model beside every score; a score without them is not
  comparable to anything, including your own earlier runs.
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
    last_modified: 2026-09-26
  - id: inspect-ai-f1-src
    resource: https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_ai/main/src/inspect_ai/scorer/_classification.py
    title: "Inspect AI f1() scorer implementation (multiset token counting)"
    author: Inspect AI maintainers
    last_modified: 2026-09-25
  - id: inspect-ai-f1-commit
    resource: https://github.com/UKGovernmentBEIS/inspect_ai/commit/20e12b059a25ea13fefc034dd81f93c69a50a37f
    title: "Inspect AI commit 20e12b0 — Fix f1() ignoring repeated tokens when scoring (#5519)"
    author: Yufeng He, with Charles Teague (Inspect AI)
    last_modified: 2026-09-25
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

**Treat an eval score as a measurement made by a specific version of a specific harness under a specific config, and record all three beside the number. A score carried without its harness version is not comparable to a published number, to another model, or to your own run from last month.** The week of 2026-09-21 supplies four independent demonstrations, each with an exact version boundary.

**A scorer can reward the failure mode you are trying to measure.** Inspect AI's `f1()` normalized both answer and target into a Python `set`, discarding token multiplicity, so a padded or repetitive answer paid no precision cost. The fix's commit message gives the illustration: "f1() normalized answers into set[str], discarding token multiplicity, so an answer repeating the target word scored a perfect 1.0 (\"Paris Paris Paris Paris Paris\" vs \"Paris\"). SQuAD F1 is a bag-of-tokens measure, so count with Counter and intersect multisets. Order-insensitivity stays; the change only moves duplicate-token shapes."[^inspect-ai-f1-commit] Release 0.3.270 ships that change, and the released implementation derives precision and recall from `sum(...values())` over `Counter` intersections rather than from `len()`.[^inspect-ai-f1-src] The changelog states the consequence: "scores can rise or fall for answers or targets containing repeated words."[^inspect-ai-changelog] **Note precisely what was wrong: multiplicity, not order.** Order-insensitivity is correct for F1 and was deliberately retained. **The hazard is that the inflation is model-dependent** — it accrues to verbose, repetition-prone outputs, so it can distort a *ranking* between two models and not merely shift a level. That ranking consequence follows from the mechanism; it is an inference, not a claim any source makes.

**This is a recurring class in the same tool, and the maintainers say so.** The commit describes itself as "the half of #4618 that #4619 did not cover."[^inspect-ai-f1-commit] The sibling half had landed in 0.3.253 (08 August 2026), where `exact()` had "compared unordered word sets, so e.g. \"world hello\" scored as an exact match for \"hello world\"", with the warning that `exact()` scores "may decrease on existing evals where answers matched only via word reordering or duplicate collapse."[^inspect-ai-changelog] **That entry then advised users to "use `f1()` for order-insensitive scoring"**[^inspect-ai-changelog] — pointing them at the scorer whose own multiplicity bug survived another seventeen releases. **Do not assume the string-matching layer of a harness is settled, and do not assume a migration note points somewhere safe.**

**Judge failures can be charged to the model under test.** In Inspect Evals' PaperBench, a rubric criterion the judge could not grade scored `0.0` — indistinguishable from a criterion the reproduction genuinely failed. Ungraded criteria are now dropped from both sides of the weighted average, and a new `graded_weight_fraction` metric reports "the share of the rubric weight those criteria represent," which "is 1.0 when every criterion was graded."[^inspect-evals-paperbench] **Read the new metric, because the fix carries its own bias in the opposite direction**, as the README states: "Leaving ungraded criteria out of the divisor raises the reported score if the judge fails more often on criteria the reproduction did not meet. Read `graded_weight_fraction` alongside `score` for this reason."[^inspect-evals-paperbench] The aggregation also now differs from the reference implementation, which "averages over every child, including those whose grading failed," so "scores produced by this implementation are therefore not directly comparable with published PaperBench numbers when the judge fails to grade any criterion."[^inspect-evals-paperbench] **This is one comparability gap among several, not the origin of them:** the same README separately lists solver and tooling deviations that already "limit how directly a run here compares with the paper."[^inspect-evals-paperbench] The lesson is cumulative — each documented deviation is another reason a cross-implementation number needs its provenance.

**Name the judge model, always.** The README instructs that "to compare results across different solver models, use the same judge model for scoring," that the original paper used `openai/o3-mini-2025-01-31`, and that "a run should record the judge model used."[^inspect-evals-paperbench] A judged benchmark number quoted without its judge is not a measurement of the model.

**Infrastructure failures can be scored as model outcomes.** Release 0.3.269 records that "samples whose solver is cut off by a cancellation that inspect did not issue are now recorded as sample errors instead of being scored as completed."[^inspect-ai-changelog] Before that boundary, an externally killed sample entered scoring as a completed run. **The direction of the resulting bias depends on how often foreign cancellations occurred in your environment, which no source here quantifies** — plausibly negligible for short tasks and material for long-horizon agentic runs where cancellations are more common, but that contrast is an inference and is not established.

**Some benchmark rows cannot be answered at all, and some published gold labels are known to be wrong and kept anyway.** BIG-Bench Hard's `ruin_names` rows 100 and 145 have "their options split on the commas inside the candidate names, so the lettered options are fragments and the target is a full name that is not among them"; they "cannot be scored by option letter and are excluded," leaving `ruin_names` to run 248 items, and the defect is present in the mirror the port loads.[^inspect-evals-bbh] **Note that this one is an upstream dataset defect, not a harness scoring bug** — it is reported against the source dataset, and the harness's contribution was to document and exclude the rows. Separately, row 41 (`'frank kappa'`) "has the unchanged input as its gold answer, which contradicts the task definition," and the README states simply that the row "is kept as published"; **it gives no rationale, so any reason you might supply for retaining it is your inference, not the maintainers'.**[^inspect-evals-bbh] **That second item is the more useful one: a known-wrong label knowingly retained.** On the suite's size, the README describes 27 tasks, "most containing 250 samples," totalling 6,511 published samples;[^inspect-evals-bbh] subtracting the two excluded rows gives 6,509 loaded, which is this concept's arithmetic rather than a figure the README states.

**Quantify the defect floor rather than guessing at it.** Three documented bad or unusable rows out of 6,511 is roughly 0.05% of the suite — a real floor, but a small one, and materially tighter at subtask level, where one retained bad label in `ruin_names` is about 0.4% of that subtask. **The discipline is to compute this floor for the suite you actually run**, then decline to read differences beneath it. A previous revision of this concept inferred from these same rows that sub-percentage-point BBH differences are noise; that does not follow from three rows in 6,511 and has been withdrawn.

**What to do**

1. **Pin the harness.** Record the exact harness version alongside every score you keep, and pin it in the environment that produces release-gating numbers. A harness upgrade is a re-baseline event.
2. **Record the config that decides the number:** judge model, subset, metric variant, and dataset revision.
3. **Never compare across a version boundary without re-running the baseline.** Three of these changes move scores, two in a direction the sources decline to predict.
4. **Compute the suite's own defect floor** from its documented excluded and known-bad rows, and treat differences below it as unresolvable.
5. **Read the aggregation, not just the metric name.** "F1" and "weighted rubric average" each named two materially different computations inside one week.

This is the tooling-facing companion to [published-result reproducibility](published-result-reproducibility.md): that concept says a published claim is an unverified hypothesis until reproduced; this one says your own reproduction is itself a measurement whose instrument has a version. It reinforces, and does not alter, the routing in [evaluation protocol by size](../foundations/evaluation-protocol-by-size.md), which governs how to *split* data rather than how to score it. A score that is not bitwise stable under batch composition has a further noise floor that no harness bookkeeping reveals — see [determinism is a pipeline contract](determinism-is-a-pipeline-contract.md).

# Open questions

- **No magnitude is established for any of these corrections.** No source re-scores a published number under the corrected code, so the size of the effect on any real leaderboard figure is unknown. The `f1()` and PaperBench entries state only that scores may move in either direction.[^inspect-ai-changelog][^inspect-evals-paperbench] Treat each correction's direction as known and its magnitude as unmeasured.
- The ranking-distortion argument for `f1()` (that it favours verbose models specifically) follows from the mechanism but is asserted by no source. It needs a controlled re-run of one suite across the 0.3.270 boundary to become evidence.
- How widely `f1()` was used as a primary metric is unknown, so the blast radius of that correction cannot be estimated.
- The frequency of externally-issued cancellations in practice is unstated, so whether that defect ever materially moved a published agentic number is open.
- No PaperBench results have been published from this implementation, so the practical size of the aggregation change is not yet observable from the source.
- All four findings come from two repositories in one organizational family (Inspect AI and Inspect Evals). **This concept's `modern-consensus` tier rests on four independent defects, not on four independent vendors** — a genuine limitation, and the reason a reader should not conclude that other harnesses are cleaner. That these surfaced together may reflect an unusually active audit in that ecosystem rather than a uniform defect rate across eval tooling.

[^inspect-ai-changelog]: Inspect AI `CHANGELOG.md` read at commit `d01e09c` (source id: inspect-ai-changelog). Release 0.3.270 (25 September 2026) carries the `f1()` multiset entry; 0.3.269 (25 September 2026) the foreign-cancellation entry; 0.3.253 (08 August 2026) the `exact()` word-order entry and its "use `f1()` for order-insensitive scoring" advice. The file at this commit also contains a 0.3.271 entry dated 26 September, hence the `last_modified` above.
[^inspect-ai-f1-src]: Inspect AI `src/inspect_ai/scorer/_classification.py` (source id: inspect-ai-f1-src), read 2026-09-28 at branch `main`. `_to_word_counts()` returns `Counter[str]`; `_f1()` intersects multisets and divides by `sum(...values())`. Fetched at a branch ref rather than a commit SHA, so this reflects the state on 2026-09-28 and may move. The pre-fix `set[str]` behaviour is documented by the commit below, not by this snapshot.
[^inspect-ai-f1-commit]: Inspect AI commit `20e12b0` (source id: inspect-ai-f1-commit), authored 2026-09-25T16:50Z. Read in this environment via `git fetch --depth 1 --filter=blob:none origin <sha>` followed by `git log -1`, because `github.com` commit pages and `api.github.com` are refused for this session while anonymous git reads are served — so the URL above is the canonical citation rather than the fetch path used. The quoted message body and the "half of #4618 that #4619 did not cover" self-description are from that commit.
[^inspect-evals-paperbench]: Inspect Evals `src/inspect_evals/paperbench/README.md` read at commit `dbd3dd2` (source id: inspect-evals-paperbench). The `graded_weight_fraction` definition, the residual-bias warning, the reference-implementation divergence, the pre-existing solver and tooling deviations, and the judge-model instruction are all stated there.
[^inspect-evals-bbh]: Inspect Evals `src/inspect_evals/bbh/README.md` read at commit `dbd3dd2` (source id: inspect-evals-bbh). The "Known dataset issues" section states the two excluded `ruin_names` rows, the 248-item run, the upstream report, and the retained `frank kappa` gold-label dispute with no rationale; the task description states 27 tasks and 6,511 total published samples, which reconciles as 24×250 + 178 + 146 + 187.
