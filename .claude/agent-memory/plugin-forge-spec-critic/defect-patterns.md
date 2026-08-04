---
name: defect-patterns
description: Recurring contract/eval defect classes seen in forge runs — re-check each one on every audit
metadata:
  type: project
---

Defect patterns observed in prior forge audits. Re-check every one against each new draft.

- **Grader-truth-in-plugin**: fixtures/graders import expectations from a builder-mutable plugin file (Audit 9). Example: dl-model-advisor CONTRACT CAP-2 C6, eval fixtures importing `pairings.json` (2026-08-02).
- **Full-enumeration-no-holdout**: contract lists the entire task budget in C5 with "generates exactly" freeze language, leaving nothing for `evals-holdout/` (Audit 9). Example: dl-model-advisor CONTRACT §2/§7 (2026-08-02).
- **Judge-only capability row**: judgment/honesty capabilities graded by judge alone, no second deterministic signal (Audit 9). Example: dl-model-advisor CAP-5 C5 (2026-08-02).
- **Unresolved "correction:" artifacts / phantom floors**: contract self-corrects mid-cell and claims a version floor for a feature the final design does not use; floors for actually-used features (e.g. skill-lifecycle `hooks:` frontmatter) missing (Audit 7 / L3). Example: dl-model-advisor CAP-4 C3, §1 (2026-08-02).
- **Missing build-guard seeding statement**: contract never says who seeds `.forge/state.json` (phase=building) + `freeze.json` into the build worktree or that the freeze guard covers Bash (L2). Example: dl-model-advisor CONTRACT (2026-08-02).
- **Cross-task workspace dependency**: a task spec grades other tasks' workspaces, impossible under isolated-workspace harnesses (Audit 1/10). Example: dl-model-advisor T17 (2026-08-02).
- **Run-workspace-inside-project-tree**: harness stages trial workspaces under `runs/` inside the repo while read tools are path-unscoped, so `tasks/*/reference/` golden answers (incl. holdout) are reachable via parent traversal from any live trial (Audit 5/9). Example: dl-model-advisor evals/bin/run.py out_dir default + harness-settings.json deny list (2026-08-02; fixed via out-of-tree mkdtemp work root + Read() deny rules — note residual: Read() deny does not cover Bash `cat` via absolute paths derivable from plugin_dir).
