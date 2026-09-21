# Catalog update log

## 2026-09-21

* **Weekly expedition landed**: weekly-2026-09-21 — 4 draft concepts (3 under
  [/modern/](/modern/), 1 under [/domains/quant-finance/](/domains/quant-finance/))
  from 14 primary sources dated 2026-05-29 through 2026-09-20, plus tag/ancestry
  checks re-derived on 2026-09-21. New concepts: release-containment discipline,
  serving-benchmark measurement windows, adapter target-matching, and qlib
  dependency pinning. All four are `frontier`; none reached `modern-consensus`.
  [Scope boundary](/foundations/scope-boundary.md) draft-coverage section updated.
* **The skeptic pass changed substantive content in all four drafts**, and two
  corrections were material rather than cosmetic:
  - *qlib dependency pinning* asserted that MLflow 3.13 **silently** disables the
    filesystem tracking backend. It does not — MLflow's changelog and
    `FileStore.__init__` show it **raises** by default. The diagnosis, the urgency
    framing, and a debugging tip describing a symptom that does not occur were all
    rewritten, and two documented remedies the draft had missed
    (`MLFLOW_ALLOW_FILE_STORE=true`, `mlflow migrate-filestore`) were added. The
    draft had excused not checking MLflow on the grounds that its notes were
    unreachable; that excuse was false. A skeptic note inside the concept records
    the correction rather than hiding it.
  - *adapter target-matching* carried an **unsourced** claim — a "canonical DINOv2
    LoRA recipe" of `["query","key","value"]` — which was both a hard-rule
    violation and the wrong string; PEFT's own docs ship `["query","value"]`. The
    claim was the sentence that made the concept actionable, so it was replaced
    with a sourced equivalent rather than deleted. Its title also overstated the
    hazard: the silent no-op required a **non-first** adapter.
  - *release-containment discipline* was downgraded from `modern-consensus` to
    `frontier`: no cited source states the rule (all are primary artifacts), and
    the five instances are not independent — two vLLM, two Hugging Face, and the
    TRL post itself runs on transformers and vLLM.
  - *serving-benchmark measurement windows* had a factual error (`rampup` does not
    move `measure_start`; only `warmup` does) and two quotes attributed to the
    documentation that live in the PR commit message and a code comment.
* **Sweep coverage was partial, for the second expedition running**: the session's
  network egress policy again blocked `arxiv.org` and `huggingface.co` outright,
  so the arXiv and Hugging Face daily-papers/model-card source classes named in the
  weekly playbook could not be swept. Findings come from the reachable classes —
  GitHub release and tag history, load-bearing repository commits, project blogs
  authored in public GitHub repos, and PyPI metadata. **Note for future expeditions:
  `raw.githubusercontent.com`, `pypi.org` and `git ls-remote`/blobless clones are all
  reachable, and the skeptic pass showed that at least one "unreachable" claim in a
  draft was simply unchecked.** Verify the channel before recording a coverage gap.
* **Deferred, not dropped**: three further candidates met the tactical lens but were
  held to keep the PR honest rather than padded — async-GRPO training defaults
  (3.9x wall-clock from three config changes; single-source, and the post cites a
  TRL version that does not exist), SGLang v0.5.20's CUDA 12 retirement and deleted
  backends, and the Chord W4A16 MoE kernels for Kimi K2.x. Candidates for
  2026-09-28. Verified groundwork on the SGLang one, recorded so it need not be
  re-derived: at tag `v0.5.20` (`94602c9c`) a whole-tree `git grep cutlass_mla`
  returns **zero** hits, against ten files at `v0.5.19` (`0bcd8223`) including the
  CUDA source and its build/binding entries — so out-of-tree code calling
  `sgl_kernel`'s `cutlass_mla` op loses the symbol, not just the
  `--attention-backend` choice. And `SGLANG_DISAGGREGATION_SAMPLING_MASK_MAX_TOKENS`
  is retained at `v0.5.20` solely as a startup tripwire
  (`srt/environ.py`: *"Retained only to reject the removed setting during startup"*),
  so prefill/decode deployments carrying it **fail to boot by design** — the variable
  must leave the manifests before the image bump, not after.

## 2026-08-17

* **Weekly expedition landed**: weekly-2026-08-17 — 3 draft concepts under
  [/modern/](/modern/) (published-result reproducibility, speculative-decoding
  concurrency dependence, open-weight model-selection signals) from 3 primary
  sources dated 2026-08-13/14/16 plus one repository-tag check. Skeptic pass
  corrected two overstatements (an organizer self-characterization stated as
  fact; a checkpoint-specific KV-dtype requirement generalized too far) and
  recorded one conflict with the stable
  [scope boundary](/foundations/scope-boundary.md) inside the affected draft.
  Two internal contradictions in cited sources are flagged, not resolved.
  [Scope boundary](/foundations/scope-boundary.md) draft-coverage section
  updated.
* **Sweep coverage was partial**: the session's network egress policy blocked
  `arxiv.org` and `huggingface.co` outright, so the arXiv and Hugging Face
  model-card/daily-papers source classes named in the weekly playbook could not
  be swept. Findings come from the reachable classes only — lab engineering
  blogs whose sources live in GitHub repositories, and load-bearing repository
  history. Recorded here so the gap is not mistaken for a quiet week.

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
