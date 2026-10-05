---
type: Decision Rule
title: "Prefill/decode disaggregation buys goodput and ITL tail, and charges every first token for the KV transfer"
description: >
  Splitting prefill from decode is not a throughput optimization. It buys goodput — the rate you can
  sustain while requests still meet both TTFT and ITL targets — and it stabilizes the ITL tail, while
  the KV-cache transfer lands on every TTFT. Verify the transfer path before benchmarking anything
  else: on a box without GPU peer-to-peer, a 470 MB KV handoff took ~1.3 s and missed a 2 s TTFT
  target at every request rate even though the ITL tail stayed flat. If TTFT is binding, stay collocated.
tags: [inference, serving, disaggregation, vllm, goodput, latency, kv-cache]
tier: frontier
applies_to:
  - deciding whether to split an LLM deployment into prefill and decode pools
  - diagnosing an ITL p99 that misses its SLO under production load
  - reading a disaggregated-serving speedup or goodput claim
  - capacity planning for long prompts at high concurrency, or for agent loops over a growing context
  - deciding whether to move templating and tokenization off GPU nodes
status: draft
stale_after: 2027-01-05
generated:
  by: expedition/weekly-2026-10-05
  at: 2026-10-05T00:42:00Z
sources:
  - id: vllm-disagg-guide
    resource: https://github.com/vllm-project/vllm-project.github.io/blob/f9792a2e4f2b65c5ef3291396f941a1d831cc6b1/_posts/2026-09-29-disaggregated-serving-guide.md
    title: "Taking vLLM Apart: A Practical Guide to Disaggregated Serving (source of blog.vllm.ai)"
    author: "Martin Hickey (IBM Research)"
    last_modified: 2026-09-29
---

# Rule

**Do not reach for prefill/decode disaggregation to raise throughput. Reach for it when your ITL tail misses its SLO, and only after you have verified that the KV cache moves fast between the two pools.** The post states the framing directly: "The pitch isn't peak throughput. With no latency target, splitting the same GPUs into prefill and decode pools won't necessarily move more tokens per second. What it buys is **goodput**: the request rate you can sustain while requests still meet both their TTFT and ITL targets."[^vllm-disagg-guide] Everything below assumes vLLM v0.30.0 or later, which the post sets as its floor.[^vllm-disagg-guide]

**The ITL win is real and large; the TTFT cost is paid on every single request.** On the author's own two-GPU box, median ITL was 21–24 ms in both configurations up to 1 req/s, but at 0.4 req/s "collocated p99 jumps to 169 ms while P/D holds at 29 ms and never exceeds 52 ms."[^vllm-disagg-guide] On the same box the transfer cost dominated first-token latency: each 8k prompt's ~470 MB of KV cache took about 1.3 s to reach decode, so "At 0.2 req/s, P/D median TTFT was 2.2 s against 0.7 s collocated, so it missed a 2 s TTFT target at every rate even though its ITL tail stayed flat."[^vllm-disagg-guide] **Read that sentence as the decision rule it is:** the two metrics move in opposite directions, so "is disaggregation better" has no answer until you say which target binds.

**Size the transfer before you commit, because it is arithmetic, not luck.** "Llama-3.1-70B in BF16 stores 320 KiB per token, so a 10k-token prompt hands decode about 3 GB. That's roughly 65 ms at a 400 Gb/s line rate before any overhead and all of it lands on TTFT."[^vllm-disagg-guide] Do this multiplication for your model and prompt length first; it tells you the floor on your added TTFT independent of any software.

**Run the pre-flight gate, and distrust your own benchmark until it passes.** The post gives a two-step check: "On one box, `nvidia-smi topo -p2p r` should say `OK` between your prefill and decode GPUs. Then send a few long prompts one at a time and read decode's `KV Transfer metrics` line. If `Avg xfer time` is in the hundreds of milliseconds, fix that first."[^vllm-disagg-guide] **The author's own box failed this gate** — the L40S pair "can't do peer-to-peer copies (`nvidia-smi topo -p2p r` reports `NS`)" — and the author says so, noting that bandwidth alone does not explain the 1.3 s: "Even staged through host memory, PCIe 4.0 should move that in tens of milliseconds. Most of it is overhead around the copy, including decode only noticing a finished transfer when it polls between its own forward steps."[^vllm-disagg-guide] So the published TTFT regression is a measurement of a deliberately weak fabric, not a property of disaggregation. Treat it as the worst case and the gate as the thing that distinguishes your case from it.

**The situations that justify it, per the post's own decision table:** disaggregate when "ITL p99 misses your SLO under production load" (named as "the main use case"); disaggregate for "Long prompts at high concurrency" *if* the transfer is fast, because "Prefill interference is worst here"; for "Chat or agent loops over a growing context", disaggregate "with bidirectional transfer" paired with KV offloading or a shared KV cache. **Stay collocated when "TTFT is the binding constraint"** ("The transfer lands on every first token"), when the KV transfer is slow, or on "Low, bursty or latency-insensitive traffic."[^vllm-disagg-guide]

**A separate, cheaper split is available and is often the one to do first.** When "Templating, tokenizing or parsing shows up in your GPU nodes' CPU profile", split off the render tier (`/render`, `/derender`, `vllm serve --tokens-only`) rather than the model.[^vllm-disagg-guide] Two concrete figures bound it: templating and tokenizing a 9k-token chat prompt for Qwen2.5-7B cost about 15 ms of CPU, and "One render server with default settings topped out at 73 req/s using just over one core" — because `--renderer-num-workers` "defaults to **1**."[^vllm-disagg-guide] The named cost is on the return path: streaming derender through a reasoning or tool parser measured "roughly 9× the in-process CPU at matched load and +15% on E2E p50" on multi-thousand-token reasoning output.[^vllm-disagg-guide]

**Two silent-failure modes are disclosed, and both produce wrong output or wrong configuration rather than an error.** For reasoning models, decode's cached blocks include the thinking traces it generated; if the next turn's prompt drops them — "as Qwen3's chat template does on its own" — "prefill's prompt no longer lines up with decode's blocks and you get wrong output, not just slow output. Nothing in vLLM catches that mismatch today."[^vllm-disagg-guide] Separately, render, derender and the engine "have to agree on the model, tokenizer, chat template and parser flags", and "A mismatch doesn't raise an error."[^vllm-disagg-guide] **If you adopt either split, these two agreements become your responsibility to assert in deployment, because the stack will not assert them for you.**

# Open questions

- The ITL, TTFT and render figures are the author's own on 2× L40S (48 GB, PCIe, no NVLink, no peer-to-peer), Qwen2.5-7B, ~8k prompts, 256 output tokens, 100 Poisson-arrival requests per rate, prefix caching off, against a collocated `vllm serve --data-parallel-size 2` baseline the author calls weaker than two independent replicas behind a load balancer.[^vllm-disagg-guide] No date beyond the post date. The direction of the ITL/TTFT trade should generalize; the magnitudes will not.
- The two favourable goodput results are **cited from other posts, not measured here**: AMD's MoRI-IO benchmark (Qwen3-235B-A22B-FP8, 8 req/s, one 8-GPU MI300X node, 73/100 vs 30/100 requests meeting a 1 s TTFT and 50 ms ITL target, "about 2.4× the goodput") and llm-d's P/D guide ("about 59% lower mean end-to-end latency and 67% lower P95 for gpt-oss-120b on 16 H200s").[^vllm-disagg-guide] Neither carries a measurement date in this source, and neither was independently checked by this expedition.
- No source here establishes the crossover point — the KV transfer time, prompt length, or concurrency at which disaggregation starts to win on a fabric that *does* pass the pre-flight gate. The gate tells you when you are clearly in the bad regime, not where the boundary is.
- The post links a bidirectional KV-transfer post dated 2026-09-30 which was not present in the source repository at the commit read here, so the "chat or agent loops" recommendation rests on a reference that could not be followed.

# Related

- The disclosed TTFT/ITL opposition means a disaggregation speedup quoted without naming which metric and which fabric it was measured on is not actionable; the same caution applies to the cited third-party goodput figures above. See [published-result reproducibility](published-result-reproducibility.md).
- Speculative decoding is the other serving knob whose optimum moves with concurrency rather than with the model — see [speculative-decoding concurrency](speculative-decoding-concurrency.md).

[^vllm-disagg-guide]: vLLM blog, "Taking vLLM Apart: A Practical Guide to Disaggregated Serving" (source id: vllm-disagg-guide), post dated 2026-09-29 (Jekyll filename date; no explicit `date:` field), author `Martin Hickey (IBM Research)`, read at repo commit `f9792a2` (commit dated 2026-09-30) and re-fetched 2026-10-05. Supplies the goodput framing, the v0.30.0 floor, the 320 KiB/token arithmetic, the ITL p99 and TTFT measurements with their stated benchmark configuration, the `nvidia-smi topo -p2p r` / `Avg xfer time` pre-flight gate and the `NS` result on the author's own box, the full decision table rows quoted above, the render-tier figures (15 ms CPU, 73 req/s, `--renderer-num-workers` default 1, 9× CPU and +15% E2E p50 on streaming derender), the reasoning-model block-mismatch warning, the render/engine flag-agreement warning, and the two cited third-party goodput results.
