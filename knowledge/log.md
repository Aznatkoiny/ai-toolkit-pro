# Catalog update log

## 2026-08-31

* **Weekly expedition landed**: weekly-2026-08-31 — 3 draft concepts under
  [/modern/](/modern/) (hardware-gated serving defaults, quantization calibration
  silent no-op, benchmark score as a selection signal) from 11 primary sources
  dated 2026-08-03 to 2026-08-28. All version, tag-containment and source-text
  claims were verified against git objects rather than release notes.
  [Scope boundary](/foundations/scope-boundary.md) draft-coverage section updated.
* **The skeptic pass changed the substance of two drafts, not just their wording.**
  It falsified three assertions, each of the same kind — a claim that a source said
  *nothing* about something: (a) a draft stated that vLLM's `v0.19` never shipped,
  when `v0.19.0` shipped 2026-04-02 carrying both the deprecated option and its own
  removal notice; (b) a draft stated that the Blackwell CUDA-graph change carried no
  measured speedup, when PR #49390 carries a throughput table and the capture-cost
  figures the draft had presented as its own inference; (c) a draft stated that no
  source quantified the GPTQ/AWQ calibration defect, when the cited commit body
  contains four benchmark tables — including the finding that the previously
  *published* Keras GPTQ perplexity numbers were round-to-nearest numbers. Root
  cause in every case: reading a squashed `git log` message or a diff and inferring
  absence, when the evidence lived in the PR description or further down the commit
  body. **Absence-of-evidence sentences are the highest-risk claims a draft can
  carry and must be verified against the rendered PR or full commit body.**
* The pass also corrected an undercount (four SGLang `EnvBool` defaults flip
  `False → True` between v0.5.17 and v0.5.18, not two — material because the draft's
  remediation advice is to reset them all), removed an unsourced "widely-repeated"
  framing, narrowed the third draft's `applies_to` to match its ASR-only evidence,
  and fixed two source titles and an author attribution. A `# Conflict with a stable
  concept` section was added to each draft; the sharpest is that
  [scope boundary](/foundations/scope-boundary.md) states "Inference deployment more
  broadly remains uncovered", which the serving-defaults draft speaks to directly.
  Conflicts are recorded in the drafts, not resolved.
* One correction the expedition made against its own scouts: a scout reported that
  vLLM v0.28.0 also raises `max_num_seqs` on ≥160 GiB devices. It does not — the
  value is 1024 in both the new tier and the pre-existing ≥70 GiB tier, verified in
  the tree at both tags.
* **Sweep coverage was again partial, and in the same direction as 2026-08-17.** The
  egress proxy blocked `arxiv.org`, `export.arxiv.org`, `huggingface.co`,
  `pytorch.org`, `blog.vllm.ai`, `ar5iv` and `semanticscholar.org`; `api.github.com`
  and plain `curl` to `github.com` return 403. **The arXiv/paper source class named
  in the playbook was therefore unreachable by any route**, and no paper was swept.
  What did work: plain `git` over the proxy against public repositories (the primary
  method used here), and WebFetch on `github.com` / `raw.githubusercontent.com`. Lab
  blogs were read as markdown from their source repositories instead of their
  websites.
* **A standing-task correction for future runs:** `pytorch/pytorch.github.io` no
  longer carries the PyTorch blog — `_posts/` was deleted 2025-08-08 and the README
  states the repository "is NOT the source of truth for the PyTorch website". With
  `pytorch.org` proxy-blocked, PyTorch blog coverage is currently unreachable by any
  route from this environment. Finding the new site's source repository is an open
  item.
* **Noted, not distilled:** `microsoft/qlib`, which backs the
  [quant-finance](/domains/quant-finance/) module, had zero commits to `main` in the
  window and none since 2026-07-23; its last release `v0.9.7` is dated 2025-08-15,
  over twelve months old. No API or workflow break occurred, so no migration work is
  due and no concept was minted. Recorded as a maintenance signal: pin qlib rather
  than tracking `main`, and expect to carry fixes as local patches. "Low commit
  volume" is what was measured; "unmaintained" is not asserted.
* **Superseded by events:** the availability gate in
  [speculative-decoding concurrency](/modern/speculative-decoding-concurrency.md)
  states that, as of 2026-08-17, vLLM's DSpark adaptive verification was
  release-candidate/`main` only. That statement was correct on its date and is left
  unedited, but commit `7f7a32c` is now contained in stable tag `v0.28.0`
  (published 2026-08-26), so the gate no longer binds.

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
