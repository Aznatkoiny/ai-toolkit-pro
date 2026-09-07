---
type: Architecture Pattern
title: "The single-node long-context SFT memory ladder, and its attention-shape gate"
description: >
  Four levers applied in order — chunked loss, RoPE rescaling, activation offload, sequence
  parallelism — bring a million-token training sequence from an impossible 288 GB per GPU down to a
  measured 63.6 GB per card. Each lever has a measured effect and a precondition, and the last one
  is closed entirely to models whose layers use sliding-window or chunked attention — by a refusal
  that is not yet in any accelerate release.
tags: [training, fine-tuning, long-context, context-parallelism, fsdp, memory, trl]
tier: frontier
status: draft
stale_after: 2027-03-07
generated:
  by: expedition/weekly-2026-09-07
  at: 2026-09-07T00:00:00Z
sources:
  - id: trl-long-context
    resource: https://github.com/huggingface/trl/blob/5dd51e4d8caf495dc4cbddcddef4c659ad8174b9/docs/source/long_context_training.md
    title: "huggingface/trl — Training Beyond 1M Tokens (docs/source/long_context_training.md at 5dd51e4, 'Rewrite the long context guide' #7003)"
    author: Quentin Gallouédec (Hugging Face)
    last_modified: 2026-09-03
  - id: transformers-gc-offload
    resource: https://github.com/huggingface/transformers/commit/69a7fb1aca7f2e7487294846be5859ebb6db9462
    title: "huggingface/transformers commit 69a7fb1 — Add offload to gradient checkpointing (#48444)"
    author: Quentin Gallouédec (Hugging Face)
    last_modified: 2026-09-01
  - id: accelerate-cp-refuse
    resource: https://github.com/huggingface/accelerate/commit/bd204169b4412c059d40318c455fe8a826374bd1
    title: "huggingface/accelerate commit bd20416 — Refuse context parallelism for models with sliding-window or chunked attention layers (#4177)"
    author: Quentin Gallouédec (Hugging Face)
    last_modified: 2026-08-31
---

# Pattern

Training on sequences of hundreds of thousands of tokens is not one technique but a **ladder of four
memory levers, applied in order, each with a measured effect and a precondition.** The reference
run fine-tunes Qwen3-8B on 1.049M-token sequences — one sequence per step — on a single node of
8×H100 with `cp_size: 8`: "Naively, this sequence needs 288 GB per GPU. The rest of this guide is
the story of how that comes down to 56."[^trl-long-context]

**Mind which model each measurement comes from.** Only that headline run is Qwen3-8B. Every
measurement for rungs 1 to 3 below is **Qwen3-4B on a single 80 GB card** — "Take Qwen3-4B on a
single 80 GB card and grow the sequence" — and the only measured million-token endpoint in the
guide is 63.6 GB on **four** GPUs. The 56 GB in the sentence above is the guide's framing figure for
its 8-GPU configuration and is never separately demonstrated.[^trl-long-context]

**Read the first step's loss before you read anything else.** In the reference run it is 4.3, and
the guide states that "a run that is subtly misconfigured for long context starts around 10
instead."[^trl-long-context] That is the cheapest available check that the positions are configured
correctly — it arrives about sixteen minutes after launch (ten minutes of loading and tokenizing,
then a 380 s step) instead of at the end of the run. The guide offers it as one diagnostic, not as a
check of the whole ladder.

## Rung 1 — chunked loss (already on)

The loss is computed a chunk of rows at a time, each chunk freed before the next. In TRL "there is
nothing to do: the chunked loss is the default", and the opt-out is `loss_type="nll"` in
`SFTConfig`.[^trl-long-context] Measured effect: "this one change alone takes us from 32k tokens to
160k."[^trl-long-context] The practical consequence is inverted from the usual: **if you are hitting
OOM in the loss, check whether something in your config turned this off.**

## Rung 2 — rescale the positions (RoPE/YaRN)

Beyond the model's trained context the positions run off the end, and the failure is a quality
failure, not an OOM. Passing YaRN at load time:

```python
training_args = SFTConfig(
    ...,
    model_init_kwargs={
        "rope_parameters": {
            "rope_type": "yarn",
            "rope_theta": 1_000_000,  # has to match what the model ships with
            "factor": 4.0,
            "original_max_position_embeddings": 40960,
        },
    },
)
```

Measured effect: "The rescaled run stays flat all the way to 160k. Over the last 20k tokens it
averages a loss of 2.8, against 7.3 without the rescaling."[^trl-long-context] **This rung is the
one that is silent if you skip it** — the run completes, the memory fits, and the model is simply
worse on the long tail of the sequence.

## Rung 3 — offload the saved activations

With gradient checkpointing on, what remains resident is one saved tensor per layer, and at long
sequence lengths those dominate. They are written in the forward and not read until the backward, so
they can live in host memory in between:

```python
training_args = SFTConfig(..., gradient_checkpointing_kwargs={"offload": True})
```

Measured at 96k tokens: "instead of 38 bands stacking up, only 4 are ever resident at once, and the
peak drops from 59.9 GB to 48.8 GB", and the reachable sequence length on one card goes from 160k to
256k.[^trl-long-context] Below 48k the two are identical — **the lever does nothing at short
lengths, and it is not free at long ones**: every saved activation crosses to the host and back on
the compute stream.[^trl-long-context][^transformers-gc-offload]

**Availability gate:** the guide states plainly that this needs "transformers from main: the example
uses gradient checkpointing's `offload`, which is not in a release yet."[^trl-long-context] The
supporting commit landed 2026-09-01.[^transformers-gc-offload]

## Rung 4 — split the sequence across GPUs

Two exchanges exist and **the choice is made by your distributed backend, not by preference**:
`cp_size` (context parallelism) requires FSDP2 and accelerate 1.11; `sp_size` (Ulysses sequence
parallelism) requires DeepSpeed 0.18.1 and accelerate 1.12; "the two knobs do not cross over today
… Pick the backend and the method follows."[^trl-long-context] CP splits tokens and scales to any
number of GPUs; SP splits attention heads and is capped at the number of KV heads (8 in the
reference model).[^trl-long-context]

```yaml
parallelism_config:
  parallelism_config_cp_size: 4
```

Measured: four GPUs carry the full million tokens at 63.6 GB, where one card stops just past 256k.
Communication is cheaper than expected — at 131k tokens a step takes 34.6 s on two GPUs, 17.8 s on
four and 9.5 s on eight, "3.7x of a possible 4x" going from two to eight.[^trl-long-context] (The
snippet above is the guide's four-GPU illustration; its shipped reference config for the 1M run sets
`parallelism_config_cp_size: 8`, "the whole node forms one context-parallel
group".[^trl-long-context])

**Three preconditions come with rung 4:**

1. Sequences must be padded to a multiple of `cp_size * 2` — `pad_to_multiple_of=8` for four
   GPUs.[^trl-long-context]
2. **Packing is out.** It relies on a block-diagonal mask, which the causal-SDPA requirement
   forbids, "and TRL raises if you ask for both."[^trl-long-context]
3. **The model's attention shape decides eligibility.** Context parallelism drops the per-layer mask
   and forces `is_causal=True`, so accelerate on `main` refuses any model whose layers use
   sliding-window or chunked attention: "Context parallelism can only express full causal attention:
   the per-layer mask has to be dropped, so those layers would silently be trained with full causal
   attention instead."[^accelerate-cp-refuse] The guide names the excluded families — "OpenAI
   GPT-OSS, Gemma 3 and 4, Qwen3.5 and later" — and the reason Qwen3 and Qwen3-MoE are used instead:
   they are full attention throughout.[^trl-long-context] The parallel restriction for Ulysses is
   linear-attention layers, whose recurrent state is never exchanged across
   ranks.[^accelerate-cp-refuse]

   **Do not rely on that refusal to protect you yet.** It landed 2026-08-31 and is in no accelerate
   release: the newest tag, v1.14.0 (2026-06-11), still contains `_attach_context_parallel_hooks`
   without the check.[^accelerate-cp-refuse] A reader who installs the versions this guide itself
   requires — accelerate 1.11 for CP, 1.12 for SP — gets **no refusal at all**, and therefore the
   silent mask-drop. Until the fix ships, check your model's `layer_types` yourself before enabling
   `cp_size`.

## One allocator setting that is not optional

`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. At a million tokens the reference run "needs
63.6 GB on an 80 GB card, and still fails without it: the tensors it asks for are large and
contiguous, and the allocator cannot find room for them among the blocks it already
holds."[^trl-long-context] **16.4 GB of headroom is not enough headroom when the requests are large
and contiguous.**

# Open questions

- Every measurement here comes from one guide and one model family: Qwen3-4B on a single 80 GB card
  for rungs 1 to 3, Qwen3-8B on 8×H100 for the million-token reference run. The ordering of the
  ladder should transfer; the specific crossovers (48k for offload, 160k → 256k, 63.6 GB at 1M)
  should not be assumed to.
- **All three sources are the same author at the same organization** — Quentin Gallouédec, across
  trl, transformers and accelerate. This is one account of one system, not three independent ones,
  which is why the tier is `frontier`. There is no independent reproduction.
- The guide reports step time only for the CP sweep at 131k. **The wall-clock cost of activation
  offload is described qualitatively ("that traffic has to fit between the compute it sits next
  to") and never quantified**, so the throughput price of rung 3 is unknown from this source.
- Whether the attention-shape exclusion is inherent to context parallelism or specific to
  accelerate's mask-dropping implementation is not settled by these sources; the accelerate comment
  frames it as a property of what CP "can express".[^accelerate-cp-refuse]
- The ladder assumes full fine-tuning. Nothing here establishes how the rungs interact with
  parameter-efficient methods.

# Conflict with a stable concept

The stable [scope boundary](../foundations/scope-boundary.md) lists "LLM / foundation-model
fine-tuning (LoRA, PEFT, instruction tuning)" as covered by no stable concept, and this pattern is a
fine-tuning recipe. **The stable concept wins:** the advisor must still give the canonical
OUT-OF-SCOPE response for fine-tuning methodology, and may use this draft only with
`Evidence: unverified` stated. Recorded here rather than resolved; promotion would require the
boundary to be revised deliberately.

# Related

- [The dangerous defects are the ones that do not raise](silent-training-defects.md) — rung 4's
  refusal is one instance of that class.

[^trl-long-context]: huggingface/trl, "Training Beyond 1M Tokens", `docs/source/long_context_training.md` read at commit `5dd51e4` (source id: trl-long-context). All quoted text, the YaRN snippet, the 288 GB → 56 GB framing, the 4.3-versus-10 first-step-loss diagnostic, the 59.9 → 48.8 GB and 160k → 256k offload measurements, the CP/SP comparison table with its version requirements, the 34.6/17.8/9.5 s step times at 131k, and the `expandable_segments` note are stated there. Verified by fetching the file at that SHA on 2026-09-07.
[^transformers-gc-offload]: huggingface/transformers commit 69a7fb1, "Add offload to gradient checkpointing (#48444)", committer date 2026-09-01 (source id: transformers-gc-offload). The commit message describes holding checkpointed activations in pinned host memory through torch's `save_on_cpu`; the cost statement is in the documentation the same commit adds, `docs/source/en/grad_checkpointing.md`: "Both copies run on the compute stream, so this trades a slower step for the memory. Reach for it when a run does not fit otherwise, not to speed one up." The availability claim ("not in a release yet") is stated by the TRL guide and independently checked during the skeptic pass against transformers v5.16.1 (2026-08-26), which does not carry the option. Verified by fetching the commit and that file at the SHA on 2026-09-07.
[^accelerate-cp-refuse]: huggingface/accelerate commit bd20416, "Refuse context parallelism for models with sliding-window or chunked attention layers (#4177)", committer date 2026-08-31 (source id: accelerate-cp-refuse). Quoted text is the `ValueError` in `_attach_context_parallel_hooks` in `src/accelerate/big_modeling.py`; the same commit refuses linear-attention layers under Ulysses. Release containment checked on 2026-09-07: the refusal string is absent from `src/accelerate/big_modeling.py` at v1.14.0, the newest tag (committer date 2026-06-11), while `_attach_context_parallel_hooks` is present there — so the mask-dropping hook ships without the guard. Verified by checking out that SHA and fetching the file at the tag.
