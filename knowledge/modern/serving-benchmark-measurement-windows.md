---
type: Decision Rule
title: "A serving-latency number is only comparable against its measurement window and control variable"
description: >
  TTFT and ITL distributions depend on whether the harness filters by request span or by event
  timestamp, and on whether load is driven by concurrency or by request rate. Both conventions
  changed in GuideLLM in September 2026, so latency figures are not comparable across harness
  versions or across load-driving methods. Pin the harness version in every benchmark writeup.
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
    title: "guidellm docs/guides/metrics.md at commit 3b261f5 — request-level vs event-level windowing"
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

**Record the benchmark harness and its version alongside every latency number you publish or cite,
and refuse to compare two numbers produced by different versions of it.** A latency distribution is
not a property of the server alone; it is a property of the server *and* the harness's rule for
deciding which events count.

**Request-span filtering and event-timestamp filtering give different TTFT distributions from the
same run.** GuideLLM changed which events fall inside the measurement window: previously TTFT,
TTFOT, ITL and per-token throughput were scoped by the whole request span, so a request that began
during warmup but finished inside the window contributed its warmup-era first-token timing to the
reported TTFT. The documentation now draws the line explicitly — *"Request-level metrics: request
totals, request latency, concurrency, and per-request token counts, etc. will include any request
whose lifetime overlaps the measurement window… Event-level metrics: TTFT, time to first output
token (TTFOT), inter-token latency (ITL), and per-token throughput rates will include only events
whose timestamps fall inside the window. A request can therefore appear in request totals while some
or all of its token events are excluded."*[^guidellm-metrics] The change shipped in tag
`v0.7.4`.[^guidellm-v074] **Consequence: any GuideLLM TTFT/ITL figure produced at or before
`v0.7.3` with warmup or rampup configured mixes pre-steady-state token events into the reported
distribution, and the shorter the measurement run relative to warmup, the larger the contamination.**
The change's own test plan states the intended effect as convergence — *"when running a shorter
concurrent run with rampup+warmup vs a longer run with no rampup+warmup the results of the shorter
run should be closer than without this patch."*[^guidellm-metrics] **Neither source quantifies the
size or direction of the shift**, so an archived comparison cannot be corrected arithmetically; it
has to be re-run.

**Drive load with concurrency, not request rate, or your measurement describes a backlog rather
than a server.** The rationale is stated directly: *"Concurrency is the control variable rather than
request rate. Every concurrency level settles into a steady state, whereas a rate above what the
server sustains grows an unbounded backlog and measurements taken there describe the backlog rather
than the server."*[^guidellm-goodput] **This is the methodological core and it is harness-independent
— it applies to any load generator you use.** A rate-driven benchmark run above saturation reports
queueing delay, and queueing delay grows with run length, so such a number is not even
self-consistent across durations.

**Report an attainment interval, not a point estimate, and treat a straddling interval as "run
longer" rather than as a result.** GuideLLM's new `goodput` profile searches for peak concurrency
under a latency SLO by doubling until attainment misses target and then bisecting, and attaches a
confidence interval to each probe: *"Each probe's attainment carries a Wilson score interval. When
that interval straddles the target the probe was too short to decide, and the search reports that
rather than a number that looks precise."*[^guidellm-goodput] Validated against a mock server with
16 slots, the search recovered 19/19, 26/26 and 38/38 for `e2el_ms` targets of 1200, 1500 and 2000
respectively.[^guidellm-goodput] **Those are mock-server self-consistency checks, not a real
serving result, and must not be quoted as one.**

**Relationship to existing concepts.** This is the measurement-side companion to
[speculative-decoding concurrency dependence](speculative-decoding-concurrency.md): that concept
establishes that the optimal setting moves with load, this one establishes that you cannot even
read the load-dependence correctly unless the window and control variable are pinned. Both feed
[published-result reproducibility](published-result-reproducibility.md) — a published serving
speedup missing its harness version and its concurrency is not an actionable claim.

# Open questions

- The event/request windowing rule may not be final. The merged code carries an unresolved
  `TODO` — *"Need to evaluate closed=False vs closed=True for first-token latencies. See
  github.com/vllm-project/guidellm/issues/1078"* — so the TTFT boundary convention could change
  again.[^guidellm-metrics] The linked issue thread was not reachable in this expedition's network
  environment and has not been read.
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

[^guidellm-metrics]: guidellm `docs/guides/metrics.md` at commit 3b261f5 (source id: guidellm-metrics), 2026-09-15. The request-level/event-level definitions, the test-plan convergence statement, and the `closed=False vs closed=True` TODO are all at that SHA.
[^guidellm-v074]: vllm-project/guidellm commit 291a6e6 (source id: guidellm-v074), tag `v0.7.4`, 2026-09-16. Tag existence and SHA confirmed by `git ls-remote --tags` on 2026-09-21 (`v0.7.3` → `39383552`, `v0.7.4` → `291a6e60`).
[^guidellm-goodput]: vllm-project/guidellm commit ead2210 (source id: guidellm-goodput), 2026-09-18. The concurrency-as-control-variable rationale, the Wilson-interval behavior, and the 19/26/38 mock-server validation figures are stated in that commit. It is on `main` and not contained in `v0.7.4`.
