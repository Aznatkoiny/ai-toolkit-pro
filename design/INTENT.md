# INTENT — dl-model-advisor

## 1. Idea

A plugin that equips AI scientists' coding agents with deep-learning model-building judgement from Deep Learning with Python 2E — routing them from problem description (data modality, task type, dataset size) to the right architecture, loss/activation pairing, evaluation protocol, and workflow, grounded in the book's decision rules. (User's words, typos corrected.) The plugin should help scientists *decide what makes the most sense for their problem* — not default to the fanciest model. Knowledge is distilled at plugin build time from the book's EPUB (decision prose, incl. ch6 "The universal workflow of ML" and ch14 "Key network architectures") and the 21 companion notebooks (canonical runnable Keras code patterns); the shipped plugin is fully self-contained.

## 2. Runtime environment

- Targets: all three — local interactive, CI/headless (`claude -p`), cloud/scheduled routines.
- Consequences: distribution must be repo-declarable (plugin install / marketplace; never personal-skills-only). Core path must work headless: no OAuth, no `requiresUserInteraction` tools, no reliance on workflows/ultracode firing. Hook use (if any) must be non-essential or degrade gracefully. Forked skills run synchronously under `-p`.
- Org policies: none — personal setups (recorded; if org-managed machines appear later, `disableSkillShellExecution` fallbacks become relevant).
- Claude Code version floor: ≥2.1.218 (latest; skill stacking, background-default forks, worktree resume all available).

## 3. External systems

| System | Access | Auth | Evals: live/mock | Mock-rot risk |
|--------|--------|------|------------------|---------------|
| none at runtime (fully self-contained) | — | — | — | — |
| Book EPUB + notebooks in this repo (BUILD-TIME ONLY corpus) | read | none (local files) | n/a — distilled into bundled refs before ship | Book is static (2021), so no content drift; the real rot is **Keras API drift** (book code is TF/Keras 2.x-era; modern installs get Keras 3). Maintainer (Antony) refreshes bundled code patterns. |

## 4. Deliverables

- Model plan — `MODEL_PLAN.md` in the scientist's project (path overridable) — structured markdown: problem framing, recommended architecture family + why (cited decision rule), last-layer activation + loss pairing, metrics, evaluation protocol, common-sense baseline, universal-workflow steps (beat baseline → overfit → regularize/tune), and explicit scope notes — consumed by the scientist and by their coding agent as a build spec.
- Starter code — `starter_model.py` in the scientist's project (path overridable) — runnable Keras scaffold implementing the recommended architecture, compiled with the planned loss/metrics, derived from the book's notebook patterns — consumed by the scientist's coding agent as the implementation seed.

## 5. Side-effect & consent inventory

| Action | Risk tier | Consent |
|--------|-----------|---------|
| Write `MODEL_PLAN.md` / `starter_model.py` inside the user's project workspace | write (workspace-local) | auto-allow |
| Network calls at runtime | none | n/a — never |
| Paid API calls, messaging, deletions, VCS pushes, long-running compute | none | n/a — never |

No side effects beyond workspace file writes → entry skills may be default-invocable; no `disable-model-invocation` needed for safety.

## 6. Success criteria (goal-condition grammar)

- SC1 — Architecture routing: given a problem description stating modality, task type, and dataset size, `MODEL_PLAN.md` exists and recommends the architecture family matching the book's decision rules (ch14 modality→architecture map; ch11 ratio rule; ch8 transfer-learning-by-dataset-size; ch10 timeseries guidance) (proof: workspace grader on plan structure + LLM judge against the distilled rule set), never recommending a sequence model for text when `samples / mean_words_per_sample < 1500` and never omitting a common-sense baseline, within 15 turns.
- SC2 — Loss/activation pairing: `MODEL_PLAN.md` contains a last-layer activation + loss pairing exactly matching the ch6 table for the stated task type (binary→sigmoid+binary_crossentropy; multiclass single-label→softmax+categorical_crossentropy; multilabel→sigmoid+binary_crossentropy; scalar regression→none+mse) (proof: workspace grader, structured-field check), never emitting a mismatched pairing, within 15 turns.
- SC3 — Evaluation protocol & workflow: `MODEL_PLAN.md` specifies an evaluation protocol chosen by dataset size (holdout / K-fold / iterated K-fold per ch5), names a concrete common-sense baseline, and lays out the universal-workflow steps in order (proof: workspace grader + judge), never proposing tuning before a baseline is beaten, within 15 turns.
- SC4 — Runnable starter code: `starter_model.py` exists, passes `python3 -m py_compile`, and structurally matches the plan (imports keras, builds the recommended layer family, `compile()` uses the planned loss) (proof: state_check running py_compile + workspace grep), never importing packages beyond keras/tensorflow/numpy stdlib, within 15 turns.
- SC5 — Scope honesty: for problems outside the book's coverage (LLM fine-tuning, diffusion models, RL, GNNs, recommenders), the response explicitly flags the boundary and does not force-fit a 2021 recipe; any partial recommendation is labeled as adjacent-best-effort (proof: transcript judge), never presenting out-of-scope guidance as book-grounded, within 10 turns.
- SC6 — Trigger discipline: the advisor triggers on model-selection requests and does not trigger on adjacent-but-different requests (env debugging, deployment, general Keras API questions) (proof: trigger-suite tasks, should/should-not sets below).

## 7. Trigger seeds

- Should trigger:
  - "What model should I use for classifying these 8,000 product images?"
  - "Help me pick an architecture for my time-series forecasting problem"
  - "I have 2,000 labeled support tickets — should I fine-tune a transformer or use something simpler?"
  - "Set up a deep learning model plan for my tabular churn data"
  - "Which loss function and last-layer activation for multi-label classification?"
- Should NOT trigger:
  - "Fix my CUDA/cuDNN installation"
  - "Deploy my trained model behind a REST API"
  - "Why does model.fit throw a shape error?" (debugging an existing model, not selecting one)

## 8. Cost posture

- Suite size tolerance: ~24 tasks; unattended ceiling: --max-cost-usd 25

## 9. Open questions

- Keras 2 vs Keras 3 idiom for starter code: book notebooks are TF/Keras 2.x-era; contract phase must pick the emitted idiom (recommend Keras 3-compatible `import keras` style with a compatibility note) and record it as a bundled-content maintenance rule.
- Whether distilled reference content constitutes "domain claims" warranting the skill-forge research-grounding offer at contract time (the source is a single authoritative book; grounding = faithful distillation, to be verified against the EPUB during evals).
