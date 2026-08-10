# Catalog update log

## 2026-08-10

* **Expedition landed**: weekly-2026-08-10 — 2 draft concepts under
  [/modern/](/modern/), both on LLM serving with vLLM: online (load-time)
  quantization, and the migration of optional integrations to out-of-tree
  plugins. A deliberately small week: the sweep found little else meeting
  the tactical bar, and nothing was added to pad the count.
* **Sweep was degraded and the drafts reflect it.** This environment's
  egress proxy blocks huggingface.co, arxiv.org, pytorch.org, and the lab
  engineering blogs, so the paper/hub source classes in the playbook could
  not be read at all. Evidence was gathered only where primary sources were
  reachable — `raw.githubusercontent.com`, git history of public repos, and
  pypi.org — which is why both concepts come from one project. Candidates
  surfaced by web search but unreadable at source (the 2026-08-07 vLLM
  decode-context-parallelism post, Qwen3.8-Max open weights, arXiv
  2607.27919) were dropped rather than cited second-hand.
* **Skeptic pass**: every quoted claim in both drafts re-checked against a
  fresh fetch of its source. Two overstatements caught and corrected: both
  changes were initially written as current vLLM behavior, but neither is
  in any release — the docs at tags v0.26.0, v0.27.0rc1, and v0.27.0rc2
  carry neither, and PyPI's latest vllm is 0.26.0 — so both drafts now
  carry an explicit version gate. One paraphrase tightened to the source's
  own wording. No conflict with any `status: stable` concept.
* **Dropped after source-checking**: a candidate concept on vLLM's
  `reasoning_content` → `reasoning` rename. The week's commit (#50624,
  2026-08-03) only *documented* the silent-empty-read failure mode; the
  rename itself already shipped in v0.26.0, so it is not this week's
  development.
* [Scope boundary](/foundations/scope-boundary.md) draft-coverage section
  revised to record LLM inference/serving as newly draft-covered.

## 2026-08-03

* **Expedition landed**: qlib-2026-08-03 — 6 draft concepts (4 under
  [/domains/quant-finance/](/domains/quant-finance/), 2 under
  [/modern/](/modern/)) from 71 sourced claims by 3 scouts; all 6 revised
  by adversarial skeptics (misquotes, overstated claims, and stale source
  metadata corrected against live sources); 10 draft eval-task specs saved
  to docs/plans for suite v2. Lead curation: one concept retyped away from
  Task Pairing (reserved for ch6 rows);
  [scope boundary](/foundations/scope-boundary.md) revised to record draft
  coverage.

* **Initialization**: Seeded 15 foundation concepts from the
  suite-validated dl-model-advisor v1 content (4 Task Pairings, 5 Decision
  Rules, 5 Architecture Patterns, 1 Scope Boundary). All
  machine-confirmed by process:forge-eval-capability-v1 (bare 0/20 →
  plugin 20/20, 2026-08-02); human review pending — see
  [index](/index.md).
* **Commissioned**: expedition #1 — quant-finance module distilled from
  [microsoft/qlib](https://github.com/microsoft/qlib).
