#!/usr/bin/env python3
"""Skill-lifecycle PostToolUse lint for dl-model-advisor outputs (v2).

Validates MODEL_PLAN.md and starter_model.py writes, now catalog-aware:
citations must name real OKF concepts and the Evidence line may never claim
a higher trust tier than the cited concept actually carries.

Bundle resolution: ./knowledge in the session cwd when present, else the
plugin's embedded snapshot (../knowledge-snapshot relative to this script).
Checks that need a concept the resolved bundle lacks are SKIPPED, never
false-blocked (the suite's workspace graders remain the final gate).

Contract (design/CONTRACT.md CAP-2/4/5 + docs/plans OKF design):
  other file      -> VERDICT=SKIP exit 0 (fast no-op)
  violation       -> VERDICT=BLOCK code=<CODE> stdout, reason stderr, exit 2
  clean           -> VERDICT=PASS exit 0
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAIRINGS_PATH = os.path.join(HERE, "..", "data", "pairings.json")
SNAPSHOT = os.path.normpath(os.path.join(HERE, "..", "knowledge-snapshot"))

OUT_OF_SCOPE_LINE = ("Status: OUT-OF-SCOPE — not covered by any stable "
                     "concept in the knowledge catalog")
LEGACY_OOS_LINE = ("Status: OUT-OF-SCOPE — not covered by "
                   "Deep Learning with Python, 2nd Edition (2021)")
IN_SCOPE_LINE = "Status: IN-SCOPE"

IN_SCOPE_SECTIONS = ["## Problem framing", "## Architecture",
                     "## Loss & activation", "## Evaluation protocol",
                     "## Workflow", "## Scope notes"]
OUT_SCOPE_SECTIONS = ["## Problem framing", "## Scope notes"]

ALLOWED_TOP_IMPORTS = {"keras", "tensorflow", "numpy"}
TIER_ORDER = {"unverified": 0, "machine-confirmed": 1, "human-reviewed": 2}


def block(code, reason):
    print("VERDICT=BLOCK code=%s" % code)
    sys.stderr.write("dl-model-advisor lint: %s\n" % reason)
    sys.exit(2)


def ok(verdict="PASS"):
    print("VERDICT=%s" % verdict)
    sys.exit(0)


def get_line_value(content, prefix):
    m = re.search(r"^%s\s*(.+?)\s*$" % re.escape(prefix), content, re.MULTILINE)
    return m.group(1) if m else None


def resolve_bundle(cwd):
    live = os.path.join(cwd, "knowledge")
    if os.path.isfile(os.path.join(live, "index.md")):
        return live
    if os.path.isdir(SNAPSHOT):
        return SNAPSHOT
    return None


def concept_tier(bundle, concept_id):
    """Returns (tier_name, stale_bool) or None when unresolvable."""
    path = os.path.join(bundle, concept_id + ".md")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = m.group(1)
    tier = "unverified"
    if re.search(r"^verified:", fm, re.M):
        vblock = fm[fm.index("verified:"):]
        if re.search(r"by:\s*human:", vblock):
            tier = "human-reviewed"
        elif re.search(r"by:\s*process:", vblock):
            tier = "machine-confirmed"
    stale = False
    sm = re.search(r"^stale_after:\s*(\d{4}-\d{2}-\d{2})", fm, re.M)
    if sm:
        try:
            stale = datetime.date.today() >= datetime.date.fromisoformat(sm.group(1))
        except ValueError:
            pass
    return tier, stale


def lint_citations(content, cwd):
    """Every bracketed concept citation must resolve; the Evidence line may
    never out-rank the weakest cited concept; stale cites must be flagged."""
    cited = re.findall(r"^Cited rule: .*\[([A-Za-z0-9/_-]+)\]\s*$",
                       content, re.MULTILINE)
    if not cited:
        block("MISSING_CONCEPT_ID",
              "every 'Cited rule:' line must end with the concept id in "
              "brackets, e.g. [foundations/text-ratio-rule]")
    evidence = get_line_value(content, "Evidence:")
    if not evidence:
        block("MISSING_EVIDENCE",
              "MODEL_PLAN.md must carry an 'Evidence:' line naming the "
              "trust tier of the cited knowledge")
    claimed = evidence.split("(")[0].strip().lower()
    if claimed not in TIER_ORDER:
        block("BAD_EVIDENCE",
              "Evidence tier must be one of: unverified | machine-confirmed "
              "| human-reviewed (got %r)" % evidence)
    bundle = resolve_bundle(cwd)
    if bundle is None:
        return  # no bundle resolvable: structural checks already passed
    floor_tier, any_stale, resolved = 2, False, False
    for cid in cited:
        info = concept_tier(bundle, cid)
        if info is None:
            if bundle != SNAPSHOT:
                block("UNKNOWN_CONCEPT",
                      "cited concept %r does not exist in the knowledge "
                      "bundle at %s" % (cid, bundle))
            continue  # snapshot lacks modern/domains — skip, don't block
        resolved = True
        tier, stale = info
        floor_tier = min(floor_tier, TIER_ORDER[tier])
        any_stale = any_stale or stale
    if resolved:
        if TIER_ORDER[claimed] > floor_tier:
            actual = [k for k, v in TIER_ORDER.items() if v == floor_tier][0]
            block("TIER_MISMATCH",
                  "Evidence claims %r but the weakest cited concept is only "
                  "%r — never claim a higher tier than the catalog grants"
                  % (claimed, actual))
        if any_stale and "stale" not in evidence.lower():
            block("STALE_UNDISCLOSED",
                  "a cited concept is past its stale_after date; the "
                  "Evidence line must disclose it, e.g. "
                  "'Evidence: machine-confirmed (stale)'")


def lint_plan(content, cwd):
    if OUT_OF_SCOPE_LINE in content or LEGACY_OOS_LINE in content:
        missing = [s for s in OUT_SCOPE_SECTIONS if s not in content]
        if missing:
            block("MISSING_SECTION",
                  "out-of-scope plan variant missing section(s): %s"
                  % ", ".join(missing))
        ok()
    if IN_SCOPE_LINE not in content:
        block("MISSING_STATUS",
              "MODEL_PLAN.md must carry 'Status: IN-SCOPE' or the canonical "
              "OUT-OF-SCOPE status line")
    missing = [s for s in IN_SCOPE_SECTIONS if s not in content]
    if missing:
        block("MISSING_SECTION",
              "MODEL_PLAN.md missing required section(s): %s" % ", ".join(missing))
    if not re.search(r"^Cited rule: ", content, re.MULTILINE):
        block("MISSING_CITATION",
              "Architecture section must carry a 'Cited rule:' line")
    task_type = get_line_value(content, "Task type:")
    activation = get_line_value(content, "Last-layer activation:")
    loss = get_line_value(content, "Loss:")
    for label, val in (("Task type:", task_type),
                       ("Last-layer activation:", activation),
                       ("Loss:", loss)):
        if not val:
            block("MISSING_FIELD", "MODEL_PLAN.md missing canonical '%s' line" % label)
    try:
        with open(PAIRINGS_PATH, "r", encoding="utf-8") as fh:
            pairings = json.load(fh)
    except (OSError, ValueError):
        block("PAIRINGS_UNREADABLE",
              "data/pairings.json missing or invalid next to the skill")
    entry = pairings.get(task_type.strip().lower())
    if entry:
        if activation.strip().lower() != entry["activation"]:
            block("PAIRING_MISMATCH",
                  "task type %r requires last-layer activation %r (ch6 table), "
                  "got %r" % (task_type, entry["activation"], activation))
        if loss.strip().lower() not in [l.lower() for l in entry["loss"]]:
            block("PAIRING_MISMATCH",
                  "task type %r requires loss in %s (ch6 table), got %r"
                  % (task_type, entry["loss"], loss))
    lint_citations(content, cwd)
    ok()


def lint_starter(content, cwd):
    try:
        compile(content, "starter_model.py", "exec")
    except SyntaxError as exc:
        block("SYNTAX", "starter_model.py does not compile: %s" % exc)
    stdlib = getattr(sys, "stdlib_module_names", set())
    for m in re.finditer(r"^\s*(?:import|from)\s+([A-Za-z_][A-Za-z0-9_]*)",
                         content, re.MULTILINE):
        root = m.group(1)
        if root in ALLOWED_TOP_IMPORTS or root in stdlib:
            continue
        block("FORBIDDEN_IMPORT",
              "starter_model.py imports %r — only keras/tensorflow/numpy "
              "and the standard library are allowed" % root)
    plan_path = os.path.join(cwd, "MODEL_PLAN.md")
    if os.path.isfile(plan_path):
        with open(plan_path, "r", encoding="utf-8", errors="replace") as fh:
            plan = fh.read()
        loss = get_line_value(plan, "Loss:")
        if loss and re.search(r"[A-Za-z_]", loss):
            token = loss.strip().lower()
            if token not in content.lower():
                block("PLAN_MISMATCH",
                      "starter_model.py never references the planned loss %r "
                      "from MODEL_PLAN.md" % loss)
    ok()


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        ok("SKIP")
    tool_input = event.get("tool_input") or {}
    file_path = str(tool_input.get("file_path") or "")
    base = os.path.basename(file_path)
    if base not in ("MODEL_PLAN.md", "starter_model.py"):
        ok("SKIP")
    content = tool_input.get("content")
    if not isinstance(content, str):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except OSError:
            ok("SKIP")
    cwd = str(event.get("cwd") or os.path.dirname(os.path.abspath(file_path))
              or os.getcwd())
    if base == "MODEL_PLAN.md":
        lint_plan(content, cwd)
    else:
        lint_starter(content, cwd)


if __name__ == "__main__":
    main()
