# dl-model-advisor

Book-grounded deep-learning model selection for AI scientists' coding
agents. Give it your problem — data modality, task type, dataset size — and
it routes you to the architecture, loss/activation pairing, evaluation
protocol, and workflow that *Deep Learning with Python, 2nd Edition*
(Chollet, 2021) selects, instead of defaulting to the fanciest model.

**Deliverables per request:** `MODEL_PLAN.md` (structured plan with the
governing rule cited by chapter) and `starter_model.py` (runnable Keras 3
scaffold, syntax-verified). Narrow questions ("which loss for multilabel?")
are answered inline with no files.

## Install

```
claude plugin marketplace add <this-repo>
claude plugin install dl-model-advisor@<marketplace>
```

Cloud / CI / team distribution (personal skills never load there — this
plugin must be repo-declared): commit to `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "<marketplace>": {"source": {"source": "github", "repo": "<org>/<repo>"}}
  },
  "enabledPlugins": {"dl-model-advisor@<marketplace>": true}
}
```

## Usage

- `/dl-model-advisor:advise 2,400 labeled product photos, 8 classes — what
  should I build?` — or just describe your problem naturally; the skill
  auto-triggers on model-selection questions.
- Out-of-scope requests (LLM fine-tuning, diffusion, RL, GNNs, recommenders)
  get an explicit boundary statement, not a force-fitted 2021 recipe — the
  book predates those techniques.

## Permissions

Add once to avoid re-prompts on multi-turn sessions (the skill verifies
starter code with `py_compile`):

```json
{"permissions": {"allow": ["Bash(python3 -m py_compile *)"]}}
```

No network access, no paid APIs, no writes outside your project workspace.

## Enforcement

A skill-lifecycle PostToolUse hook (`skills/advise/scripts/lint_outputs.py`)
mechanically validates every write to `MODEL_PLAN.md` (required sections;
loss/activation pairing checked against `skills/advise/data/pairings.json`,
the book's ch6 table) and `starter_model.py` (compiles; imports restricted
to keras/tensorflow/numpy/stdlib). If hooks are disabled by org policy — or
in environments where skill-frontmatter hooks do not register (observed in
headless `-p` sessions on some CLI versions) — the plugin degrades to
advisory-only guidance; the eval suite that gated this plugin's build is the
backstop that validated the shipped content, and its T18 fixture pipes test
the lint script directly.

## Notes

- Starter code is emitted in Keras 3 idiom (`import keras`); the book's
  notebooks are TF/Keras 2.x-era — patterns were modernized at build time.
  It is a scaffold: adapt data loading to your environment before training.
- Minimum Claude Code version: 2.1.218.
- Knowledge is fully self-contained (distilled from the book at build time);
  the plugin makes no runtime network calls.
- Evals: the generating project carries a 24-task frozen suite plus a 6-task
  holdout tranche (see `evals/` there); this plugin's behavior contract is
  that suite.
