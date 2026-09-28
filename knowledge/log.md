# Catalog update log

## 2026-09-28

* **Weekly expedition landed**: weekly-2026-09-28 — 4 draft concepts under
  [/modern/](/modern/) (eval-harness version provenance, library-upgrade silent
  behavior drift, determinism is a pipeline contract, benchmark measurement
  layer) from 22 source entries, every one a permalink pinned to a commit SHA or
  release tag and re-fetched during distillation. The week was rich in
  inference/serving and eval-tooling material and essentially empty in
  training-recipe material.
* **The skeptic pass changed the output materially — 10 MUST-FIX findings, and two
  claims were withdrawn rather than repaired.** Corrections of record: an example
  ("Paris Paris Paris Paris Paris") was attributed to a changelog that does not
  contain it and is now cited to the commit message that does; a "date
  inconsistency" this expedition had itself manufactured (a commit read in two
  timezones) was deleted as non-existent; a quoted residual "pre-scoring
  cancellation window" was removed as unfindable in the cited source; an inference
  that sub-percentage-point BBH differences are noise was withdrawn, the
  documented defect floor being ~0.05%, not ~1%; a claim that PyTorch had stopped
  building cp310 nightly wheels was withdrawn as unverifiable from this session
  (`download.pytorch.org` blocked); a Keras validation claim was narrowed from all
  label-smoothing losses to the 2 of 5 that actually call the validator; a GGUF
  "fallback is a warning" detail was removed as absent from the doc; and the Gemma
  activation item was corrected twice over — it emits `logger.warning_once` rather
  than being silent, and it **restores** a conversion dropped by #35235 rather than
  diverging from all earlier v5.x.
* **One headline claim was quote-mined and is now fixed.** The measurement-layer
  concept had paired TensorRT-LLM's 5.05x kernel geomean against its 2.9-4.5%
  serving figure to assert a ~100x dilution. The source states that the 2.9-4.5%
  is the *incremental* benefit of a prefill change on a deployment already running
  V2 decode, and separately reports 6-19% lower time per output token for decode —
  which this expedition had omitted. The concept now uses the post's own framing
  ("the serving benefit depends on Top-K's share of total execution time") and the
  fixed-ratio claim is recorded as withdrawn inside the draft. Similarly, an NVFP4
  TTFT quote had dropped its "at matched concurrency" condition, under which the
  draft's conclusion was false: the same post reports TTFT *decreasing* 0.74-10.72%
  under capacity-driven load, and iso-capacity decode gains of 37-78% against the
  26-30% iso-concurrency figure originally quoted alone. That concept was
  rewritten around the load regime as a result.
* **Method improvement worth keeping**: `github.com` commit/blob pages and
  `api.github.com` are refused for this session, but anonymous
  `git fetch --depth 1 --filter=blob:none origin <sha>` **is** served, which
  recovers commit subjects and dates. Where a claim needed a before-state, the
  stronger technique proved to be fetching the same file at the previous **release
  tag** via `raw.githubusercontent.com` and comparing — a blob-filtered shallow
  fetch cannot produce a true diff, since parent blobs are absent. That is how the
  `conv` remap removal, the inverted vLLM FP8 default, and the fact that
  `use_rand4x` never shipped in a stable release were each established.
* One conflict with a stable concept recorded, not resolved: the determinism draft
  reaches into reinforcement learning, which the stable
  [scope boundary](/foundations/scope-boundary.md) lists as uncovered. RL
  methodology remains OUT-OF-SCOPE; the draft covers only the numerical
  reproducibility of the stack beneath such a loop.
  [Scope boundary](/foundations/scope-boundary.md) draft-coverage section updated.
* **Sweep coverage was partial, again, and for the same reason as 2026-08-17**: the
  session's network egress policy blocked `arxiv.org`, `huggingface.co`,
  `pytorch.org` and `blog.vllm.ai` outright (403 on CONNECT), and the
  Anthropic-side fetch tool is blocked for those hosts too. **The arXiv source
  class named in the weekly playbook could therefore not be swept at all**, and no
  mirror or rehost was used to work around the denial. Lab-blog coverage survived
  only because those blogs publish from public GitHub repositories, which
  anonymous git reads and `raw.githubusercontent.com` do serve. Recorded so a thin
  paper section is not mistaken for a quiet week in the literature. Also
  unswept for want of clone budget: jax, triton, llama.cpp, axolotl, peft,
  accelerate.
* Leads carried forward for next week: an async GRPO + LoRA training recipe
  published 2026-09-14 (just outside this window); a GEM-proceedings systematic
  review of contamination detection on ACL Anthology, which is *not* blocked and
  was simply not reached; and an in-window HLE eval change in inspect_evals
  (configurable metrics, changed default subset) read only at commit-title depth.

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
