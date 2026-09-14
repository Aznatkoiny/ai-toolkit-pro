---
type: Decision Rule
title: "Tag date does not imply containment, and prose does not tell you whether your checkpoint still loads"
description: >
  Framework removals reach you in three modes — hard failure at load, silent fallback, and silent
  semantic change — and a release note tells you what changed without telling you which mode applies
  to your deployment. Audit an upgrade against your own checkpoint and launch-script inventory, and
  verify containment with `git tag --contains` rather than inferring it from a tag's date: release
  branches are cut early, so a commit merged before a tag can still be absent from it.
tags: [upgrades, deprecation, migration, versioning, serving, release-engineering]
tier: frontier
applies_to:
  - planning a version upgrade of a serving engine or training framework
  - deciding whether a fix you need is present in a specific release tag
  - auditing launch scripts, Helm charts, or a model registry before a rollout
  - judging how much risk a release note is disclosing
status: draft
stale_after: 2027-03-14
generated:
  by: expedition/weekly-2026-09-14
  at: 2026-09-14T00:00:00Z
sources:
  - id: vllm-54809
    resource: https://github.com/vllm-project/vllm/pull/54809
    title: "vllm-project/vllm PR #54809 — remove group/dynamic activation ordering; raise at config parse (commit 2c9d68f80bd20af7af1bc539c044a4aebbe52f8e)"
    author: vLLM contributors
    last_modified: 2026-09-08
  - id: vllm-55353
    resource: https://github.com/vllm-project/vllm/pull/55353
    title: "vllm-project/vllm PR #55353 — v0.29 deprecation sweep: env vars and config aliases removed (commit 5fe77aecfc7687c1f3cc49862022ce34d45d1784)"
    author: vLLM contributors
    last_modified: 2026-09-11
  - id: vllm-56446
    resource: https://github.com/vllm-project/vllm/pull/56446
    title: "vllm-project/vllm PR #56446 — YaRN derived max_model_len no longer multiplied by scaling factor (commit c191787a6861868069bc4f6ed6f842af541de23a)"
    author: vLLM contributors
    last_modified: 2026-09-11
  - id: vllm-v0290
    resource: https://github.com/vllm-project/vllm/releases/tag/v0.29.0
    title: "vllm-project/vllm release v0.29.0 (tag sha 98dff2a)"
    author: vLLM Project
    last_modified: 2026-09-08
  - id: trl-1130
    resource: https://github.com/huggingface/trl/releases/tag/v1.13.0
    title: "huggingface/trl release v1.13.0 — PPOTrainer, PPOConfig and modeling_value_head.py removed"
    author: huggingface/trl contributors
    last_modified: 2026-09-10
  - id: tr-48685
    resource: https://github.com/huggingface/transformers/pull/48685
    title: "huggingface/transformers PR #48685 — huggingface-hub floor raised 1.5.0 to 1.31.0 (commit 80a79d1bef2bacfa10b1b543669eebffa3f0ec36)"
    author: huggingface/transformers contributors
    last_modified: 2026-09-12
---

# Rule

**Classify every removal in an upgrade by how it will reach you, because the three modes carry very
different risk.**

**Mode 1 — hard failure at load. Loud, and therefore the safest.** vLLM removed group and dynamic
activation-ordering support for GPTQ and compressed-tensors (roughly 3,900 deleted lines across CUDA,
ROCm and CPU kernels) and added guards that *raise* `ValueError` at config-parse time for
`desc_act=True` and for `actorder` in `{GROUP, DYNAMIC}`.[^vllm-54809] A large share of community GPTQ
quantizations ship `desc_act: true`, so the engine will simply not start on them. **The audit this
calls for is a grep of your own model registry's `quantize_config.json` / `config.json` for `desc_act`
and `actorder` before you plan the upgrade, not after the rollout fails.**[^vllm-54809]

**Mode 2 — silent fallback. The dangerous one.** The same release sweep removed the environment
variables `VLLM_MM_HASHER_ALGORITHM` and `VLLM_PREFIX_CACHE_RETENTION_INTERVAL`, which are now
**silently ignored rather than rejected** — no warning, no error, and no generic validator for
unrecognized `VLLM_` variables exists to catch them.[^vllm-55353] The compliance consequence is not an
inference from the outside: the deleted comment on the removed variable read "Use sha256 or sha512 for
FIPS compliance in government/enterprise deployments", and the surviving default is
`mm_hasher_algorithm: MMHasherAlgorithm = "blake3"`.[^vllm-55353] **A deployment that set
`VLLM_MM_HASHER_ALGORITHM=sha256` to satisfy a FIPS requirement now runs blake3 and reports
nothing.** A launch script or Helm chart is an unversioned interface into the engine, and nothing
validates it for you: enumerate the environment variables and CLI flags your deployment actually sets,
and check each against the release's removals.

**Mode 3 — silent semantic change. Configuration unchanged, behavior different.** vLLM stopped
multiplying the derived `max_model_len` by the scaling factor for `yarn`, `deepseek_yarn` and
`deepseek_llama_scaling`, treating `max_position_embeddings` as already scaled.[^vllm-56446] The
context length the engine accepts therefore changes without touching a flag, and previously accepted
long requests can now be rejected — the change's own scoping says two models move:
`Tele-AI/TeleChat3-36B-Thinking` from 131072 to 32768, and `sarvamai/sarvam-105b` from 5242880 to
131072.[^vllm-56446] The flip side is the defect being fixed: the old path let requests run past the
end of the cos/sin cache.[^vllm-56446] **Re-verify `--max-model-len` assumptions and client-side
truncation budgets as part of the upgrade, not as an incident response.**

**Read the diff, because prose and diff answer different questions.** The activation-ordering change
above does state its headline plainly — its description opens "Remove gptq group/dynamic activation
ordering entirely from vLLM. This includes tests, checkpoint format (we ignore g_idx now), and
kernels."[^vllm-54809] But the operational fact you need — that *your* `desc_act: true` checkpoint will
now fail at config parse, while a `desc_act=True` checkpoint with `group_size == -1` is silently
downgraded and keeps working — appears only in the diff, below a list of mechanical
cleanups.[^vllm-54809] **Prose tells you what changed; only the diff tells you whether your specific
artifact still loads.** That is the question an upgrade audit has to answer, and no release note is
organized around it.

**Verify containment before you pin, and do not infer it from a date.** Of thirteen in-window vLLM
changes checked with `git merge-base --is-ancestor`, none is reachable from the `v0.29.0` tag and every
one is reachable from `v0.29.1rc0`. The two tags are **not on one line of history**: they diverge at a
release-branch cut on 2026-08-31, with 14 commits unique to `v0.29.0` and 596 unique to
`v0.29.1rc0`.[^vllm-v0290] **So a commit merged days *before* a tag's date can still be absent from
that tag** — the v0.29.0 tag is dated 2026-09-08, and changes merged 2026-09-08 through 2026-09-11 are
not in it. `git tag --contains <sha>`, checked against each candidate tag, is the only answer; a
changelog entry and a tag date are not.

**Budget for API deletions, and check where the symbol actually lived before you judge the notice
given.** TRL v1.13.0 removed `PPOTrainer`, `PPOConfig` and `modeling_value_head.py`, freezing any PPO
pipeline at ≤1.12 until it is ported (`create_reference_model` survives, since BCO, A2PO and Online DPO
depend on it).[^trl-1130] The release note presents this as a bare removal — but the tree shows those
symbols were moved to `trl/experimental/ppo/` in November 2025 and shipped there through v1.12.0, a
roughly ten-month window under a namespace that carries no stability guarantee.[^trl-1130] **Here the
release note *understated* the notice that had been given, which is the mirror image of the failure
this concept warns about — the diff is the record in both directions. A dependency you import from an
`experimental/` path is already on notice, and your inventory should track that separately from
version pins.** Dependency floors move sharply enough to break locked environments on their own:
`transformers` raised its `huggingface-hub` floor from `>=1.5.0` to `>=1.31.0` — a 26-minor-version
jump — which will fail resolution against any co-installed library that caps
`huggingface_hub`.[^tr-48685]

**Read a stated removal target as a scheduling input.** vLLM's v0.29.0 release makes Model Runner V2
the default for all models and states the project is "considering Model Runner V1 deprecated and are
targeting v0.32 for its removal"; the same release removes ten model architectures, deprecates
`python -m vllm.entrypoints.openai.api_server` in favour of `vllm serve`, and removes the PyAV video
decoder backend.[^vllm-v0290] **A named removal version converts an open-ended migration into a dated
one — schedule against it rather than discovering it.**

# Open questions

- The three-mode taxonomy (hard failure / silent fallback / silent semantic change) is this concept's
  own organizing frame, generalized from the in-window examples. It is offered as a checklist, not as
  a claim from any source.
- **This concept was drafted around a stronger thesis — "release-note prose systematically undersells
  the diff" — and the skeptic pass falsified both of its examples.** The activation-ordering PR's
  description does disclose the removal and the checkpoint-format change in its opening line, and the
  TRL removal had a roughly ten-month `trl/experimental/` window the release note failed to mention.
  The drafting error is recorded rather than buried, because it is an instance of the very failure the
  concept describes: the draft read the prose and did not read the diff. What survives is narrower and
  better supported — the three-mode taxonomy, the containment rule, and the observation that prose and
  diff answer different questions in *both* directions. **Do not restore the stronger claim without
  new evidence.**
- Most examples come from one serving engine during one unusually large release cycle. The
  `transformers` dependency-floor bump and the TRL removal show the pattern is not vLLM-specific, but
  four of the six sources are vLLM and a single week cannot establish any base rate. The tier is
  `frontier` accordingly. **The rule to audit is well-founded; any claim about frequency is not.**
- The `huggingface-hub` floor of 1.31.0 specifically is asserted by the pin, not justified in the
  change — the visible motivation is only that `transformers` now takes `httpx` from
  `huggingface_hub.utils`'s re-export.[^tr-48685] Whether a lower floor would suffice is unestablished.
- This concept says to read the diff but does not address the cost of doing so at scale. For a release
  with several hundred commits, the practical scope is the subset touching your configuration surface
  — checkpoints, launch flags, environment variables, pinned dependencies — and no source here offers
  tooling for that triage.
- Release *dates* themselves proved unreliable this week and are worth treating with the same
  suspicion as release prose: see the log entry for 2026-09-14, where three artifacts gave three
  different dates for the same tag.

# Conflict with a stable concept

The stable [scope boundary](../foundations/scope-boundary.md) lists reinforcement learning as not
covered by any stable concept, and its 2026-08-17 section states that inference deployment beyond
speculative decoding remains uncovered. This draft touches both: the TRL item concerns a PPO
(reinforcement-learning) pipeline, and the vLLM items concern serving-engine deployment. **The stable
concept wins:** the advisor must still give the canonical OUT-OF-SCOPE response for RL methodology and
for inference-deployment design. This draft covers only the *upgrade-auditing discipline* — how to
bound the blast radius of a version bump and how to establish that a fix is in the tag you are pinning
— and never how to do RL or how to architect a serving stack. Usable only at `Evidence: unverified`.
Recorded here rather than resolved; promotion would require the boundary to be revised deliberately.

# Relation to existing concepts

The verification stance here is the same one
[published-result reproducibility](published-result-reproducibility.md) applies to published claims,
turned toward release engineering: a vendor's description of its own change is a hypothesis about
impact, and the diff is the evidence. Mode 3 (silent semantic change) is also the mechanism behind the
re-baselining requirement in
[performance attribution discipline](performance-attribution-discipline.md).

[^vllm-54809]: vllm-project/vllm PR #54809 (source id: vllm-54809), commit `2c9d68f`, dated 2026-09-08 from `git log`. Both raise sites — `normalize_and_validate_gptq_desc_act()` for GPTQ (including via a `dynamic` per-pattern rule) and the `CompressedTensorsConfig` check for `actorder` in `{GROUP, DYNAMIC}` — were read in the diff, as was the new `get_checkpoint_weight_mapper()` discarding `.g_idx` tensors. Diffstat: 3,918 deletions / 1,183 insertions across 99 files. **On the PR description:** it opens with "Remove gptq group/dynamic activation ordering entirely from vLLM. This includes tests, checkpoint format (we ignore g_idx now), and kernels" — so the headline and the checkpoint-format change *are* disclosed up front. Phrases such as "Dead code branching" and "Unused attribute assignments" appear further down as sub-bullets enumerating the mechanical cleanups the removal entailed, and it would be a misreading to present them as the description's framing of the change. The error text also names the fix ("Use a checkpoint with static activation ordering or desc_act=False"). Carve-out confirmed verbatim in the diff: `if desc_act and group_size == -1:` downgrades to `False` with the comment that activation ordering is a no-op for one group per output channel — **no warning is emitted**; "static"/"weight" actorder remains supported.
[^vllm-55353]: vllm-project/vllm PR #55353 (source id: vllm-55353), commit `5fe77ae`, dated 2026-09-11 from `git log`. Removal of the two environment variables, the `use_fp4_indexer_cache` config alias, the deprecated `CommonAttentionMetadata.seq_lens_cpu` / `num_computed_tokens_cpu` properties, and the ROCm `CUDA_VISIBLE_DEVICES` shim confirmed in the diff across `envs.py`, `config/{attention,cache,multimodal}.py`, `v1/attention/backend.py` and `platforms/rocm.py`. The underlying config *fields* survive as CLI/config options; only the environment-variable aliases and the deprecated properties are gone. The blake3 fallback consequence follows from the removal being a silent ignore rather than an error.
[^vllm-56446]: vllm-project/vllm PR #56446 (source id: vllm-56446), commit `c191787`, dated 2026-09-11 from `git log`. The exclusion of `yarn`/`deepseek_yarn`/`deepseek_llama_scaling` from the `scaling_factor` multiply in `_get_and_verify_max_len`, and the accompanying regression tests asserting 32768, were confirmed in the diff (`vllm/config/model.py`). **The PR's own text is internally inconsistent and this concept does not resolve it silently:** one line reads "Only sarvam-105b changes; DeepSeek-V3/R1, Kimi-K2, gpt-oss, A.X-K1, TeleChat3, Llama-3.1 and Qwen3 all keep their derived lengths", while the Purpose section and the added regression tests both have TeleChat3-36B-Thinking moving 131072 → 32768 (the test table carries `# TeleChat3-36B-Thinking: 32768 already scaled from 8192 by 4` against `("yarn", 4.0, 32768)`). **The tests are authoritative and the stale line is wrong; TeleChat3 does change.** The remainder of the unaffected list, and the claim that non-YaRN rope types (`linear`, `su`, `longrope`, `llama3`) are unchanged, is stated in the PR and is not independently verified here.
[^vllm-v0290]: vllm-project/vllm release v0.29.0 (source id: vllm-v0290), tag sha `98dff2a`. Date 2026-09-08 from the tag's `creatordate` via `git for-each-ref`; note the GitHub release page displays "September 9" (the page publication) and a release feed reported 2026-09-10 — the tag date is authoritative and the discrepancy is recorded in the log. The Model Runner V2 default, the quoted v0.32 removal target for V1, the ten removed architectures, the entrypoint deprecation and the PyAV removal are release-note prose; the Model Runner V2 default (#53183, `4aab2b0`, 2026-08-27) and the PyAV deprecation (#54231, `4fc943b`, 2026-08-29) were confirmed against commits. The containment finding is from `git merge-base --is-ancestor` run over thirteen in-window commits, each returning no for `v0.29.0` and yes for `v0.29.1rc0`. **The mechanism is a divergent release branch, not ordering in time:** `v0.29.0` is not an ancestor of `v0.29.1rc0`; their merge base is `f5c3cc240b` (2026-08-31), with 14 commits reachable only from `v0.29.0` and 596 reachable only from `v0.29.1rc0`. This is why a tag's date cannot be used to infer containment in either direction.
[^trl-1130]: huggingface/trl release v1.13.0 (source id: trl-1130), annotated tag `creatordate` 2026-09-10 00:40:15 +0000 via `git for-each-ref`. The removal of `PPOTrainer`, `PPOConfig` and `modeling_value_head.py` was confirmed against the v1.12.0→v1.13.0 tree diff (`ppo_trainer.py` −1030, `ppo_config.py` −279, `modeling_value_head.py` −1020, ~3,924 lines total including docs, examples and tests, removed in commit `700b845` on 2026-09-04); `create_reference_model` survives at `trl/models/utils.py` and is imported by `bco`, `a2po` and `online_dpo`, matching the release note. **The deprecation-window detail is not in the release note and was established from git history:** commit `f1e6377` (2025-11-13) moved PPO to `trl.experimental.ppo`, and the files are present under `trl/experimental/ppo/` at tags v1.10.0, v1.11.0 and v1.12.0. The release note also characterizes PPO as the only trainer never aligned on the input format, with near-zero recorded usage.
[^tr-48685]: huggingface/transformers PR #48685 (source id: tr-48685), commit `80a79d1`, dated 2026-09-12 from `git log`. The floor change from `huggingface-hub>=1.5.0,<2.0` to `>=1.31.0,<2.0` was confirmed in the diff (`setup.py`, `src/transformers/dependency_versions_table.py`); the remainder of the change is a mechanical `import httpx` → `from huggingface_hub.utils import httpx` rewrite. This landed after the v5.17.0 tag and is main-only as of 2026-09-14.
