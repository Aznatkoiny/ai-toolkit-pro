---
type: Decision Rule
title: "A serving-latency number is only comparable against its measurement window and control variable"
description: >
  TTFT and ITL distributions depend on whether the harness filters by request span or by event
  timestamp, and on whether load is driven by concurrency or by request rate. Both conventions
  changed in GuideLLM in September 2026, so token-latency figures are not comparable across that
  version boundary when warmup or cooldown was configured. Pin the harness version in every writeup.
tags: [eval-methodology, benchmarking, inference, serving, latency, ttft, goodput]
tier: frontier
applies_to:
  - comparing serving-latency numbers across runs, versions, or published posts
  - designing a benchmark to size an inference deployment
  - reading a vendor or project throughput/latency claim
status: draft
stale_after: 2026-12-21
generated:
  by: expedition/weekly-2026-09-21
  at: 2026-09-21T00:00:00Z
sources:
  - id: guidellm-metrics
    resource: https://github.com/vllm-project/guidellm/blob/3b261f581513ba060efa6e34786537386eba1ca8/docs/guides/metrics.md
    title: "guidellm docs/guides/metrics.md at commit 3b261f5 — request-level vs event-level windowing (documentation only)"
    author: GuideLLM contributors (vLLM project)
    last_modified: 2026-09-15
  - id: guidellm-1079
    resource: https://github.com/vllm-project/guidellm/commit/3b261f581513ba060efa6e34786537386eba1ca8
    title: "vllm-project/guidellm commit 3b261f5 (PR #1079) — commit message, test plan, and the code change itself"
    author: GuideLLM contributors (vLLM project)
    last_modified: 2026-09-15
  - id: guidellm-v074
    resource: https://github.com/vllm-project/guidellm/commit/291a6e609c3eb52d6eadcedecc7a056e396cd5eb
    title: "vllm-project/guidellm commit 291a6e6 — cherry-pick shipped as tag v0.7.4"
    author: GuideLLM contributors (vLLM project)
    last_modified: 2026-09-16
  - id: guidellm-goodput
    resource: https://github.com/vllm-project/guidellm/commit/ead221011c6bbb30df1942cf37870c091db10738
    title: "vllm-project/guidellm commit ead2210 — goodput profile: concurrency search under latency SLOs"
    author: GuideLLM contributors (vLLM project)
    last_modified: 2026-09-18
---

# Rule

**Record the benchmark harness and its version alongside every latency number you publish or cite.**
Concretely: **do not compare token-latency or token-throughput numbers across the GuideLLM
`v0.7.3`/`v0.7.4` boundary when `warmup` or `cooldown` was configured** — the windowing convention
changed there. Request-level numbers (request latency, requests/s, concurrency, per-request token
counts) are *unaffected* by that specific change. The general point is that a version bump can
silently redefine which events count, so pin the version rather than assume comparability.

**Request-span filtering and event-timestamp filtering give different TTFT distributions from the
same run.** GuideLLM changed which events fall inside the measurement window. Previously TTFT, TTFOT
and ITL were scoped by the whole request span — and per-token throughput rates were not clipped to
the window at all — so a request that began during warmup and was still running when the window
opened contributed its warmup-era first-token timing to the reported TTFT.[^guidellm-1079] The
documentation now draws the line explicitly — *"Request-level metrics: request totals, request
latency, concurrency, and per-request token counts, etc. will include any request whose lifetime
overlaps the measurement window… Event-level metrics: TTFT, time to first output token (TTFOT),
inter-token latency (ITL), and per-token throughput rates will include only events whose timestamps
fall inside the window. A request can therefore appear in request totals while some or all of its
token events are excluded."*[^guidellm-metrics] The change shipped in tag
`v0.7.4`.[^guidellm-v074] **Note `time_per_output_token_ms` (TPOT) was not changed and remains
request-span-scoped after the change** — this was not a blanket move of all token latencies to event
filtering.[^guidellm-1079]

**Consequence.** Any GuideLLM TTFT/TTFOT/ITL or per-token-throughput figure produced at or before
`v0.7.3` **with `warmup` or `cooldown` configured** mixes token events from outside the measurement
window into the reported distribution: the old filter admitted a request whenever its span
overlapped the window (`request_end >= measure_start and request_start <= measure_end`) and then
used all of that request's token timings.[^guidellm-1079] **`rampup_duration` alone does *not*
trigger this** — it staggers request start times but never moves `measure_start`, which is set only
by `warmup`.[^guidellm-1079] The change's own test plan — in the PR description, not in the
documentation — states the intended effect as convergence: *"when running a shorter concurrent run
with rampup+warmup vs a longer run with no rampup+warmup the results of the shorter run should be
closer than without this patch."*[^guidellm-1079] **Neither the documentation nor the PR description
quantifies the size or direction of the shift** — the doc says only that event-level filtering
*"keeps pre-warmup token timing from skewing latency and throughput figures"*, and the PR says only
that a short rampup+warmup run *"should be closer"* to a long run without one.[^guidellm-metrics][^guidellm-1079]
So an archived comparison cannot be corrected arithmetically; it has to be re-run.

**Drive load with concurrency, not request rate, or your measurement describes a backlog rather
than a server.** The rationale is stated directly: *"Concurrency is the control variable rather than
request rate. Every concurrency level settles into a steady state, whereas a rate above what the
server sustains grows an unbounded backlog and measurements taken there describe the backlog rather
than the server."*[^guidellm-goodput] **The argument is a queueing one rather than a GuideLLM one,
so it plausibly generalizes to any load generator — but the cited source argues it only for
GuideLLM's own profile, and this expedition checked no other harness.** A rate-driven benchmark run
above saturation reports queueing delay, and queueing delay grows with run length, so such a number
is not even self-consistent across durations.

**Report an attainment interval, not a point estimate, and treat a straddling interval as "run
longer" rather than as a result.** GuideLLM's new `goodput` profile searches for peak concurrency
under a latency SLO by doubling until attainment misses target and then bisecting, and attaches a
confidence interval to each probe: *"Each probe's attainment carries a Wilson score interval. When
that interval straddles the target the probe was too short to decide, and the search reports that
rather than a number that looks precise."*[^guidellm-goodput] Against the bundled mock server
configured with 16 concurrent slots, the knee was predicted analytically from the service-time
distribution and then searched for: `e2el_ms` 1200 predicted 19 / found 19, 1500 predicted 26 /
found 26, 2000 predicted 38 / found 38.[^guidellm-goodput] **That is a prediction-vs-recovery check
against a mock server, not a real serving result, and must not be quoted as one.**

**Relationship to existing concepts.** This is the measurement-side companion to
[speculative-decoding concurrency dependence](speculative-decoding-concurrency.md): that concept
establishes that the optimal setting moves with load, this one establishes that you cannot even
read the load-dependence correctly unless the window and control variable are pinned. Both feed
[published-result reproducibility](published-result-reproducibility.md) — a published serving
speedup missing its harness version and its concurrency is not an actionable claim.

# Open questions

- The event/request windowing rule may not be final. The merged code carries an unresolved `TODO` in
  `src/guidellm/benchmark/schemas/metrics.py` — *"Need to evaluate closed=False vs closed=True for
  first-token latencies. See github.com/vllm-project/guidellm/issues/1078"* — and the PR's own
  history is explicit that the choice was provisional: the commit that set it reads *"It is still
  debatable which approch is better, since we are on a bit of a time crunch to get this
  out."*[^guidellm-1079] The linked issue thread was not reachable in this expedition's network
  environment and has not been read.
- The pre-change behavior was verified in the `0.7.x` line at `v0.7.0`, `v0.7.2` and `v0.7.3`, where
  the filtering code is identical. **Earlier lines were not checked**, so "at or before `v0.7.3`"
  should not be read as a claim about `0.6.x` and older.
- The `goodput` profile is on `main` only and is **not** in `v0.7.4`.[^guidellm-goodput] Per
  [release-containment discipline](release-containment-discipline.md), do not plan around it as a
  released feature.
- Both the windowing fix and the goodput profile are single-project artifacts from the vLLM
  organization, and GuideLLM is the harness used in vLLM's own performance posts. No independent
  party has assessed either convention. Tier is `frontier` accordingly.
- The general claim — that *other* harnesses (`vllm bench serve`, `llmperf`, `locust`-based rigs)
  filter by request span and are therefore subject to the same warmup contamination — is
  **plausible but unverified**; this expedition checked only GuideLLM. Do not cite this concept as
  evidence about a harness it does not name.

[^guidellm-metrics]: guidellm `docs/guides/metrics.md` at commit 3b261f5 (source id: guidellm-metrics), 2026-09-15. The request-level/event-level definitions and the "keeps pre-warmup token timing from skewing latency and throughput figures" phrasing are in the "Measurement Window, Warmup, and Cooldown" section, added by that commit. The elision in the quoted passage spans a bullet-list boundary and the clause ", even when the request started during warmup or finished during cooldown".
[^guidellm-1079]: vllm-project/guidellm commit 3b261f5 / PR #1079 (source id: guidellm-1079), 2026-09-15. **The test-plan convergence statement is in the commit message, not in any file in the tree**; the `closed=False vs closed=True` TODO and the "still debatable … time crunch" phrasing are a code comment and a squashed-history commit message respectively. The pre-change filter (`get_within_range` in `src/guidellm/benchmark/schemas/accumulator.py`, request-span overlap) and the fact that `measure_start` is set only from `config.warmup.compute_transition_time(...)` — never from `rampup_duration`, which only staggers request start times — were read from the tree at tags `v0.7.0`, `v0.7.2` and `v0.7.3` during the skeptic pass on 2026-09-21. `time_per_output_token_ms` was confirmed unchanged at `v0.7.4`.
[^guidellm-v074]: vllm-project/guidellm commit 291a6e6 (source id: guidellm-v074), tag `v0.7.4`, 2026-09-16. Tag existence and SHA confirmed by `git ls-remote --tags` on 2026-09-21 (`v0.7.3` → `39383552`, `v0.7.4` → `291a6e60`); 291a6e6 is a cherry-pick of PR #1079 carrying the same five-file change.
[^guidellm-goodput]: vllm-project/guidellm commit ead2210 (source id: guidellm-goodput), 2026-09-18. The concurrency-as-control-variable rationale, the Wilson-interval behavior, and the mock-server figures are stated in that commit. Confirmed on `main` and not contained in `v0.7.4` by `git merge-base --is-ancestor` during the skeptic pass, 2026-09-21.
