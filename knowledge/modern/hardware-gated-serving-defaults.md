---
type: Decision Rule
title: "Inference-server defaults are hardware-gated, and they flip on upgrade"
description: >
  A serving engine's "default" is not one value: it is selected at startup from the device's memory
  size and compute capability, so one version behaves differently across a mixed fleet and a
  benchmark from one GPU class does not transfer to another. Upgrades change these gates silently,
  with no flag change on your side, and the gates themselves are often set from a single-configuration
  measurement. Pin every default you benchmarked against, and re-measure after an upgrade rather
  than reading the version number.
tags: [inference, serving, deployment, vllm, sglang, upgrades, configuration, reproducibility]
tier: modern-consensus
applies_to:
  - upgrading vLLM or SGLang in a deployment whose capacity model was calibrated on the old version
  - running one serving image across a fleet of mixed GPU classes
  - reading or reproducing an inference throughput/latency benchmark
  - scheduling a migration off a deprecated serving flag
status: draft
stale_after: 2027-02-28
generated:
  by: expedition/weekly-2026-08-31
  at: 2026-08-31T00:00:00Z
sources:
  - id: vllm-batch-defaults
    resource: https://github.com/vllm-project/vllm/commit/4988df2eb80a8d1debae7de85c3b242fa436f3c1
    title: "vllm commit 4988df2e — [Config] Update default _max_num_batched_tokens from 8192 to 16384 (#51726)"
    author: vLLM contributors
    last_modified: 2026-08-11
  - id: vllm-cudagraph-blackwell
    resource: https://github.com/vllm-project/vllm/commit/021b7d985b54264393b4c339f2823d783080942a
    title: "vllm commit 021b7d98 — [Perf] Raise Blackwell CUDA graph capture default to 1024 (#49390)"
    author: vLLM contributors
    last_modified: 2026-08-07
  - id: vllm-cudagraph-pr
    resource: https://github.com/vllm-project/vllm/pull/49390
    title: "vllm PR #49390 description — benchmark for the Blackwell CUDA graph capture default"
    author: vLLM contributors
    last_modified: 2026-08-07
  - id: vllm-mamba-prefix
    resource: https://github.com/vllm-project/vllm/commit/f9c74b4b9c25c202cb84e0e9908b82a503a8c7c4
    title: "vllm commit f9c74b4b — [Mamba] enable prefix cache by default (#50991)"
    author: vLLM contributors
    last_modified: 2026-08-04
  - id: vllm-kv-scales-removal
    resource: https://github.com/vllm-project/vllm/commit/dd11df04f3b7046c40f13e586ac38a3725bc3c03
    title: "vllm commit dd11df04 — removal of calculate_kv_scales (#49389)"
    author: vLLM contributors
    last_modified: 2026-08-03
  - id: sglang-environ-0518
    resource: https://github.com/sgl-project/sglang/blob/v0.5.18/python/sglang/srt/environ.py
    title: "sglang python/sglang/srt/environ.py at tag v0.5.18"
    author: SGLang contributors
    last_modified: 2026-08-20
---

# Rule

**A serving engine's default is a function of the device, not of the version. Never carry a
measured configuration across GPU classes, and never assume two nodes running the same image are
running the same configuration.** In vLLM v0.28.0 the batch defaults are chosen by a three-way
branch: at or above 160 GiB of device memory, `max_num_batched_tokens` is 16384 for both the offline
and the API-server path; at or above 70 GiB *and* with `"a100"` absent from the device name, the
API-server path gets 8192; everything else gets 2048, and only in that last tier does `max_num_seqs`
drop, from 1024 to 256.[^vllm-batch-defaults] The same release picks the CUDA-graph capture ceiling
from compute capability rather than memory — `1024 if current_platform.is_device_capability_family(100)
else 512` — where v0.27.1 hardcoded 512.[^vllm-cudagraph-blackwell] **So a single vLLM version has at
least three distinct default configurations, and a throughput number measured on an H100 is not a
prediction for a B200 even with an identical command line.**

**On upgrade these gates move, and nothing in your configuration changes to tell you.** The
≥160 GiB tier did not exist at v0.27.1; the file at that tag contains no such branch, so the
API-server default for a B200-class device was the 70 GiB tier's 8192.[^vllm-batch-defaults] A
deployment that pinned nothing therefore doubles its prefill chunk budget on exactly that hardware
by upgrading. Note precisely what does *not* change: `max_num_seqs` is 1024 in both the new
≥160 GiB tier and the pre-existing ≥70 GiB tier, so on B200/B300 only `max_num_batched_tokens`
moves.[^vllm-batch-defaults] The two gates nonetheless compound: with `max_num_seqs` at 1024,
`max_num_seqs * decode_query_len * 2` exceeds 1024, so on an SM100 device the `min()` resolves to
the raised 1024 ceiling rather than 512.[^vllm-cudagraph-blackwell] The source measures what that
costs — *"Capturing up to 1024 took 80 seconds and 4.88 GiB per GPU in this
configuration"*[^vllm-cudagraph-pr] — so budget startup time and memory accordingly, or set
`max_cudagraph_capture_size` explicitly. **The compounding does not occur in the fallback tier**,
where `max_num_seqs` is 256 and `min(256 * 1 * 2, 512)` is still 512.[^vllm-batch-defaults]

**A default can be set from a single measured configuration and still apply globally.** The
capture-ceiling raise is defended by a benchmark, but one run on one GPU and one model: NVIDIA B300
SXM6 AC, a *"DeepSeek-V4-Flash DSpark workload with fixed verification (7 draft tokens)"*, reporting
1,127 → 7,559 output tok/s at concurrency 64, 904 → 5,101 at 128, and 977 → 4,812 at 256 for capture
size 512 → 1024.[^vllm-cudagraph-pr] The same description states *"B200 validation is still pending,
which is why this PR is being opened as a draft"* — and the change nevertheless shipped as the
default for the entire SM100 family.[^vllm-cudagraph-pr] **Treat a default as a hypothesis carrying
the hardware and workload it was measured on, and check whether that is yours.**

**The pattern is not one project's.** SGLang v0.5.18 flips four `EnvBool` defaults from `False` to
`True`: `SGLANG_AUTO_NUMA_BIND`, `SGLANG_ENABLE_MOE_DEFERRED_FINALIZE`, `SGLANG_OPT_FUSE_MHC_POST_PRE`
and `SGLANG_OPT_UNIFIED_CACHE_FREE_OUT_OF_WINDOW_SLOTS`.[^sglang-environ-0518] The surrounding churn
is larger still — 26 `EnvBool` names disappear and 25 appear between v0.5.17 and
v0.5.18.[^sglang-environ-0518] **Before attributing a post-upgrade throughput or memory change to
your own code, set the flipped defaults back and re-measure.** That is the cheap bisect, and it
requires knowing the whole set: resetting two of the four is not a bisect, it is a different
configuration.

**Feature enablement is a default too.** vLLM v0.28.0 turns prefix caching on for Mamba/hybrid
models by dropping the `and not model_config.is_hybrid` guard that made it opt-in at
v0.27.1.[^vllm-mamba-prefix] The mode auto-selected alongside it changed as well, from a
conditional `"all"`/`"align"` choice to unconditional `"align"` — so cache-hit behavior changes even
for hybrid models that already had prefix caching.[^vllm-mamba-prefix] Set
`--no-enable-prefix-caching` or `--mamba-cache-mode` explicitly to hold v0.27.x behavior.

**Do not schedule migration work off a deprecation notice's stated removal version.** vLLM's
`calculate_kv_scales` deprecation names v0.19 as its horizon: *"This option is deprecated and will be
removed in v0.19."*[^vllm-kv-scales-removal] **v0.19.0 shipped on 2026-04-02 still carrying the
option — and still carrying its own removal notice.** The symbol persists unchanged through v0.20.0,
v0.25.0 and v0.27.1 (five occurrences in `vllm/config/cache.py` at each) and is gone only at v0.28.0
(zero).[^vllm-kv-scales-removal] **A stated removal version is a statement of intent that slipped
here by nine minor releases and about five months.** Track the symbol's presence in the tree at the
tag you intend to install; that is the only statement of removal that is reliably true.

# Open questions

- **The two gates are not equally defended, and the difference matters.** The capture ceiling has a
  benchmark behind it, if a narrow one (above). The batch-default gate does not: the commit
  introducing the ≥160 GiB tier offers only *"Update this num to a larger num when gpu memory is
  enough, perf can be seen #51725"*, and #51725 is a different change rather than a
  `max_num_batched_tokens` sweep.[^vllm-batch-defaults] Neither the 160 GiB threshold nor the 16384
  value has a stated methodology. Treat them as the project's operating points, not as tuned optima.
- The memory gate is vendor-blind in its top branch: it tests `get_device_total_memory() >= 160 GiB`
  with no vendor or capability condition, so any accelerator reporting that much memory receives the
  new defaults.[^vllm-batch-defaults] (The second branch additionally excludes devices whose name
  contains `"a100"`, and TPU-specific overrides are applied afterwards, so the memory-only reading
  holds for the top tier alone.) Whether 16384 is appropriate on non-NVIDIA devices at that memory
  size is not addressed by the source.
- Removing the on-the-fly KV-scale calibration path leaves scales defaulting to 1.0 when a
  checkpoint carries none, but no source quantifies the accuracy cost of that
  fallback.[^vllm-kv-scales-removal]
- Whether the SGLang default flips change numerics (the MoE one is adjacent to reduction ordering)
  is not stated, and neither flip is accompanied by accuracy validation in the source consulted.
- This concept generalizes from two serving projects observed over one fortnight. The mechanism
  (device-conditioned defaults) is structural and unlikely to reverse, but the specific gates will
  move again; re-derive them from the tree rather than citing the values here after `stale_after`.

# Conflict with a stable concept

The stable [scope boundary](../foundations/scope-boundary.md) records, of the previous expedition,
that "Inference deployment more broadly remains uncovered." This draft is inference deployment more
broadly. **The stable concept wins:** the advisor must continue to treat general inference-deployment
questions as uncovered, and may use this draft only at `Evidence: unverified` and only for the
narrow decision it states — which defaults to pin, and how to read a serving benchmark. Recorded
here rather than resolved; promotion would require the boundary to be revised deliberately.

# Relationship to other concepts

The measurement discipline here is the deployment-side instance of the caution recorded in
[published-result reproducibility](published-result-reproducibility.md): a serving benchmark is
under-specified unless it names the device class, because on these engines the device class selects
the configuration. It also supplies the missing half of
[speculative-decoding concurrency](speculative-decoding-concurrency.md) — that concept establishes
that the right speculation setting depends on load; this one establishes that the *baseline* it is
measured against depends on hardware.

[^vllm-batch-defaults]: vllm commit 4988df2e, `[Config] Update default _max_num_batched_tokens from 8192 to 16384 (#51726)`, authored 2026-08-11 (source id: vllm-batch-defaults). Verified independently on 2026-08-31 against the repository: `git tag --contains 4988df2eb` returns `v0.28.0 v0.28.0rc1 v0.28.0rc2 v0.28.1rc0` and no v0.27.x tag; `git show v0.27.1:vllm/engine/arg_utils.py` contains no `160 * GiB_bytes` branch while `git show v0.28.0:...` contains exactly one. Tier values read from the tree at each tag: ≥160 GiB → batched {LLM 16384, API 16384}, seqs {1024, 1024}; ≥70 GiB and not a100 → batched {16384, 8192}, seqs {1024, 1024}; fallback → batched {8192, 2048}, seqs {256, 256}. The retained in-code note excluding A100 reads: "NOTE(Kuntai): Setting large `max_num_batched_tokens` for A100 reduces throughput, see PR #17885 for more details." The quoted justification is from the PR description for #51726, read on 2026-08-31.
[^vllm-cudagraph-blackwell]: vllm commit 021b7d98, `[Perf] Raise Blackwell CUDA graph capture default to 1024 (#49390)`, authored 2026-08-07 (source id: vllm-cudagraph-blackwell). Verified on 2026-08-31: contained in `v0.28.0 v0.28.0rc1 v0.28.0rc2 v0.28.1rc0`. The executable line at `v0.28.0:vllm/config/vllm.py` is `default_max_graph_size = (1024 if current_platform.is_device_capability_family(100) else 512)`; the corresponding expression at `v0.27.1` is `min(self.scheduler_config.max_num_seqs * decode_query_len * 2, 512)` with 512 hardcoded. A variant line also appears in the `_set_cudagraph_sizes` docstring at v0.28.0 using a different predicate (`is_data_center_blackwell`); the figures here are taken from the executable path.
[^vllm-cudagraph-pr]: PR description for vllm #49390 (source id: vllm-cudagraph-pr), read 2026-08-31. **Provenance caveat:** GitHub PR and release bodies are not stored in the git repository, so unlike every other claim in this concept they could not be verified against a git object; this text was retrieved through a summarizing fetch. The benchmark table (512 → 1024 output tok/s: 1,127 → 7,559 at concurrency 64; 904 → 5,101 at 128; 977 → 4,812 at 256), the hardware/workload description, the 80 s / 4.88 GiB capture cost, and the "B200 validation is still pending" sentence were each reproduced consistently across three independent fetches by two different agents. Treat the figures as well-corroborated but not git-verified.
[^vllm-mamba-prefix]: vllm commit f9c74b4b, `[Mamba] enable prefix cache by default (#50991)`, authored 2026-08-04 (source id: vllm-mamba-prefix). Verified on 2026-08-31: contained in `v0.28.0` and its rcs, not in v0.27.x. At `v0.27.1:vllm/engine/arg_utils.py` the default is computed as `(model_config.is_prefix_caching_supported and not model_config.is_hybrid)` under the comment "Hybrid models support prefix caching but keep it opt-in for now while the feature matures"; at `v0.28.0` it is `model_config.is_prefix_caching_supported`. The `"align"` mode selection appears at `v0.28.0:vllm/model_executor/models/config.py`.
[^vllm-kv-scales-removal]: vllm commit dd11df04, removal of `calculate_kv_scales` (#49389), authored 2026-08-03 (source id: vllm-kv-scales-removal). Verified on 2026-08-31: contained in `v0.28.0` and its rcs. The deprecation text is quoted verbatim from `git show v0.27.1:vllm/config/cache.py` (docstring at line 112, and the `_warn_deprecated_calculate_kv_scales` logger warning at line 275). Occurrence counts of `calculate_kv_scales` in that file by tag: v0.19.0 = 5, v0.20.0 = 5, v0.25.0 = 5, v0.27.1 = 5, v0.28.0 = 0. The v0.19 line was checked directly: `git tag | grep '^v0\.19'` returns `v0.19.0`, `v0.19.0rc0`, `v0.19.0rc1`, `v0.19.1`, `v0.19.1rc0`, `v0.19.2rc0`, and v0.19.0 is dated 2026-04-02. An earlier version of this concept asserted that v0.19 never shipped; that was false and was corrected in the skeptic pass.
[^sglang-environ-0518]: sglang `python/sglang/srt/environ.py` at tag v0.5.18 (source id: sglang-environ-0518), tag commit `71de97b2` dated 2026-08-20. Verified on 2026-08-31 by an exhaustive diff of every `EnvBool` declaration in the file at both tags (286 unique names at v0.5.17, 285 at v0.5.18): four names flip `False → True` (`SGLANG_AUTO_NUMA_BIND`, `SGLANG_ENABLE_MOE_DEFERRED_FINALIZE`, `SGLANG_OPT_FUSE_MHC_POST_PRE`, `SGLANG_OPT_UNIFIED_CACHE_FREE_OUT_OF_WINDOW_SLOTS`), 26 names present at v0.5.17 are absent at v0.5.18, and 25 are newly present. No name flips `True → False`.
