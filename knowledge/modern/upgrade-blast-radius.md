---
type: Decision Rule
title: "The diff defines the upgrade blast radius; the release note does not"
description: >
  Framework removals reach you in three modes — hard failure at load, silent fallback, and silent
  semantic change — and release-note prose is a poor predictor of which one you get, sometimes
  describing a checkpoint-compatibility break as a dead-code cleanup. Audit an upgrade against your
  own checkpoint and launch-script inventory, and verify that the fix you are upgrading for is
  actually contained in the tag you are pinning.
tags: [upgrades, deprecation, migration, versioning, serving, release-engineering]
tier: modern-consensus
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
**silently ignored rather than rejected**.[^vllm-55353] The worked consequence: a deployment setting
`VLLM_MM_HASHER_ALGORITHM=sha256` for a compliance requirement falls back to blake3 without any
warning.[^vllm-55353] **A launch script or Helm chart is an unversioned interface into the engine, and
nothing validates it for you.** Enumerate the environment variables and CLI flags your deployment
actually sets, and check each against the release's removals.

**Mode 3 — silent semantic change. Configuration unchanged, behavior different.** vLLM stopped
multiplying the derived `max_model_len` by the scaling factor for `yarn`, `deepseek_yarn` and
`deepseek_llama_scaling`, treating `max_position_embeddings` as already scaled.[^vllm-56446] The
context length the engine accepts therefore changes without touching a flag, and previously accepted
long requests can now be rejected — the change's own scoping says two models move:
`Tele-AI/TeleChat3-36B-Thinking` from 131072 to 32768, and `sarvamai/sarvam-105b` from 5242880 to
131072.[^vllm-56446] The flip side is the defect being fixed: the old path let requests run past the
end of the cos/sin cache.[^vllm-56446] **Re-verify `--max-model-len` assumptions and client-side
truncation budgets as part of the upgrade, not as an incident response.**

**Do not let prose set your risk estimate — read the diff.** The activation-ordering change above is
the week's clearest case: its description reads as housekeeping ("Dead code branching", "Unused
attribute assignments") and offers no migration path, while the diff is a checkpoint-compatibility
break that prevents startup.[^vllm-54809] **Where a change's stated framing and its diff disagree, the
diff is the specification.**

**Verify containment before you pin.** A fix existing on a project's main branch does not establish
that it is in the release you are about to deploy. Of thirteen in-window vLLM changes checked with
`git merge-base --is-ancestor`, every one landed *after* the `v0.29.0` tag and was reachable only from
the `v0.29.1rc0` prerelease — so they are "pin to a prerelease or wait", not "upgrade to v0.29.0 and
you get them".[^vllm-v0290] **`git tag --contains <sha>` is the check; a changelog entry is not.**

**Budget for outright API deletions, which arrive without a deprecation window.** TRL v1.13.0 removed
`PPOTrainer`, `PPOConfig` and `modeling_value_head.py` entirely, freezing any PPO pipeline at ≤1.12
until it is ported (note `create_reference_model` survives, since BCO, A2PO and Online DPO depend on
it).[^trl-1130] And dependency floors move sharply enough to break locked environments on their own:
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
- Most examples come from one serving engine during one unusually large release cycle. The
  `transformers` dependency-floor bump and the TRL removal are independent corroboration that the
  pattern is not vLLM-specific, but a four-repository sample in a single week cannot establish a base
  rate for how often prose understates a diff. **The rule to audit is well-founded; any claim about
  frequency is not.**
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

# Relation to existing concepts

The verification stance here is the same one
[published-result reproducibility](published-result-reproducibility.md) applies to published claims,
turned toward release engineering: a vendor's description of its own change is a hypothesis about
impact, and the diff is the evidence. Mode 3 (silent semantic change) is also the mechanism behind the
re-baselining requirement in
[performance attribution discipline](performance-attribution-discipline.md).

[^vllm-54809]: vllm-project/vllm PR #54809 (source id: vllm-54809), commit `2c9d68f`, dated 2026-09-08 from `git log`. Both raise sites — `normalize_and_validate_gptq_desc_act()` for GPTQ (including via a `dynamic` per-pattern rule) and the `CompressedTensorsConfig` check for `actorder` in `{GROUP, DYNAMIC}` — were read in the diff, as was the new `get_checkpoint_weight_mapper()` discarding `.g_idx` tensors, and the quoted "Dead code branching" / "Unused attribute assignments" framing in the PR description. Carve-out stated in the diff: `desc_act=True` with `group_size == -1` is silently downgraded to `False`, since activation ordering is a no-op for channelwise; "static"/"weight" actorder remains supported, and the error text names the fix.
[^vllm-55353]: vllm-project/vllm PR #55353 (source id: vllm-55353), commit `5fe77ae`, dated 2026-09-11 from `git log`. Removal of the two environment variables, the `use_fp4_indexer_cache` config alias, the deprecated `CommonAttentionMetadata.seq_lens_cpu` / `num_computed_tokens_cpu` properties, and the ROCm `CUDA_VISIBLE_DEVICES` shim confirmed in the diff across `envs.py`, `config/{attention,cache,multimodal}.py`, `v1/attention/backend.py` and `platforms/rocm.py`. The underlying config *fields* survive as CLI/config options; only the environment-variable aliases and the deprecated properties are gone. The blake3 fallback consequence follows from the removal being a silent ignore rather than an error.
[^vllm-56446]: vllm-project/vllm PR #56446 (source id: vllm-56446), commit `c191787`, dated 2026-09-11 from `git log`. The exclusion of `yarn`/`deepseek_yarn`/`deepseek_llama_scaling` from the `scaling_factor` multiply in `_get_and_verify_max_len`, and the accompanying regression tests asserting 32768, were confirmed in the diff (`vllm/config/model.py`). The scoping claim — that only the two named models change, while DeepSeek-V3/R1, Kimi-K2, gpt-oss, A.X-K1, TeleChat3, Llama-3.1 and Qwen3 keep their derived lengths, and non-YaRN rope types are unaffected — is stated in the PR and is not independently verified here.
[^vllm-v0290]: vllm-project/vllm release v0.29.0 (source id: vllm-v0290), tag sha `98dff2a`. Date 2026-09-08 from the tag's `creatordate` via `git for-each-ref`; note the GitHub release page displays "September 9" (the page publication) and a release feed reported 2026-09-10 — the tag date is authoritative and the discrepancy is recorded in the log. The Model Runner V2 default, the quoted v0.32 removal target for V1, the ten removed architectures, the entrypoint deprecation and the PyAV removal are release-note prose; the Model Runner V2 default (#53183, `4aab2b0`, 2026-08-27) and the PyAV deprecation (#54231, `4fc943b`, 2026-08-29) were confirmed against commits. The containment finding is from `git merge-base --is-ancestor` run over thirteen in-window commits, each returning no for `v0.29.0` and yes for `v0.29.1rc0`.
[^trl-1130]: huggingface/trl release v1.13.0 (source id: trl-1130), dated 2026-09-10. The removal of `PPOTrainer`, `PPOConfig` and `modeling_value_head.py`, the survival of `create_reference_model` for BCO/A2PO/Online DPO, and the raised dependency floors are stated in the release notes.
[^tr-48685]: huggingface/transformers PR #48685 (source id: tr-48685), commit `80a79d1`, dated 2026-09-12 from `git log`. The floor change from `huggingface-hub>=1.5.0,<2.0` to `>=1.31.0,<2.0` was confirmed in the diff (`setup.py`, `src/transformers/dependency_versions_table.py`); the remainder of the change is a mechanical `import httpx` → `from huggingface_hub.utils import httpx` rewrite. This landed after the v5.17.0 tag and is main-only as of 2026-09-14.
