# OKF Knowledge Catalog for dl-model-advisor — Design

Date: 2026-08-03 · Author: Antony Zaki with Claude · Status: validated in
brainstorm, ready for implementation

## Goal

Evolve dl-model-advisor from a fixed 2021 book advisor into the reasoning
front-end of a growing knowledge catalog. Multi-agent research expeditions
continuously add current techniques — papers, repositories, Hugging Face
models, and qlib as the first commissioned domain — while every
recommendation stays cited, tiered, and verifiable. The catalog uses the
Open Knowledge Format (OKF v0.2, GoogleCloudPlatform/knowledge-catalog).

The design preserves the property that made v1 trustworthy: the advisor
never states ungrounded guidance as fact. The knowledge boundary no longer
sits at 2021; it sits at the catalog's edge and moves outward with each
verified expedition.

## Architecture: three layers

```
knowledge/                      LAYER 1 — the OKF bundle (grows daily)
  index.md                        okf_version "0.2"; catalog map
  log.md                          population history, newest first
  foundations/                    book-canon concepts (seeded from v1)
  modern/                         2022–2026 techniques (expedition output)
  domains/quant-finance/          qlib module — expedition #1
dl-model-advisor/               LAYER 2 — the plugin (stays small)
evals/ + evals-holdout/         LAYER 3 — the trust machinery (suite v2)
```

The catalog holds knowledge and provenance. The plugin holds judgment: the
routing procedure, the plan format, the enforcement hook. The evals hold
proof. Knowledge changes never require plugin releases: the skill reads
`knowledge/` from the workspace when present and falls back to a frozen
snapshot of `foundations/` embedded in the plugin at release time — the
same build-time distillation discipline as v1, now with OKF provenance.

## Catalog schema

Four concept `type` values, each a `.md` file whose bundle path is its ID:

| Type | Content | Example |
|---|---|---|
| Decision Rule | one routing rule; custom fields `applies_to`, `rule`, `tier` | `foundations/text-ratio-rule` |
| Architecture Pattern | canonical code pattern with runnable snippet | `foundations/pretrained-feature-extraction` |
| Task Pairing | one ch6 table row; `data/pairings.json` is generated from these | `foundations/pairing-multilabel` |
| Scope Boundary | what the catalog knowingly does not cover | `foundations/scope-boundary` |

Trust conventions per concept:

```yaml
sources: [{id: dlwp2e-ch11, resource: <anchor>, author: F. Chollet, last_modified: 2021-10-03}]
generated: {by: expedition/<topic>-<date>, at: <ISO-8601>}
verified:
  - {by: process:forge-eval-capability-v2, at: ...}   # machine-confirmed
  - {by: human:antony, at: ...}                       # human-reviewed
status: draft | stable | deprecated
stale_after: YYYY-MM-DD    # mandatory in modern/ (+12 months default,
                           # +6 for benchmark-derived claims)
```

Trust tiers follow OKF: no `verified` → unverified; `process:` actors only
→ machine-confirmed; any `human:` actor → human-reviewed. Admission is
cheap — drafts enter freely; authority stays human — only human-reviewed
concepts earn confident, unhedged advice.

Seed inventory (converted from validated v1 content): 4 Task Pairings,
5 Decision Rules (modality map, ratio rule, image size-ladder,
protocol-by-size, universal workflow), 5 Architecture Patterns, 1 Scope
Boundary — all `stable`, sourced to book chapters, `verified` by the green
suite run and Antony's approval.

## Plugin v2

Routing flow per request: scope gate → extract facts → load matching
Decision Rule and Architecture Pattern concepts → emit plan. SKILL.md keeps
a compact fallback routing table for compaction survival and missing
bundles; when the catalog is readable, the catalog wins.

The scope gate becomes dynamic: "out of scope" means no stable concept
covers the ask. A draft-only match produces advice with its tier stated,
not a refusal. The canonical OUT-OF-SCOPE line survives for uncovered asks.

Two canonical plan lines change or appear:

```
Cited rule: DLwP-2E ch11 — ratio rule [foundations/text-ratio-rule]
Evidence: human-reviewed | machine-confirmed | unverified (+ stale flag)
```

The citation line keeps the old `DLwP-2E ch` prefix for book-grounded
advice, so all 30 existing graders pass unchanged; concept IDs ride in
brackets. Modern concepts cite their own sources
(`arXiv:2106.09685 — LoRA [modern/lora-peft]`).

`lint_outputs.py` gains three checks: the cited concept exists; the
Evidence line matches the concept's actual trust tier (no self-promotion);
pairing validation reads a `pairings.json` generated from Task Pairing
concepts, drift-checked byte-for-byte. Headless behavior, the
narrow-question rule, starter-code discipline, and the full-request rule
carry over unchanged.

## Research pipeline: expeditions

Knowledge enters through commissioned multi-agent expeditions, one topic
each. Shape (3–5 teammates + lead):

1. **Scouts** (parallel, per source class): paper-scout, repo-scout,
   hub-scout. Every claim returns with a URL and date.
2. **Distiller**: converts findings into draft concepts — decision rules
   first. Sets `status: draft`, full `sources`, mandatory `stale_after`.
3. **Skeptic**: adversarially refutes each draft; conflicts with stable
   concepts are recorded in the draft, never silently resolved.
4. **Eval-drafter**: any concept that could change a recommendation ships
   1–2 draft eval tasks (unverifiable → unbuildable, extended to knowledge).
5. **Lead**: merges survivors, appends the `log.md` entry, and emits a
   one-screen digest: concepts, sources, conflicts, evals.

Trust flow: draft (usable at `Evidence: unverified`) → eval tasks pass →
`process:` verification (machine-confirmed) → digest review adds
`human:antony` → stable. Cadence: manual commissions first (qlib is
expedition #1); a scheduled scouting routine later, once digest quality
earns it.

## Evals and failure modes

**The suite freezes; the catalog flows.** `knowledge/` stays outside the
freeze hash. A catalog-integrity class of cheap `launch: none` regression
tasks bridges the two:

- CI-01 OKF conformance (frontmatter parses; `type` present)
- CI-02 provenance (every stable concept has ≥1 `sources[].resource`)
- CI-03 drift (`pairings.json` byte-matches regeneration from concepts)
- CI-04 freshness (no stable concept past `stale_after` without a flag)
- CI-05 no self-promotion (Evidence lines match actual trust tiers)

Suite re-arms as v2 because tasks are added; T01–T24 and the holdout stay
untouched. Failure modes: missing bundle → embedded snapshot, disclosed;
nonexistent cited concept → lint blocks; draft conflicts with stable →
stable wins, disclosed in Scope notes; broken OKF cross-links → tolerated
per spec, warned by CI, never fatal.

## Implementation plan

1. **Seed the catalog** — convert the 15 validated concepts; write
   `index.md`, `log.md`; generate `pairings.json` from concepts; CI tasks.
2. **Plugin v2 + suite v2** — skill routing through the bundle; lint hook
   checks; new eval tasks; re-arm (reference, red for new tasks, freeze).
3. **Expedition #1: qlib** — commission the quant-finance module; run the
   full expedition shape as a multi-agent workflow; digest for review.

Prerequisite: `git init` (also required by forge-build), with a
`.gitignore` excluding the book files, `runs/`, and build logs.

## Open questions

- Where the catalog eventually lives (in-repo vs its own repository with
  the plugin consuming it as a submodule or release artifact).
- Whether expedition scouting graduates to a scheduled routine, and how
  often.
- EPUB anchor format for book `sources[].resource` entries (page anchors
  vs chapter files).
