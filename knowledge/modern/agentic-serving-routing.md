---
type: Decision Rule
title: "Route agentic sessions by affinity, not by load — and distrust parallelism gains that were measured on a different workload shape"
description: >
  Multi-turn agentic traffic is dominated by prefix-cache hits on a warm GPU, which inverts several
  defaults carried over from single-turn serving: session-sticky routing beats queue-depth and
  KV-utilization load balancing, pipeline parallelism stops paying for warm turns, and decode context
  parallelism does not transfer across model architectures. Design to the measured workload shape.
tags: [inference, serving, agents, routing, prefix-cache, pipeline-parallelism, context-parallelism]
tier: frontier
applies_to:
  - designing a gateway or router in front of an LLM serving fleet that carries multi-turn agent traffic
  - choosing a parallelism strategy (PP, DCP) for an agentic or long-context deployment
  - capacity planning for agentic workloads
  - reading a serving-throughput or serving-cost claim
status: draft
stale_after: 2026-12-14
generated:
  by: expedition/weekly-2026-09-14
  at: 2026-09-14T00:00:00Z
sources:
  - id: vllm-agentx
    resource: https://github.com/vllm-project/vllm-project.github.io/blob/d2fe8cfa8294b8568b3d86c106e4a8c982d33701/_posts/2026-09-08-vllm-agentx.md
    title: "vLLM x AgentX: Optimizing for Real-World Agentic Serving (source of blog.vllm.ai)"
    author: vLLM Team and Inferact, with NVIDIA and AMD support
    last_modified: 2026-09-08
  - id: vllm-55780
    resource: https://github.com/vllm-project/vllm/pull/55780
    title: "vllm-project/vllm PR #55780 — attention backends must opt in to decode context parallelism (commit db3814a4f215e666098ffb74a5c21bf46c60bae9)"
    author: vLLM contributors
    last_modified: 2026-09-08
---

# Rule

**Agentic traffic is not single-turn traffic with more requests, and the defaults do not carry
over.** The workload shape reported from the AgentX benchmark traces is: a median of 43 turns per
session, a median input of 142K tokens against a median output of 444 tokens, a prefix-cache hit rate
above 96%, and 44% of sessions spawning subagents.[^vllm-agentx] **A warm turn adds only hundreds of
fresh tokens to an already-cached prefix** — that single fact is what inverts the rules below.

**Prefer session affinity over load balancing.** In aggregated data-and-expert-parallel deployments,
queue-depth, running-token and KV-utilization routing policies were all reported to underperform
simple session-sticky routing: moving a session off its warm GPU forces a KV retrieval which, though
asynchronous and overlapped with computation, is not free — its prefetched blocks occupy KV capacity
at the destination and reduce the number of sequences that rank can admit.[^vllm-agentx] The result is
a more balanced queue that processes fewer concurrent requests overall.[^vllm-agentx] **The
load-balancing win is real but it is smaller than the cache-locality loss it causes**, whenever the
inter-turn delay is short enough that the prefix is still resident. This is the opposite of the
standard stateless-service default.

**Do not make pipeline parallelism the default for warm agentic turns.** Pipeline parallelism performs
well on long, fresh prompts, but because a warm turn contributes only a few hundred to a few thousand
fresh tokens there is not enough fresh computation to fill the pipeline and bubbles consume much of
the gain; the reported guidance is to keep it for cold, compute-heavy prefills rather than applying it
uniformly.[^vllm-agentx] The post scopes chunked pipeline parallelism into the same finding rather
than treating it as a remedy.[^vllm-agentx]

**Do not budget decode-context-parallelism gains by analogy from another model family.** After
substantial communication/compute overlap work, decode context parallelism (DCP) only *matched* data
and expert parallelism (DEP) on DeepSeek V4 — a result that did not transfer from the pure-MLA models
where DCP works well (DeepSeek R1, Kimi K2.5, K2.7), nor from the hybrid-MLA Kimi K3.[^vllm-agentx]
The stated reason is that compressed sparse attention puts an indexer, a compressor and the main
attention all in need of partitioning and coordination.[^vllm-agentx] **Architecture, not just scale,
decides whether DCP pays.** Corroboration that DCP is not a universally applicable lever landed the
same week in the engine itself — a vLLM pull request from an AMD contributor, so adjacent to rather
than independent of the post's authorship: `AttentionImplBase.supports_dcp` was flipped from
defaulting `True` to defaulting `False`, requiring each attention backend to opt in explicitly, with
eleven in-tree backends doing so and anything outside that list — including out-of-tree and custom
backends — now failing closed at startup rather than running an untested path.[^vllm-55780]

**Capacity-plan against total tokens, but read the metric's definition first.** The post's own headline
is up to 130K total tokens per GPU-second; **the figure worth carrying is the SLO-filtered one** — 83K
total tokens per GPU-second on DeepSeek V4 Pro at P90 interactivity above 50 tokens/s/user, measured on
12× GB300 at concurrency 256.[^vllm-agentx] **That metric counts input, output *and cached* tokens**,
which the post states explicitly.[^vllm-agentx] It follows — this is the concept's inference, not a
claim the post makes — that with a cache hit rate above 96% most of what is counted was never
recomputed, so the number is not comparable to an output-token throughput figure and the two should
never be placed side by side.

**The largest quantified lever in this source is scheduling, not routing.** Setting
`--long-prefill-token-threshold` to 512 tokens is reported to raise total tokens per GPU-second by up
to 93% and improve P90 interactivity by roughly 2.3× on DeepSeek V4 Pro on B300s, with a stated
time-to-first-token trade-off; `--prefill-schedule-interval` is offered for aligning cadence in
data-and-expert-parallel deployments.[^vllm-agentx] **Head-of-line blocking by long prefills is
therefore worth checking before any topology change**, since it is a one-flag experiment.

# Open questions

- **The cost comparison in this source is marketing and must not be repeated as a finding.** The
  reported 14.6×–106× advantage compares GPU total-cost-of-ownership per hour against Opus 5 retail
  API list pricing — infrastructure cost against a priced product that includes margin, serving
  operations, and a different model. The post itself concedes "The comparison is about serving cost,
  not model quality."[^vllm-agentx] **Do not cite a cost multiple from this concept.**
- The post is vendor-authored (vLLM Team and Inferact, work led by Inferact, with NVIDIA and AMD
  support). Its mitigation is that the benchmark, dataset, harness and dashboard are third-party —
  SemiAnalysis AgentX, with public traces, a public harness, and per-row links to the hosted runs.
  **But this is a reproducible harness, not third-party execution:** the configurations benchmarked
  are the authors' own and self-tuned, and reported best-config-per-model. The same SemiAnalysis
  infrastructure also underpins the MiniMax M3 post cited by
  [performance attribution discipline](performance-attribution-discipline.md), so those two concepts
  rest partly on one third party.[^vllm-agentx]
- Results are best-config-per-model, filtered to P90 interactivity above 50 tokens/s/user. A
  best-config-per-model presentation is not a like-for-like comparison across models: DeepSeek V4 Pro
  runs 12× GB300 at concurrency 256, MiniMax M3 runs 2× B300 at concurrency 24, Kimi K3 runs 16× GB300
  at concurrency 48.[^vllm-agentx]
- The workload shape (43 turns, 142K median input, >96% hit rate) comes from one benchmark's traces.
  How well it represents any particular production agent deployment is unestablished, and the routing
  conclusion depends on it: **a workload with long inter-turn gaps, or one where the prefix is evicted
  between turns, may not reproduce the session-affinity result at all.** This is the main reason the
  tier is `frontier` and the `stale_after` is short.
- No source here quantifies the tail-latency or fairness cost of session-sticky routing, which is the
  standard argument *for* load balancing. The finding as stated optimizes throughput; a deployment with
  a strict per-session latency SLO under skewed load may reach a different answer.

# Relation to existing concepts

**Scope note.** The stable [scope boundary](../foundations/scope-boundary.md) still records inference
deployment beyond speculative decoding as uncovered, and this concept is inference deployment at fleet
scale — routing, topology, and capacity planning. It opens that area at `frontier` and at
`Evidence: unverified` only; the boundary's draft-coverage section is updated on landing to record the
carve-out, and the stable boundary continues to govern anything this draft does not cover.

This concept extends the inference-serving coverage opened by
[speculative-decoding concurrency](speculative-decoding-concurrency.md), which established that a
serving parameter tuned at one concurrency is untuned at another. The rule here is the architectural
counterpart: a *topology* choice (PP, DCP) and a *routing* choice validated on one workload shape do
not transfer to another. Both are instances of the caution in
[published-result reproducibility](published-result-reproducibility.md).

[^vllm-agentx]: vLLM blog, "vLLM x AgentX: Optimizing for Real-World Agentic Serving" (source id: vllm-agentx), read at repo commit `d2fe8cf`, post dated 2026-09-08 (verified from the `_posts/` filename, the frontmatter `date: 2026-09-08 23:00:00 +0000`, and `git log` on the file: added in `f82aa01` on 2026-09-08 and touched once more the same day by `091b4c5`, "set publish time and escape dollar signs"; `d2fe8cf` is a later repository snapshot at which the file is byte-identical, used here as a stable blob pin). The workload-shape statistics, the three "bitter lessons" (pipeline parallelism including its chunked form on warm turns, decode context parallelism not transferring, load-balancing policies losing to session-sticky routing together with the KV-retrieval mechanism behind it and its "asynchronous and overlaps with computation, but it is not free" qualifier), the model lists (DCP working well on pure-MLA DeepSeek R1 / Kimi K2.5 / Kimi K2.7 and on hybrid-MLA Kimi K3), the `--long-prefill-token-threshold` result (up to 93% total tokens per GPU-second, roughly 2.3× P90 interactivity, at 512 tokens on DeepSeek V4 Pro / B300s), the 83K tokens/GPU-second figure with its 12× GB300 / concurrency 256 / P90 > 50 tok/s conditions, the footnoted statement that "Total tokens per GPU-second (TPGS) counts input, output, and cached tokens", and the serving-cost disclaimer are all stated in the post. Note that the post's own TL;DR and `summary` frontmatter lead with 130K TPGS rather than the SLO-filtered 83K; this concept deliberately carries the more conservative figure. "DEP" is the post's abbreviation for data and expert parallelism, not decode expert parallelism. Benchmark is SemiAnalysis AgentX (public traces, harness at `SemiAnalysisAI/agentx-harness`); figures are tabulated rather than read off a chart.
[^vllm-55780]: vllm-project/vllm PR #55780 (source id: vllm-55780), commit `db3814a`, dated 2026-09-08 from `git log`. The `supports_dcp` default flip from `True` to `False` and the eleven in-tree backends opting in were confirmed in the diff (`vllm/v1/attention/backend.py`; the ROCm test now asserts `pytest.raises(ValueError, match="DCP not supported")`). The gate is on the attention implementation, not the model, and it fails closed at startup. This commit is not contained in tag `v0.29.0` and is reachable only from `v0.29.1rc0`. Cited here only as corroboration that DCP applicability is backend-specific — it does not speak to the AgentX measurements.
