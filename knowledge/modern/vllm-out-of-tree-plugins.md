---
type: Architecture Pattern
title: "vLLM externalizes optional integrations into out-of-tree plugins"
description: >
  vLLM is moving optional integrations out of the main tree behind its Python
  entry-point plugin system; bitsandbytes became the first quantization method to leave,
  so `quantization="bitsandbytes"` now needs a separately installed package. Treat
  "supported by vLLM" as "supported by vLLM plus a plugin you must install".
tags: [inference, serving, vllm, plugins, packaging, quantization, bitsandbytes, migration]
tier: frontier
status: draft
stale_after: 2027-02-10
generated:
  by: expedition/weekly-2026-08-10
  at: 2026-08-10T00:00:00Z
sources:
  - id: bnb-doc
    resource: https://github.com/vllm-project/vllm/blob/main/docs/features/quantization/bnb.md
    title: "vLLM docs: BitsAndBytes"
    author: vLLM maintainers
    last_modified: 2026-08-09
  - id: bnb-commit
    resource: https://github.com/vllm-project/vllm/commit/073c510c916f385315a5366173c883781762bb9e
    title: "[Migration] Migrate bitsandbytes support to OOT plugin (#43529)"
    author: vLLM contributors
    last_modified: 2026-08-09
  - id: plugin-system
    resource: https://github.com/vllm-project/vllm/blob/main/docs/design/plugin_system.md
    title: "vLLM docs: Plugin System"
    author: vLLM maintainers
    last_modified: 2026-08-10
  - id: bnb-plugin-repo
    resource: https://github.com/vllm-project/vllm-bnb-plugin
    title: "vllm-project/vllm-bnb-plugin README"
    author: vLLM maintainers
    last_modified: 2026-08-10
  - id: bnb-plugin-pypi
    resource: https://pypi.org/pypi/vllm-bnb-plugin/json
    title: "vllm-bnb-plugin on PyPI (release history)"
    author: vLLM maintainers
    last_modified: 2026-08-10
  - id: kv-oot-commit
    resource: https://github.com/vllm-project/vllm/commit/8543522ca792de824c026e1b9e3eb51ca809550d
    title: "[KV Offload] Support out-of-tree secondary tier managers via module_path (#51007)"
    author: vLLM contributors
    last_modified: 2026-08-05
  - id: mla-oot-commit
    resource: https://github.com/vllm-project/vllm/commit/aa6138169f80863c0f4438403c2f78f64a13907c
    title: "[MLA][Attention] Add OOT MLA prefill backend registration mechanism (#43325)"
    author: vLLM contributors
    last_modified: 2026-05-26
  - id: vllm-repo
    resource: https://github.com/vllm-project/vllm
    title: "vllm-project/vllm git repository (release tags and main-branch history)"
    author: vLLM maintainers
    last_modified: 2026-08-10
---

# Pattern

**vLLM's extension point for optional integrations is the standard Python `entry_points` mechanism, and functionality is migrating outward through it.** The plugin system exists so users "can add custom features without modifying the vLLM codebase"; because distributed inference spans multiple processes, "every process created by vLLM needs to load the plugin", and discovery happens through entry-point groups — `vllm.general_plugins`, `vllm.platform_plugins`, `vllm.io_processor_plugins`, `vllm.stat_logger_plugins`, and `vllm.endpoint_plugins`.[^plugin-system] Two properties matter operationally: plugins can be filtered with the `VLLM_PLUGINS` environment variable (set it to a plugin name to load only that one), and endpoint plugins are the exception to load-by-default — they load only in the API-server front-end process and are **not loaded by default**, behind an opt-in trust model.[^plugin-system] Registration functions must be re-entrant, because they may be called more than once per process.[^plugin-system]

**The load-bearing consequence: bitsandbytes is now an out-of-tree install.** On 2026-08-09, bitsandbytes support was migrated out of the vLLM tree.[^bnb-commit] The documentation now states that "BitsAndBytes support is provided by the out-of-tree `vllm-bnb-plugin`" and instructs `uv pip install vllm-bnb-plugin` **before** using BitsAndBytes with vLLM.[^bnb-doc] The plugin registers itself through the `vllm.general_plugins` entry-point group, so `quantization="bitsandbytes"` and `load_format="bitsandbytes"` remain available once installed — in-flight 4-bit quantization, pre-quantized 4-bit and 8-bit checkpoint loading, and the bitsandbytes linear and MoE quantization methods all move with it.[^bnb-plugin-repo] The package exists on PyPI (0.0.2, uploaded 2026-08-05) and declares `vllm` and `bitsandbytes>=0.48.1` as requirements.[^bnb-plugin-pypi]

The user-facing API is otherwise unchanged: pre-quantized checkpoints are still inferred from the model's `config.json` `quantization_config` section with no explicit argument, and in-flight 4-bit still requires an explicit `quantization="bitsandbytes"` (or `--quantization bitsandbytes` on the OpenAI-compatible server).[^bnb-doc] **The migration is an install-time break, not a code-level one** — which is exactly why it is easy to miss until a deployment fails.

**This is a direction, not a one-off.** Other extension points opened out-of-tree in the same period: out-of-tree secondary-tier KV-offload managers became loadable via `module_path` on 2026-08-05,[^kv-oot-commit] and an out-of-tree MLA prefill backend registration mechanism landed on 2026-05-26.[^mla-oot-commit] The plugin documentation itself points at `bart-plugin` as an official out-of-tree *model* plugin.[^plugin-system] The planning implication: when pinning a vLLM version for a deployment, **enumerate which of your integrations live in the tree at that version**, because "vLLM supports X" is drifting toward "vLLM plus a separately versioned package supports X", each with its own release cadence.

**Version gate.** The bitsandbytes migration is on `main` only as of 2026-08-10: the doc at tags `v0.26.0`, `v0.27.0rc1`, and `v0.27.0rc2` does not mention `vllm-bnb-plugin`, and the latest release on PyPI is vLLM 0.26.0.[^vllm-repo] Builders on a released vLLM are not affected yet; builders tracking `main`, building from source, or upgrading past v0.27.0rc2 are.

**Scope note:** this concept covers packaging and deployment of a serving stack, an area no `status: stable` concept addresses; it conflicts with nothing in [foundations](../foundations/scope-boundary.md). It pairs with [online quantization](vllm-online-quantization.md), which covers the in-tree schemes that remain.

# Open questions

- Whether other quantization backends (AWQ, GPTQ, GGUF, and similar) are slated to follow bitsandbytes out of the tree is not stated in any source read here; the trend is inferred from three separate out-of-tree mechanisms plus one completed migration, not from a published roadmap.
- The vLLM doc instructs `uv pip install vllm-bnb-plugin` (the PyPI package) while the plugin's own README shows `uv pip install -e /path/to/vllm-bnb-plugin` (a local editable install). The PyPI package exists, so the doc's instruction is the one that works for consumers; the README appears to be written for contributors, but no source states this explicitly.
- No source read here states a support or maintenance guarantee for the out-of-tree plugin relative to in-tree code.

[^plugin-system]: vLLM docs, `docs/design/plugin_system.md` on `main` (source: plugin-system), read 2026-08-10. Supplies the rationale, the entry-point discovery mechanism, the five plugin group names, the `VLLM_PLUGINS` filter, the endpoint-plugins not-loaded-by-default and opt-in trust note, the re-entrancy guideline, and the `bart-plugin` reference.
[^bnb-doc]: vLLM docs, `docs/features/quantization/bnb.md` on `main` (source: bnb-doc), read 2026-08-10. Supplies the out-of-tree statement, the `uv pip install vllm-bnb-plugin` instruction, the config.json inference behavior for pre-quantized checkpoints, and the explicit `quantization="bitsandbytes"` / `--quantization bitsandbytes` requirement for in-flight 4-bit. File last modified 2026-08-09 per the repository's git history.
[^bnb-commit]: vLLM commit 073c510c (source: bnb-commit), "[Migration] Migrate bitsandbytes support to OOT plugin (#43529)", committer date 2026-08-09.
[^bnb-plugin-repo]: vllm-project/vllm-bnb-plugin README (source: bnb-plugin-repo), read 2026-08-10: entry-point group `vllm.general_plugins`; `quantization="bitsandbytes"` and `load_format="bitsandbytes"` "remain available after installation"; the listed capabilities.
[^bnb-plugin-pypi]: vllm-bnb-plugin PyPI JSON metadata (source: bnb-plugin-pypi), read 2026-08-10: version 0.0.2 uploaded 2026-08-05T09:42:50Z (0.0.1 on 2026-07-30); `requires_dist` = `vllm`, `bitsandbytes>=0.48.1`.
[^kv-oot-commit]: vLLM commit 8543522c (source: kv-oot-commit), "[KV Offload] Support out-of-tree secondary tier managers via `module_path` (#51007)", committer date 2026-08-05.
[^mla-oot-commit]: vLLM commit aa613816 (source: mla-oot-commit), "[MLA][Attention] Add OOT MLA prefill backend registration mechanism (#43325)", committer date 2026-05-26.
[^vllm-repo]: vllm-project/vllm git repository (source: vllm-repo). Checked 2026-08-10 by resolving tags `v0.26.0`, `v0.27.0rc1`, and `v0.27.0rc2` and inspecting `docs/features/quantization/bnb.md` at each: none contains the string `vllm-bnb-plugin`. Latest vllm version on PyPI at the same time: 0.26.0.
