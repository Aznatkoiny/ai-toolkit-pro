---
type: Architecture Pattern
title: "Cross-stream buffer lifetime: keepalive plus wait_event, not record_stream"
description: >
  When a producer CUDA stream allocates a buffer that a consumer stream reads, `Tensor.record_stream`
  is correct but hands block reuse to the allocator's event polling, so the number of live buffers —
  and therefore peak memory — is set by how far ahead the CPU runs rather than by the pipeline depth
  you designed. Holding a Python reference and enqueueing `stream.wait_event(event)` BEFORE dropping
  it makes the buffer count a design parameter. The ordering matters: wait_event before del.
tags: [pytorch, cuda, streams, memory, fsdp, distributed-training, offload]
tier: frontier
status: draft
stale_after: 2027-04-05
generated:
  by: expedition/weekly-2026-10-05
  at: 2026-10-05T00:42:00Z
sources:
  - id: pt-devlog-streams
    resource: https://github.com/pytorch/devlogs/blob/bc81039c71dad3df74415d4bab232327a23d949d/content/eager/2026-09-29-cross-stream-memory-without-record-stream.md
    title: "Cross-stream memory management: wait_event instead of record_stream (PyTorch devlogs, eager)"
    author: "Wei Feng (@weifengpy), PyTorch"
    last_modified: 2026-09-29
---

# Pattern

**Any time a buffer is allocated on one CUDA stream and read on another — communication/compute overlap, activation offload, a custom all-gather — three implementations are available and only one gives you a peak memory you chose.** The caching allocator knows only the stream a tensor was *allocated* on, so the producer stream is free to hand that block to a later allocation the moment the block is freed, regardless of whether the consumer stream has finished reading it.[^pt-devlog-streams]

**The naive version is a correctness bug, not a performance one.** Dropping the reference as soon as the consumer kernel is enqueued lets the allocator reuse the block immediately. In the post's single-GPU repro (4 layers, HIDDEN = BATCH = 4096, 64 MB of parameters, 50 trials, H100), that corrupts results every time: `[FAIL] 50/50 trials corrupted, at most 1 param blocks per run (4 layers)`.[^pt-devlog-streams]

**`record_stream` fixes correctness and silently surrenders control of memory.** It is correct — `[PASS] 0/50 trials corrupted` — but the same repro then holds `at most 4 param blocks per run (4 layers)`, i.e. every layer's buffer live at once in a pipeline designed to need two.[^pt-devlog-streams] The reason is the handoff: `record_stream` "hands memory reuse to the allocator's event polling", so, in the post's words, "The number of live buffers is bounded by **how far the CPU runs ahead**, not by the two-deep pipeline you designed."[^pt-devlog-streams] Two consequences follow, and the second is the one that bites in production:

- **Peak memory becomes nondeterministic.** It "changes with CPU speed, kernel timing, and anything else that shifts the race."[^pt-devlog-streams] A job that fits on one host can OOM on an identical host under different load.
- **Hidden synchronizations appear exactly when you are already in trouble.** Under memory pressure the allocator's OOM-retry path calls `release_cached_blocks`, "which blocks the CPU on *every* outstanding `record_stream` event (`cudaEventSynchronize`) before it can reclaim those blocks."[^pt-devlog-streams] So the failure mode is a stall that shows up only near the memory ceiling.

**The recommended pattern — keep a reference, defer the `wait_event`.** Hold the buffer in Python, record an event on the consumer stream after the consuming kernel, and enqueue `wait_event` on the *allocation* stream before releasing the reference. The same repro then reports `[PASS] 0/50 trials corrupted, at most 2 param blocks per run (4 layers)` — correct, and at the depth the pipeline was designed for.[^pt-devlog-streams]

**The ordering is the whole trick, and getting it backwards reintroduces the corruption.** The invariant is that the `wait_event` must be enqueued on the allocation stream *before* the block is released. The post is explicit: "Put `wait_event` *before* `del`, not after. If you `del` first, any allocation that sneaks in between (a hook, another module, another library) can get the block, and its kernels won't be ordered after the consumer."[^pt-devlog-streams] **This is why the pattern cannot be applied by inspection of your own module alone** — the intervening allocation can come from code you did not write.

**PyTorch's own current-generation implementation is the corroborating evidence.** "On CUDA, FSDP2 never calls `record_stream`."[^pt-devlog-streams] Where FSDP2 does keep a buffer alive for an unbounded window, there is now a knob that converts it to this pattern: `FSDPModule.set_reduce_scatter_max_input_buffers(2)` (experimental), whose cost the post names as "one extra reduce-scatter input buffer, a known amount of memory".[^pt-devlog-streams] **The contrast with FSDP1 tells you what the alternative costs:** FSDP1 frees unsharded parameters with `record_stream` and therefore ships a CPU-side rate limiter (`limit_all_gathers=True`, on by default) that bounds growth "by blocking the CPU thread, capping all-gathered memory at two FSDP instances."[^pt-devlog-streams] That is the general shape of the trade: with `record_stream` you buy bounded memory back by stalling the CPU; with keepalive plus `wait_event` you set the bound directly.

**When `record_stream` is still the right call.** The post does not claim it is never appropriate, and nothing here argues for ripping it out of working code whose peak memory is comfortably inside budget. The pattern earns its complexity when peak memory is near the ceiling, when it must be predictable across hosts, or when you are debugging an OOM that moves between runs.

# Open questions

- The repro is single-GPU, 4 layers, one shape, on an H100, and reports block counts and corruption rates rather than throughput.[^pt-devlog-streams] The memory claim is a count of live buffers, not a measured end-to-end peak on a real training job, and no overhead figure for the extra event bookkeeping is published.
- `set_reduce_scatter_max_input_buffers` is labelled experimental,[^pt-devlog-streams] so its API and default are not safe to build a launch script around yet; the source gives no release containment for it.
- The post covers CUDA. Whether the same allocator-handoff semantics and the same remedy apply on ROCm or XPU is not addressed, and the explicit scoping of "On CUDA, FSDP2 never calls `record_stream`" implies other backends may differ.
- Single source, and it is a PyTorch-project artifact describing PyTorch's own design choice. No independent party has reproduced the block counts; tier is `frontier` accordingly.

# Related

- The failure this pattern prevents is silent in the naive form and nondeterministic in the `record_stream` form, which places it in the class of defects that do not raise — see [published-result reproducibility](published-result-reproducibility.md) for the evidence discipline that applies to the single-source measurements above.

[^pt-devlog-streams]: PyTorch devlogs, "Cross-stream memory management: wait_event instead of record_stream" (source id: pt-devlog-streams), post frontmatter `date: 2026-09-29`, author `Wei Feng (@weifengpy)`, read at repo commit `bc81039` and re-fetched 2026-10-05. Supplies the TL;DR allocator framing, the three implementations and their trial lines (`[FAIL] 50/50 ... at most 1 param blocks`, `[PASS] 0/50 ... at most 4 param blocks`, `[PASS] 0/50 ... at most 2 param blocks`), the CPU-run-ahead bound, the nondeterministic-peak and `release_cached_blocks` consequences, the `wait_event`-before-`del` invariant and its rationale, and the FSDP2/FSDP1 comparison including `set_reduce_scatter_max_input_buffers(2)` and `limit_all_gathers`. Repro script `cross_stream_demo.py` is included in the post; measurements are 50 trials, 4 layers, HIDDEN = BATCH = 4096, 64 MB parameters, H100.
