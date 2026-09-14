# Catalog update log

## 2026-09-14

* **Weekly expedition landed**: weekly-2026-09-14 — 4 draft concepts under
  [/modern/](/modern/) (sharded-training silent correctness, performance-attribution
  discipline, agentic-serving routing, upgrade blast radius) from 17 primary sources
  dated 2026-09-07/08/09/10/11/12, all verified against git metadata or read diffs.
  [Scope boundary](/foundations/scope-boundary.md) draft-coverage section updated.
* **The skeptic pass changed the tier of every concept.** All four drafts were
  submitted at `modern-consensus` or `frontier` and all four landed at `frontier`.
  The recurring cause: source counts overstated source independence. In
  sharded-training silent correctness, three of four `transformers` sources share a
  single author working one expert-/context-parallelism workstream; in
  performance-attribution discipline, four of six claim-pillars rest on a single
  vendor blog post.
* **Two drafts had a central claim falsified and rewritten, not quietly dropped**:
  - *performance-attribution-discipline* asserted that a QuickReduce kernel "never
    ran", where the source says only that its logs prove the kernel was *configured*,
    not that it ran. A concept about not asserting unverified execution had asserted
    unverified non-execution. Also corrected: the attribution was withdrawn in a
    pre-publication audit, not publicly retracted, and was found in a pinned
    threshold table rather than by dispatch tracing.
  - *upgrade-blast-radius* was built on the thesis that release-note prose
    systematically undersells the diff. **Both examples failed verification** — the
    vLLM activation-ordering PR does disclose the removal and the checkpoint-format
    change in its opening line, and TRL's PPO removal had a roughly ten-month
    `trl/experimental/` window the release note omitted. The thesis was withdrawn and
    the concept re-centred on release containment and a three-mode removal taxonomy.
    The drafting error is recorded inside the concept because it is an instance of
    the failure the concept describes.
* **Source self-contradictions flagged, not resolved**: the vLLM YaRN change states
  in one line that only `sarvam-105b` changes while its Purpose section and its added
  regression tests both move `TeleChat3-36B-Thinking` from 131072 to 32768. The tests
  are treated as authoritative and the contradiction is recorded in the draft.
* **Release dates proved unreliable in three different ways this week** and are now
  treated as claims requiring verification. vLLM v0.29.0: the git tag reads
  2026-09-08, the GitHub release page displays "September 9", and the releases Atom
  feed reported 2026-09-10. transformers v5.17.0: git tag 2026-09-09 against an Atom
  feed reading 2026-09-10. Git tag `creatordate` was taken as authoritative
  throughout. Separately, **tag date does not imply containment**: `v0.29.0` and
  `v0.29.1rc0` are divergent branches whose merge base is 2026-08-31, so thirteen
  in-window commits merged *before* the v0.29.0 tag date are absent from it.
* **Sweep coverage was partial, for the second consecutive expedition.** The session's
  network egress policy blocked `arxiv.org`, `huggingface.co`, `pytorch.org`,
  `blog.vllm.ai` and the major lab domains outright. Reachable classes were
  `github.com` (via fetch and the git protocol) and server-side web search. The arXiv
  and Hugging Face source classes named in the playbook could not be swept directly,
  so **no paper-derived concept appears in this expedition** — that is an access
  limitation, not a quiet week in research. A workaround that did hold: framework
  engineering blogs were read from their GitHub source repositories.
  `pytorch/pytorch.github.io` is no longer usable this way — it now carries a notice
  that it is not the source of truth for the PyTorch website, and no public
  replacement source was found, so "PyTorch published nothing this week" is
  **unverified** rather than established.
* **Quiet where it was genuinely quiet**: `microsoft/qlib` had zero commits in the
  window and its newest tag, `v0.9.7`, predates it by more than a year; `keras` had no
  release and one main-branch breaking change. TensorRT-LLM, MLC and the SGLang site
  were verified quiet against real git history.

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
