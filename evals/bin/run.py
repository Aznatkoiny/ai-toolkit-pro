#!/usr/bin/env python3
"""plugin-forge eval harness core (single-file, stdlib-only).

This file is the entire harness runtime. It is vendored verbatim into generated
plugins as evals/bin/run.py so their suites run WITHOUT plugin-forge installed.
Therefore: zero imports outside the Python standard library, zero imports from
sibling files. Everything (YAML subset parser, graders, judge/trigger drivers,
isolation, reporting) is implemented here.

USAGE (normally via the `forge-eval` wrapper, which execs this file):
    run.py run        --suite S --plugin-dir P [--target T] [--trials N]
                      [--jobs N] [--task ID] [--max-cost-usd X] [--dry-run]
                      [--out DIR] [--evals-dir D]
    run.py red        ... (same flags; forces the no-plugin target; PASS means
                      ZERO tasks pass bare — every task shows signal)
    run.py reference  ... (grades each task's reference/ solution with the
                      task's own workspace/state_check/judge graders)
    run.py smoke      --plugin-dir P   (delegates to ../smoke/smoke.py when it
                      exists next to this install; else built-in init gate)
    run.py metaeval   [--judge NAME] [--evals-dir D]   (judge-vs-human-labels
                      agreement over evals/labels/labels.jsonl)
    run.py graduate   [--threshold 0.9] [--dry-run]    (move saturated
                      capability tasks to the regression suite)
    run.py doctor     [--dry-run]      (clear stuck .forge phase, remove leaked
                      forge worktrees and stale run workspaces)

EXIT CODE: 0 iff the final scoreboard line says RESULT=PASS (per subcommand
semantics). The FINAL stdout line is always the scoreboard:

    FORGE_EVAL: suite=<name> version=v<N> passed=<X>/<Y> pass^<k>=<0.00> cost_usd=<C> RESULT=PASS|FAIL

That line is also appended to .forge/last-scoreboard.txt and embedded in
runs/<ts>/summary.json — it is the /goal-evaluator and CI contract.

TREE HASH CONTRACT (must byte-match hooks/scripts/sweep-evals.sh):
    cd <project root>
    find evals -type f -print0 | LC_ALL=C sort -z | xargs -0 shasum -a 256 | shasum -a 256
    → first field. I.e. sha256 over the concatenation of
    "<sha256(file)>  <relpath>\n" lines (TWO spaces — shasum text-mode format)
    for every regular file under evals/ (symlinks excluded, as `find -type f`
    excludes them), sorted bytewise by relative path. An empty tree hashes the
    empty concatenation (e3b0c442...).

YAML SUBSET (stdlib has no yaml; this constrained parser covers exactly what
plugin-forge's templates emit — task.yaml/target yaml/judge yaml/suite yaml/
registry.yaml stay inside it; JSON twins *.json are accepted everywhere too):
  - block mappings and block sequences, nested by indentation (spaces only)
  - plain scalars: int, float, true/false, null/~, everything else = string
  - single- and double-quoted strings ('' and \\" escapes)
  - one-line flow collections: {k: v, ...} and [a, b, ...] (nestable)
  - literal/folded block scalars: `key: |` / `key: >` (with optional - chomp)
  - full-line and trailing ` #` comments; blank lines
  NOT supported (templates never emit them): anchors/aliases, tags, multi-doc
  `---` streams, complex keys, tabs for indentation.

EVENTS (runs/<ts>/events.jsonl, one JSON object per line, typed):
  sample  — one task×trial outcome {task, trial, status, cost_usd, turns,
            tokens, duration_s} where status ∈ pass|fail|timeout|unverified|
            error|aborted|skipped
  check   — one grader verdict {task, trial, grader, check, passed, detail}
  judge   — one judge call {task, trial, spec, model, choice, score,
            rationale, evidence, cost_usd}
  metric  — tracked metric {name, value, task?, trial?}
  error   — harness-level problem {where, message}

SCORING DOCTRINE:
  - timeouts (SIGTERM → exit 143) are recorded status=timeout and count as
    failures; api_retry events mark the trial status=unverified and EXCLUDE it
    from all pass-rate denominators (infra noise is not agent failure).
  - pass@k = fraction of tasks with ≥1 verified passing trial.
  - pass^k = fraction of tasks where ALL verified trials passed (headline).
  - a task's own `metric` field (pass^k default) decides whether IT passed;
    RESULT=PASS iff every graded task passed its own metric.
  - numeric workspace checks REQUIRE `tolerance`; a task without it refuses to
    LOAD (CORE-Bench lint at load time, not grade time).
  - transcript tool checks match name + params SUBSET — NEVER call order.

TRIGGER TASKS AND HOOKS: hook firings do NOT appear in stream-json output, so
`type: trigger` graders can only observe Skill tool_use (skills) and
Task/Agent tool_use (agent dispatch). To trigger-test a HOOK, write a
state_check grader on the hook's side effects (log file, blocked exit, marker
file) instead — see build-evals references/task-authoring.md.
"""

import argparse
import concurrent.futures
import datetime as _dt
import hashlib
import html as _html
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

# --------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------

SCOREBOARD_FMT = ("FORGE_EVAL: suite={suite} version=v{version} "
                  "passed={passed}/{total} pass^{k}={passk:.2f} "
                  "cost_usd={cost:.2f} RESULT={result}")
MAX_JOBS = 8
DEFAULT_TRIALS = 3
DEFAULT_TIMEOUT_S = 600
DEFAULT_JUDGE_MODEL = "haiku"
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "choice": {"type": "string"},
        "rationale": {"type": "string"},
        "evidence": {"type": "string"},
    },
    "required": ["choice", "rationale"],
}


class HarnessError(Exception):
    """Fatal harness-level problem (bad task file, missing suite, ...)."""


class TaskLoadError(HarnessError):
    """A task file violates the schema (e.g. tolerance-less numeric check)."""


# --------------------------------------------------------------------------
# minimal YAML parser (subset documented in module docstring)
# --------------------------------------------------------------------------

_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+[eE][+-]?\d+|\d+\.\d*[eE][+-]?\d+)$")


def _parse_scalar(text):
    t = text.strip()
    if t == "" or t in ("~", "null", "Null", "NULL"):
        return None
    if t in ("true", "True", "TRUE"):
        return True
    if t in ("false", "False", "FALSE"):
        return False
    if _INT_RE.match(t):
        return int(t)
    if _FLOAT_RE.match(t):
        return float(t)
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        # JSON-compatible double-quoted string
        try:
            return json.loads(t)
        except ValueError:
            return t[1:-1]
    if len(t) >= 2 and t[0] == "'" and t[-1] == "'":
        return t[1:-1].replace("''", "'")
    return t


def _split_flow(body, seps=","):
    """Split a flow-collection body on top-level separators."""
    parts, depth, quote, cur = [], 0, None, []
    i = 0
    while i < len(body):
        ch = body[i]
        if quote:
            cur.append(ch)
            if quote == '"' and ch == "\\" and i + 1 < len(body):
                cur.append(body[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        elif ch in "{[":
            depth += 1
            cur.append(ch)
        elif ch in "}]":
            depth -= 1
            cur.append(ch)
        elif depth == 0 and ch in seps:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    if cur or parts:
        parts.append("".join(cur))
    return parts


def _parse_flow(text):
    """Parse a one-line flow collection or scalar."""
    t = text.strip()
    if t.startswith("{") and t.endswith("}"):
        out = {}
        body = t[1:-1].strip()
        if not body:
            return out
        for part in _split_flow(body):
            if not part.strip():
                continue
            kv = _split_flow(part, seps=":")
            if len(kv) < 2:
                raise HarnessError("bad flow mapping entry: %r" % part)
            key = _parse_scalar(kv[0])
            out[key] = _parse_flow(":".join(kv[1:]))
        return out
    if t.startswith("[") and t.endswith("]"):
        body = t[1:-1].strip()
        if not body:
            return []
        return [_parse_flow(p) for p in _split_flow(body) if p.strip() != ""]
    return _parse_scalar(t)


def _strip_comment(line):
    """Remove a trailing comment (a ' #' outside quotes). Full-line comments
    are handled by the caller."""
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if quote == '"' and ch == "\\":
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line.rstrip()


def yaml_load(text):
    """Parse the documented YAML subset. Returns dict/list/scalar."""
    lines = []
    for raw in text.splitlines():
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise HarnessError("tabs in YAML indentation are not supported")
        stripped = raw.strip()
        if stripped == "---":
            continue  # single leading doc marker tolerated
        lines.append(raw)
    value, idx = _parse_block(lines, 0, 0, allow_less=False)
    # skip trailing blank/comment lines
    while idx < len(lines):
        s = lines[idx].strip()
        if s and not s.startswith("#"):
            raise HarnessError("trailing content at line %d: %r" % (idx + 1, s))
        idx += 1
    return value


def _indent_of(line):
    return len(line) - len(line.lstrip(" "))


def _next_content(lines, idx):
    while idx < len(lines):
        s = lines[idx].strip()
        if s and not s.startswith("#"):
            return idx
        idx += 1
    return None


_KEY_RE = re.compile(r"""^(?P<key>[^:#]+?|"[^"]*"|'[^']*')\s*:(?:\s+(?P<rest>.*))?$""")


def _parse_block(lines, idx, indent, allow_less=True):
    """Parse a block (mapping or sequence) at exactly `indent` columns.
    Returns (value, next_index)."""
    start = _next_content(lines, idx)
    if start is None:
        return None, len(lines)
    first = lines[start]
    if _indent_of(first) < indent:
        return None, start
    ind = _indent_of(first)
    if first.lstrip().startswith("- "):
        return _parse_sequence(lines, start, ind)
    if first.lstrip() == "-":
        return _parse_sequence(lines, start, ind)
    return _parse_mapping(lines, start, ind)


def _parse_mapping(lines, idx, indent):
    out = {}
    while True:
        nxt = _next_content(lines, idx)
        if nxt is None:
            return out, len(lines)
        line = lines[nxt]
        if _indent_of(line) < indent:
            return out, nxt
        if _indent_of(line) > indent:
            raise HarnessError("unexpected indent at line %d: %r" % (nxt + 1, line))
        content = _strip_comment(line.strip())
        if content.startswith("- "):
            raise HarnessError("sequence item inside mapping at line %d" % (nxt + 1))
        m = _KEY_RE.match(content)
        if not m:
            raise HarnessError("expected 'key: value' at line %d: %r" % (nxt + 1, content))
        key = _parse_scalar(m.group("key"))
        rest = (m.group("rest") or "").strip()
        if rest in ("|", "|-", ">", ">-"):
            val, idx = _parse_block_scalar(lines, nxt + 1, indent, rest)
            out[key] = val
        elif rest:
            out[key] = _parse_flow(rest)
            idx = nxt + 1
        else:
            val, idx = _parse_block(lines, nxt + 1, indent + 1)
            out[key] = val
    return out, idx


def _parse_sequence(lines, idx, indent):
    out = []
    while True:
        nxt = _next_content(lines, idx)
        if nxt is None:
            return out, len(lines)
        line = lines[nxt]
        if _indent_of(line) != indent or not line.lstrip().startswith("-"):
            if _indent_of(line) < indent:
                return out, nxt
            raise HarnessError("unexpected line %d in sequence: %r" % (nxt + 1, line))
        content = _strip_comment(line.strip())
        rest = content[1:].strip()  # drop the dash
        if not rest:
            val, idx = _parse_block(lines, nxt + 1, indent + 1)
            out.append(val)
        elif _KEY_RE.match(rest) and not rest.startswith(("{", "[", '"', "'")):
            # "- key: value" — inline start of a nested mapping; re-parse the
            # remainder as a mapping whose first line is the rest, by shifting
            # the dash into indentation.
            dash_col = line.index("-")
            synthetic = [" " * (dash_col + 2) + rest] + lines[nxt + 1:]
            val, consumed = _parse_mapping(synthetic, 0, dash_col + 2)
            out.append(val)
            idx = nxt + 1 + (consumed - 1)
        else:
            out.append(_parse_flow(rest))
            idx = nxt + 1
    return out, idx


def _parse_block_scalar(lines, idx, parent_indent, marker):
    """Parse `|` / `>` block scalars (with optional `-` chomping)."""
    body_lines = []
    body_indent = None
    while idx < len(lines):
        line = lines[idx]
        if line.strip() == "":
            body_lines.append("")
            idx += 1
            continue
        ind = _indent_of(line)
        if ind <= parent_indent:
            break
        if body_indent is None:
            body_indent = ind
        body_lines.append(line[body_indent:])
        idx += 1
    while body_lines and body_lines[-1] == "":
        body_lines.pop()
    if marker.startswith("|"):
        text = "\n".join(body_lines)
    else:  # folded
        text = ""
        for i, l in enumerate(body_lines):
            if l == "":
                text += "\n"
            elif text and not text.endswith("\n"):
                text += " " + l
            else:
                text += l
    if not marker.endswith("-"):
        text += "\n"
    return text, idx


def load_structured(path):
    """Load a .yaml/.yml/.json file via the subset parser or json."""
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if str(path).endswith(".json"):
        return json.loads(text)
    return yaml_load(text)


def find_structured(base_no_ext):
    """Return the existing .yaml/.yml/.json twin of a base path, or None."""
    for ext in (".yaml", ".yml", ".json"):
        p = base_no_ext + ext
        if os.path.isfile(p):
            return p
    return None


# --------------------------------------------------------------------------
# structural helpers
# --------------------------------------------------------------------------

def json_subset_match(expected, actual, _path=""):
    """Structural subset: every key/element in `expected` must be present and
    match in `actual`. Dicts: recursive on expected keys. Lists: each expected
    element must match SOME actual element (order-free). Strings starting with
    're:' are regex-searched. Returns (ok, detail)."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False, "%s: expected object, got %s" % (_path or "$", type(actual).__name__)
        for k, v in expected.items():
            if k not in actual:
                return False, "%s.%s: missing" % (_path or "$", k)
            ok, why = json_subset_match(v, actual[k], "%s.%s" % (_path, k))
            if not ok:
                return False, why
        return True, ""
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False, "%s: expected array, got %s" % (_path or "$", type(actual).__name__)
        for i, ev in enumerate(expected):
            if not any(json_subset_match(ev, av)[0] for av in actual):
                return False, "%s[%d]: no matching element" % (_path or "$", i)
        return True, ""
    if isinstance(expected, str) and expected.startswith("re:"):
        if re.search(expected[3:], str(actual)):
            return True, ""
        return False, "%s: %r !~ /%s/" % (_path or "$", actual, expected[3:])
    if isinstance(expected, bool) or isinstance(actual, bool):
        if expected is actual:
            return True, ""
        return False, "%s: expected %r, got %r" % (_path or "$", expected, actual)
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if float(expected) == float(actual):
            return True, ""
        return False, "%s: expected %r, got %r" % (_path or "$", expected, actual)
    if expected == actual:
        return True, ""
    return False, "%s: expected %r, got %r" % (_path or "$", expected, actual)


def tree_sha256(project_root, subdir="evals"):
    """Byte-match of the sweep-evals.sh pipeline (see module docstring)."""
    base = os.path.join(project_root, subdir)
    rels = []
    for dirpath, _dirnames, filenames in os.walk(base):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            if os.path.islink(full) or not os.path.isfile(full):
                continue  # find -type f excludes symlinks
            rels.append(os.path.relpath(full, project_root))
    rels.sort(key=lambda r: r.encode("utf-8"))  # LC_ALL=C sort
    outer = hashlib.sha256()
    for rel in rels:
        h = hashlib.sha256()
        with open(os.path.join(project_root, rel), "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        outer.update(("%s  %s\n" % (h.hexdigest(), rel)).encode("utf-8"))
    return outer.hexdigest()


def now_iso():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_json(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=False)
        fh.write("\n")


# --------------------------------------------------------------------------
# suite / task / target loading
# --------------------------------------------------------------------------

def default_evals_dir():
    """When vendored as evals/bin/run.py, the evals root is our grandparent;
    when installed as scripts/harness/run.py, it is ./evals under CWD."""
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(here) == "bin":
        parent = os.path.dirname(here)
        if os.path.isdir(os.path.join(parent, "tasks")) or \
           find_structured(os.path.join(parent, "registry")):
            return parent
    return os.path.join(os.getcwd(), "evals")


def resolve_suite(evals_dir, suite_name):
    """Return (suite_dict, version_int). registry.yaml maps alias →
    '<suite>.<split>.v<N>' (OpenAI-style); the suite file lives at
    suites/<suite_name>.yaml with a `tasks:` id list."""
    version = 0
    reg_path = find_structured(os.path.join(evals_dir, "registry"))
    if reg_path:
        reg = load_structured(reg_path) or {}
        aliases = reg.get("aliases", reg) if isinstance(reg, dict) else {}
        target_id = aliases.get(suite_name)
        if isinstance(target_id, str):
            m = re.search(r"\.v(\d+)$", target_id)
            if m:
                version = int(m.group(1))
    suite_path = find_structured(os.path.join(evals_dir, "suites", suite_name))
    if not suite_path:
        raise HarnessError("suite %r not found under %s/suites/" % (suite_name, evals_dir))
    suite = load_structured(suite_path) or {}
    if not isinstance(suite, dict) or not isinstance(suite.get("tasks"), list):
        raise HarnessError("suite file %s must contain a `tasks:` list" % suite_path)
    suite.setdefault("name", suite_name)
    suite["_path"] = suite_path
    if isinstance(suite.get("version"), (int, str)):
        m = re.search(r"(\d+)", str(suite["version"]))
        if m:
            version = int(m.group(1))
    return suite, version


VALID_WORKSPACE_CHECKS = ("file_exists", "file_contains", "json_match",
                          "git_diff", "exit_code", "numeric")
VALID_TRANSCRIPT_CHECKS = ("tool_called", "max_turns", "token_budget")
VALID_GRADER_TYPES = ("workspace", "transcript", "state_check", "judge", "trigger")


def load_task(evals_dir, task_id):
    """Load tasks/<id>/task.yaml (+instruction.md) and validate. Raises
    TaskLoadError on schema violations — notably tolerance-less numeric."""
    task_dir = os.path.join(evals_dir, "tasks", task_id)
    task_path = find_structured(os.path.join(task_dir, "task"))
    if not task_path:
        raise TaskLoadError("task %r: no task.yaml/task.json under %s" % (task_id, task_dir))
    task = load_structured(task_path)
    if not isinstance(task, dict):
        raise TaskLoadError("task %r: task file is not a mapping" % task_id)
    task.setdefault("id", task_id)
    task.setdefault("trials", DEFAULT_TRIALS)
    task.setdefault("metric", "pass^k")
    task.setdefault("scoring", "binary")
    task.setdefault("timeout_s", DEFAULT_TIMEOUT_S)
    task.setdefault("launch", "claude")
    if task["launch"] not in ("claude", "none"):
        raise TaskLoadError("task %r: `launch` must be 'claude' or 'none', got %r"
                            % (task_id, task["launch"]))
    task["_dir"] = task_dir
    graders = task.get("graders")
    if not isinstance(graders, list) or not graders:
        raise TaskLoadError("task %r: `graders` must be a non-empty list" % task_id)
    for i, g in enumerate(graders):
        if not isinstance(g, dict):
            raise TaskLoadError("task %r: grader %d is not a mapping" % (task_id, i))
        gtype = g.get("type")
        if gtype not in VALID_GRADER_TYPES:
            raise TaskLoadError("task %r: grader %d has unknown type %r "
                                "(valid: %s)" % (task_id, i, gtype,
                                                 ", ".join(VALID_GRADER_TYPES)))
        if gtype == "workspace":
            check = g.get("check")
            if check not in VALID_WORKSPACE_CHECKS:
                raise TaskLoadError("task %r: workspace grader %d has unknown "
                                    "check %r" % (task_id, i, check))
            if check == "numeric" and not isinstance(g.get("tolerance"), (int, float)):
                raise TaskLoadError(
                    "task %r: numeric check (grader %d) has no numeric "
                    "`tolerance` — REFUSING to load. Exact float equality is "
                    "the CORE-Bench grader bug; every numeric check must "
                    "declare tolerance (e.g. tolerance: 0.01)." % (task_id, i))
        if gtype == "transcript":
            check = g.get("check")
            if check not in VALID_TRANSCRIPT_CHECKS:
                raise TaskLoadError("task %r: transcript grader %d has unknown "
                                    "check %r" % (task_id, i, check))
            if "order" in g or "sequence" in g:
                raise TaskLoadError("task %r: transcript grader %d asserts tool "
                                    "ORDER — forbidden (order is not part of "
                                    "the contract; assert calls, not choreography)"
                                    % (task_id, i))
        if task["launch"] == "none" and gtype in ("transcript", "trigger"):
            raise TaskLoadError("task %r: grader %d is type %r but launch: none "
                                "runs no Claude session — there is no transcript "
                                "to grade. Use state_check/workspace graders."
                                % (task_id, i, gtype))
        if gtype == "judge" and not g.get("spec"):
            raise TaskLoadError("task %r: judge grader %d missing `spec`" % (task_id, i))
        if gtype == "trigger":
            if not isinstance(g.get("should"), list) and not isinstance(g.get("should_not"), list):
                raise TaskLoadError("task %r: trigger grader %d needs `should` "
                                    "and/or `should_not` prompt lists" % (task_id, i))
    instr = os.path.join(task_dir, "instruction.md")
    task["_instruction"] = None
    if os.path.isfile(instr):
        with open(instr, "r", encoding="utf-8") as fh:
            task["_instruction"] = fh.read()
    return task


def load_target(evals_dir, target_name):
    """targets/<name>.yaml — a named `claude -p` launch config. Recognized
    keys (defaults in parens): bare (true), plugin (true — load --plugin-dir),
    model, permission_mode, allowed_tools, settings (path relative to the
    target file), distractor_plugin_dirs (list, for crowded-listing targets),
    append_system_prompt, extra_flags (list of raw argv strings)."""
    path = find_structured(os.path.join(evals_dir, "targets", target_name))
    if not path:
        raise HarnessError("target %r not found under %s/targets/" % (target_name, evals_dir))
    t = load_structured(path) or {}
    if not isinstance(t, dict):
        raise HarnessError("target file %s is not a mapping" % path)
    t.setdefault("name", target_name)
    t["_path"] = path
    # canonicalize alternate key spellings emitted by hand-written targets
    for a, b in (("permissionMode", "permission_mode"),
                 ("allowedTools", "allowed_tools"),
                 ("distractors", "distractor_plugin_dirs"),
                 ("extra_plugin_dirs", "distractor_plugin_dirs")):
        if a in t and b not in t:
            t[b] = t.pop(a)
    # plugin_dir: a BOOLEAN is the legacy spelling of `plugin`; a STRING is a
    # path fallback used when the CLI --plugin-dir flag is absent (standalone
    # vendored suites) — keep it as plugin_dir in that case.
    if "plugin_dir" in t and isinstance(t["plugin_dir"], bool) and "plugin" not in t:
        t["plugin"] = t.pop("plugin_dir")
    return t


# --------------------------------------------------------------------------
# event log
# --------------------------------------------------------------------------

class EventLog:
    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._fh = open(path, "a", encoding="utf-8")

    def emit(self, etype, **fields):
        rec = {"type": etype, "ts": now_iso()}
        rec.update(fields)
        with self._lock:
            self._fh.write(json.dumps(rec, default=str) + "\n")
            self._fh.flush()
        return rec

    def close(self):
        with self._lock:
            self._fh.close()


# --------------------------------------------------------------------------
# claude -p launcher + stream-json parsing
# --------------------------------------------------------------------------

class TrialStream:
    """Parsed view over one claude -p stream-json run."""

    def __init__(self):
        self.events = []
        self.init = None
        self.result = None
        self.api_retries = 0
        self.tool_uses = []          # [{name, input, parent_tool_use_id}]
        self.plugin_errors = []
        self.mcp_server_errors = []

    def feed_line(self, line):
        line = line.strip()
        if not line:
            return
        try:
            ev = json.loads(line)
        except ValueError:
            return
        self.events.append(ev)
        etype = ev.get("type")
        if etype == "system":
            sub = ev.get("subtype")
            if sub == "init":
                self.init = ev
                self.plugin_errors = ev.get("plugin_errors") or []
                self.mcp_server_errors = ev.get("mcp_server_errors") or []
            elif sub == "api_retry":
                self.api_retries += 1
        elif etype == "assistant":
            msg = ev.get("message") or {}
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    self.tool_uses.append({
                        "name": block.get("name", ""),
                        "input": block.get("input") or {},
                        "parent_tool_use_id": ev.get("parent_tool_use_id"),
                    })
        elif etype == "result":
            self.result = ev

    @property
    def cost_usd(self):
        if self.result and isinstance(self.result.get("total_cost_usd"), (int, float)):
            return float(self.result["total_cost_usd"])
        return 0.0

    @property
    def num_turns(self):
        if self.result and isinstance(self.result.get("num_turns"), int):
            return self.result["num_turns"]
        return None

    @property
    def total_tokens(self):
        usage = (self.result or {}).get("usage") or {}
        total = 0
        for key in ("input_tokens", "output_tokens",
                    "cache_creation_input_tokens", "cache_read_input_tokens"):
            v = usage.get(key)
            if isinstance(v, (int, float)):
                total += int(v)
        return total or None

    @property
    def result_text(self):
        return (self.result or {}).get("result") or ""

    def plugin_loaded(self, name):
        for p in (self.init or {}).get("plugins") or []:
            if isinstance(p, dict) and p.get("name") == name:
                return True
        return False


def build_claude_cmd(target, prompt, plugin_dir, evals_dir):
    """Assemble the claude -p argv for one trial per the target yaml.
    Defaults: --bare, --plugin-dir <plugin>, stream-json + --verbose +
    --forward-subagent-text, --settings if the target names one."""
    cmd = ["claude", "-p", prompt]
    if target.get("bare", True):
        cmd.append("--bare")
    eff = _effective_plugin_dir(target, plugin_dir, evals_dir)
    if eff:
        cmd += ["--plugin-dir", eff]
    for d in target.get("distractor_plugin_dirs") or []:
        # relative distractor paths resolve against the target FILE's dir
        # (templates reference them as ../distractors/<name>)
        base = os.path.dirname(target.get("_path", evals_dir))
        cmd += ["--plugin-dir", os.path.abspath(os.path.join(base, d))
                if not os.path.isabs(d) else d]
    cmd += ["--output-format", "stream-json", "--verbose",
            "--forward-subagent-text"]
    if target.get("model"):
        cmd += ["--model", str(target["model"])]
    if target.get("permission_mode"):
        cmd += ["--permission-mode", str(target["permission_mode"])]
    if target.get("allowed_tools"):
        at = target["allowed_tools"]
        cmd += ["--allowedTools", ",".join(at) if isinstance(at, list) else str(at)]
    if target.get("settings"):
        s = str(target["settings"])
        if not os.path.isabs(s) and not s.lstrip().startswith("{"):
            s = os.path.abspath(os.path.join(os.path.dirname(target["_path"]), s))
        cmd += ["--settings", s]
    if target.get("append_system_prompt"):
        cmd += ["--append-system-prompt", str(target["append_system_prompt"])]
    for extra in target.get("extra_flags") or []:
        cmd.append(str(extra))
    return cmd


_HERMETIC_ENV = None


def hermetic_env():
    """Environment for every claude subprocess: a throwaway CLAUDE_CONFIG_DIR
    so the user's personal plugin fleet and settings NEVER load into a trial,
    trigger-probe, or judge session. Observed on 2026-08-02: `--bare` alone
    still loaded all user-scope plugins (30 of them), breaking the
    hermeticity contract and contaminating the RED baseline. Auth flows
    through ANTHROPIC_API_KEY, which bare mode reads from the environment."""
    global _HERMETIC_ENV
    if _HERMETIC_ENV is None:
        cfg = tempfile.mkdtemp(prefix="forge-eval-config-")
        _HERMETIC_ENV = dict(os.environ, CLAUDE_CONFIG_DIR=cfg)
    return _HERMETIC_ENV


def run_claude(cmd, cwd, timeout_s, transcript_path=None, env=None):
    """Run a claude -p invocation; SIGTERM at timeout (recorded exit 143).
    Returns (TrialStream, exit_code, timed_out)."""
    stream = TrialStream()
    tf = open(transcript_path, "w", encoding="utf-8") if transcript_path else None
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            env=env or hermetic_env(), start_new_session=True)
    timed_out = False
    KILL_GRACE_S = 5

    def _hard_kill():
        # Escalation: fires KILL_GRACE_S after SIGTERM regardless of whether
        # the stdout read loop is still blocked (a descendant trapping SIGTERM
        # and holding the merged pipe open would otherwise hang the harness).
        if proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass

    def _kill():
        nonlocal timed_out
        timed_out = True
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        escalate = threading.Timer(KILL_GRACE_S, _hard_kill)
        escalate.daemon = True
        escalate.start()

    timer = threading.Timer(timeout_s, _kill)
    timer.daemon = True
    timer.start()
    try:
        for line in proc.stdout:
            if tf:
                tf.write(line)
            stream.feed_line(line)
        proc.wait()
    finally:
        timer.cancel()
        if tf:
            tf.close()
    code = proc.returncode
    if timed_out:
        code = 143
    return stream, code, timed_out


# --------------------------------------------------------------------------
# per-trial isolation
# --------------------------------------------------------------------------

class Workspace:
    """Fresh isolation for one task×trial.

    If the task's fixtures/ directory is itself a git repo, a detached git
    worktree is added from it (and recorded in a ledger so `doctor` can reap
    leaks after a crash). Otherwise fixtures/ is copied into a fresh dir.
    .worktreeinclude in the fixture root is honored either way: gitignored
    files matching its patterns are copied in (credentials, .env, ...).
    Teardown is MANDATORY and runs in a finally block at the call site.
    """

    def __init__(self, task, work_root, ledger_path):
        self.task = task
        self.ledger_path = ledger_path
        self.fixture_dir = os.path.join(task["_dir"], "fixtures")
        self.dir = os.path.join(work_root, "%s-t%d" % (task["id"], task["_trial"]))
        self.is_worktree = False

    def stage(self):
        os.makedirs(os.path.dirname(self.dir), exist_ok=True)
        if os.path.isdir(os.path.join(self.fixture_dir, ".git")):
            subprocess.run(
                ["git", "-C", self.fixture_dir, "worktree", "add",
                 "--detach", os.path.abspath(self.dir)],
                check=True, capture_output=True, text=True)
            self.is_worktree = True
            self._ledger("add")
            self._copy_worktreeinclude()
        elif os.path.isdir(self.fixture_dir):
            shutil.copytree(self.fixture_dir, self.dir)
        else:
            os.makedirs(self.dir, exist_ok=True)
        return self.dir

    def _copy_worktreeinclude(self):
        """Copy gitignored files matching .worktreeinclude patterns into the
        fresh worktree (git worktree add only carries tracked files)."""
        inc = os.path.join(self.fixture_dir, ".worktreeinclude")
        if not os.path.isfile(inc):
            return
        with open(inc, "r", encoding="utf-8") as fh:
            patterns = [l.strip() for l in fh
                        if l.strip() and not l.strip().startswith("#")]
        if not patterns:
            return
        import fnmatch
        for dirpath, dirnames, filenames in os.walk(self.fixture_dir):
            if ".git" in dirnames:
                dirnames.remove(".git")
            for fn in filenames:
                src = os.path.join(dirpath, fn)
                rel = os.path.relpath(src, self.fixture_dir)
                matched = any(
                    fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(fn, pat) or
                    fnmatch.fnmatch(rel, pat.rstrip("/") + "/*")
                    for pat in patterns)
                if not matched:
                    continue
                dst = os.path.join(self.dir, rel)
                if os.path.exists(dst):
                    continue  # tracked file already present
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

    def _ledger(self, action):
        try:
            os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
            with open(self.ledger_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"action": action, "ts": now_iso(),
                                     "fixture_repo": self.fixture_dir,
                                     "worktree": os.path.abspath(self.dir)}) + "\n")
        except OSError:
            pass

    def teardown(self):
        """MANDATORY: -p never cleans up; neither worktrees nor copies may leak."""
        if self.is_worktree:
            subprocess.run(
                ["git", "-C", self.fixture_dir, "worktree", "remove",
                 "--force", os.path.abspath(self.dir)],
                capture_output=True, text=True)
            subprocess.run(["git", "-C", self.fixture_dir, "worktree", "prune"],
                           capture_output=True, text=True)
            self._ledger("remove")
        if os.path.isdir(self.dir):
            shutil.rmtree(self.dir, ignore_errors=True)


# --------------------------------------------------------------------------
# graders
# --------------------------------------------------------------------------

def _resolve_in(base, path):
    return path if os.path.isabs(path) else os.path.join(base, path)


def grade_workspace(grader, ctx):
    """workspace checks: file_exists | file_contains | json_match | git_diff |
    exit_code | numeric (tolerance REQUIRED — enforced at load)."""
    ws = ctx["workspace"]
    check = grader.get("check")
    if check == "file_exists":
        p = _resolve_in(ws, grader.get("path", ""))
        ok = os.path.isfile(p) or (grader.get("dir", False) and os.path.isdir(p))
        return ok, "%s %s" % (grader.get("path"), "exists" if ok else "MISSING")
    if check == "file_contains":
        p = _resolve_in(ws, grader.get("path", ""))
        if not os.path.isfile(p):
            return False, "%s missing" % grader.get("path")
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        pattern = str(grader.get("pattern", grader.get("regex", "")))
        if re.search(pattern, content, re.MULTILINE):
            return True, "pattern /%s/ found" % pattern
        return False, "pattern /%s/ not found in %s" % (pattern, grader.get("path"))
    if check == "json_match":
        p = _resolve_in(ws, grader.get("path", ""))
        if not os.path.isfile(p):
            return False, "%s missing" % grader.get("path")
        actual = read_json(p)
        if actual is None:
            return False, "%s is not valid JSON" % grader.get("path")
        ok, why = json_subset_match(grader.get("expect"), actual)
        return ok, why or "structural subset matched"
    if check == "git_diff":
        if not os.path.isdir(os.path.join(ws, ".git")):
            return False, "workspace is not a git checkout — git_diff needs a git fixture"
        proc = subprocess.run(["git", "-C", ws, "status", "--porcelain"],
                              capture_output=True, text=True)
        changed = set()
        for line in proc.stdout.splitlines():
            if len(line) > 3:
                changed.add(line[3:].strip().strip('"'))
        proc2 = subprocess.run(["git", "-C", ws, "diff", "--name-only", "HEAD"],
                               capture_output=True, text=True)
        changed.update(l.strip() for l in proc2.stdout.splitlines() if l.strip())
        import fnmatch
        for pat in grader.get("must_change") or []:
            if not any(fnmatch.fnmatch(c, pat) for c in changed):
                return False, "no changed file matches must_change %r (changed: %s)" % (
                    pat, sorted(changed)[:10])
        for pat in grader.get("must_not_change") or []:
            hits = [c for c in changed if fnmatch.fnmatch(c, pat)]
            if hits:
                return False, "must_not_change %r violated by %s" % (pat, hits[:5])
        return True, "git diff constraints hold (%d files changed)" % len(changed)
    if check == "exit_code":
        expect = grader.get("expect", 0)
        actual = ctx.get("exit_code")
        ok = actual == expect
        return ok, "claude exit code %s (expected %s)" % (actual, expect)
    if check == "numeric":
        tol = grader["tolerance"]  # presence enforced at load time
        expect = grader.get("expect")
        if not isinstance(expect, (int, float)):
            return False, "numeric check has non-numeric `expect`: %r" % (expect,)
        p = _resolve_in(ws, grader.get("path", ""))
        if not os.path.isfile(p):
            return False, "%s missing" % grader.get("path")
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        value = None
        jp = grader.get("json_path")
        if jp:
            data = read_json(p)
            cur = data
            for part in str(jp).lstrip("$.").split("."):
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
                    cur = cur[int(part)]
                else:
                    return False, "json_path %r not found in %s" % (jp, grader.get("path"))
            value = cur
        elif grader.get("pattern"):
            m = re.search(str(grader["pattern"]), content, re.MULTILINE)
            if not m:
                return False, "pattern /%s/ not found" % grader["pattern"]
            value = m.group(1) if m.groups() else m.group(0)
        else:
            value = content.strip()
        try:
            value = float(value)
        except (TypeError, ValueError):
            return False, "extracted value %r is not numeric" % (value,)
        ok = abs(value - float(expect)) <= float(tol)
        return ok, "value %s vs expected %s ± %s" % (value, expect, tol)
    return False, "unknown workspace check %r" % check


def grade_transcript(grader, ctx):
    """transcript checks: tool_called (params SUBSET — never order) |
    max_turns | token_budget."""
    stream = ctx["stream"]
    check = grader.get("check")
    if stream is None:
        return False, "no transcript available for check %r" % check
    if check == "tool_called":
        want_name = str(grader.get("tool", ""))
        want_params = grader.get("params") or {}
        name_re = re.compile("^(%s)$" % want_name) if want_name else None
        for tu in stream.tool_uses:
            if name_re and not name_re.match(tu["name"]):
                continue
            ok, _why = json_subset_match(want_params, tu["input"])
            if ok:
                return True, "tool %s called with matching params" % tu["name"]
        called = sorted({t["name"] for t in stream.tool_uses})
        return False, "no %s call with params ⊇ %s (tools called: %s)" % (
            want_name, json.dumps(want_params)[:200], called[:15])
    if check == "max_turns":
        limit = grader.get("limit", grader.get("max"))
        turns = stream.num_turns
        if turns is None:
            return False, "no turn count in result event"
        ok = turns <= int(limit)
        return ok, "%d turns (limit %s)" % (turns, limit)
    if check == "token_budget":
        limit = grader.get("limit", grader.get("max"))
        tokens = stream.total_tokens
        if tokens is None:
            return False, "no usage in result event"
        ok = tokens <= int(limit)
        return ok, "%d total tokens (budget %s)" % (tokens, limit)
    return False, "unknown transcript check %r" % check


def grade_state_check(grader, ctx):
    """Run `command`; compare stdout per expect mode exact|regex|json
    (default exact). Optional expect_exit_code. Optional `cwd` selects the
    working directory: workspace (default) | plugin_dir | evals_dir —
    plugin_dir is what dogfood-style suites use to reach the plugin's own
    scripts with relative paths."""
    cwd_key = grader.get("cwd", "workspace")
    cwd_map = {
        "workspace": ctx["workspace"],
        "plugin_dir": os.path.abspath(ctx["plugin_dir"]) if ctx.get("plugin_dir") else ctx["workspace"],
        "evals_dir": ctx["evals_dir"],
    }
    if cwd_key not in cwd_map:
        return False, "state_check has unknown cwd %r (workspace|plugin_dir|evals_dir)" % cwd_key
    ws = cwd_map[cwd_key]
    command = grader.get("command")
    if not command:
        return False, "state_check has no `command`"
    timeout = int(grader.get("timeout_s", 60))
    try:
        proc = subprocess.run(["bash", "-c", command], cwd=ws,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "state_check command timed out after %ds" % timeout
    if "expect_exit_code" in grader:
        if proc.returncode != int(grader["expect_exit_code"]):
            return False, "exit code %d (expected %s); stderr: %s" % (
                proc.returncode, grader["expect_exit_code"], proc.stderr[:300])
        if "expect" not in grader:
            return True, "exit code %d as expected" % proc.returncode
    out = proc.stdout.strip()
    expect = grader.get("expect")
    mode = grader.get("match", "exact")
    if mode == "exact":
        ok = out == str(expect).strip()
        return ok, "stdout %r vs expected %r" % (out[:200], str(expect)[:200])
    if mode == "regex":
        ok = re.search(str(expect), proc.stdout, re.MULTILINE) is not None
        return ok, "stdout %s /%s/" % ("matches" if ok else "does not match", expect)
    if mode == "json":
        try:
            actual = json.loads(proc.stdout)
        except ValueError:
            return False, "stdout is not valid JSON: %r" % out[:200]
        ok, why = json_subset_match(expect, actual)
        return ok, why or "structural subset matched"
    return False, "unknown state_check match mode %r" % mode


def load_judge_spec(evals_dir, spec_path):
    """judges/*.yaml: {prompt (placeholders {input}/{completion}/{criteria}),
    choice_strings, choice_scores, eval_type: cot_classify, model, threshold}."""
    p = spec_path
    if not os.path.isabs(p):
        cand = os.path.normpath(os.path.join(evals_dir, spec_path))
        p = cand if os.path.isfile(cand) else os.path.normpath(
            os.path.join(evals_dir, "tasks", spec_path))
    if not os.path.isfile(p):
        raise HarnessError("judge spec not found: %r" % spec_path)
    spec = load_structured(p)
    if not isinstance(spec, dict) or not spec.get("prompt"):
        raise HarnessError("judge spec %s must be a mapping with `prompt`" % p)
    spec["_path"] = p
    choices = list(spec.get("choice_strings") or ["Pass", "Fail"])
    if "Unknown" not in choices:
        choices.append("Unknown")  # Unknown is ALWAYS a legal verdict
    spec["_choices"] = choices
    return spec


def run_judge(spec, variables, ctx):
    """Render the judge spec and invoke a pinned cheap model via
    `claude -p --bare --output-format json --json-schema ...`.
    Returns dict {choice, score, rationale, evidence, cost_usd, passed}."""
    prompt = str(spec["prompt"])
    for key, val in variables.items():
        prompt = prompt.replace("{%s}" % key, str(val))
    prompt += ("\n\nAnswer with a JSON object: choice (one of: %s), rationale "
               "(cite specific evidence), evidence (verbatim quote). If you "
               "cannot determine the verdict from the material, choose "
               "\"Unknown\" — never guess." % ", ".join(spec["_choices"]))
    schema = json.loads(json.dumps(JUDGE_SCHEMA))
    schema["properties"]["choice"]["enum"] = spec["_choices"]
    model = str(spec.get("model", DEFAULT_JUDGE_MODEL))
    cmd = ["claude", "-p", prompt, "--bare", "--output-format", "json",
           "--json-schema", json.dumps(schema), "--model", model]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              env=hermetic_env(),
                              timeout=int(spec.get("timeout_s", 300)))
    except subprocess.TimeoutExpired:
        return {"choice": "Unknown", "score": 0.0, "rationale": "judge call timed out",
                "evidence": "", "cost_usd": 0.0, "passed": False, "model": model}
    payload = {}
    try:
        payload = json.loads(proc.stdout)
    except ValueError:
        pass
    structured = payload.get("structured_output") or {}
    choice = structured.get("choice", "Unknown")
    scores = spec.get("choice_scores") or {}
    if choice in scores:
        score = float(scores[choice])
    elif choice == "Unknown":
        score = 0.0
    else:
        score = 1.0 if choice in ("Pass", "Yes", "Correct", "True") else 0.0
    threshold = float(spec.get("threshold", 1.0))
    return {
        "choice": choice,
        "score": score,
        "rationale": structured.get("rationale", proc.stderr[:300] if proc.returncode else ""),
        "evidence": structured.get("evidence", ""),
        "cost_usd": float(payload.get("total_cost_usd") or 0.0),
        "passed": choice != "Unknown" and score >= threshold,
        "model": model,
    }


def grade_judge(grader, ctx):
    spec = load_judge_spec(ctx["evals_dir"], str(grader["spec"]))
    judge_model = str(spec.get("model", DEFAULT_JUDGE_MODEL))
    target_model = ctx.get("target", {}).get("model")
    if target_model and str(target_model) == judge_model:
        # Self-grading is the classic judge failure mode; refuse loudly rather
        # than emit a silently biased score (same rule judge.py enforces).
        return False, ("judge config error: judge model %r equals the target "
                       "model — pin a different (cheaper) judge model in the "
                       "judge spec" % judge_model)
    stream = ctx.get("stream")
    completion = ctx.get("completion_override")
    if completion is None:
        completion = stream.result_text if stream else ""
    variables = {
        "input": ctx.get("instruction") or "",
        "completion": completion,
        "criteria": grader.get("criteria") or grader.get("dimension") or
                    spec.get("criteria") or "",
    }
    verdict = run_judge(spec, variables, ctx)
    ctx["log"].emit("judge", task=ctx["task_id"], trial=ctx["trial"],
                    spec=os.path.basename(spec["_path"]), model=verdict["model"],
                    choice=verdict["choice"], score=verdict["score"],
                    rationale=verdict["rationale"], evidence=verdict["evidence"],
                    cost_usd=verdict["cost_usd"])
    ctx["budget"].add(verdict["cost_usd"])
    detail = "judge %s → %s (score %.2f): %s" % (
        os.path.basename(spec["_path"]), verdict["choice"], verdict["score"],
        verdict["rationale"][:200])
    return verdict["passed"], detail


def detect_activation(stream, kind, name):
    """Detect component activation in one trial stream.
    skill  → Skill tool_use whose input names the skill (also matches a
             SlashCommand-style invocation carrying the skill name);
    agent  → Task/Agent tool_use whose subagent_type/agent name matches.
    Hook firings are NOT visible in stream-json — use state_check instead."""
    short = name.split(":")[-1]
    for tu in stream.tool_uses:
        tname = tu["name"]
        ti = tu["input"] or {}
        blob = json.dumps(ti)
        if kind == "skill":
            if tname == "Skill" and (short in blob or name in blob):
                return True
            if tname == "SlashCommand" and (short in blob or name in blob):
                return True
        elif kind == "agent":
            if tname in ("Task", "Agent"):
                sub = str(ti.get("subagent_type") or ti.get("agent") or "")
                if sub == short or sub == name or short in blob:
                    return True
    return False


def grade_trigger(grader, ctx):
    """Fire N paraphrase prompts through claude -p; measure activation
    precision/recall for the named component. `should` prompts must activate,
    `should_not` must not. Pass iff precision ≥ min_precision (default 1.0)
    and recall ≥ min_recall (default 1.0)."""
    kind = str(grader.get("kind", "skill"))
    name = str(grader.get("component", grader.get("skill", grader.get("agent", ""))))
    if not name:
        return False, "trigger grader needs `component` (and `kind: skill|agent`)"
    if kind not in ("skill", "agent"):
        return False, ("trigger kind %r unsupported: hook firings are not in "
                       "stream-json — trigger-test hooks via state_check on "
                       "their side effects" % kind)
    should = [str(p) for p in grader.get("should") or []]
    should_not = [str(p) for p in grader.get("should_not") or []]
    timeout_s = int(grader.get("timeout_s", ctx["task"].get("timeout_s", DEFAULT_TIMEOUT_S)))
    tp = fn = fp = tn = unverified = 0
    details = []
    for i, prompt in enumerate(should + should_not):
        expect_fire = i < len(should)
        cmd = build_claude_cmd(ctx["target"], prompt, ctx["plugin_dir"], ctx["evals_dir"])
        tpath = os.path.join(ctx["transcripts_dir"],
                             "%s-t%d-trigger%d.jsonl" % (ctx["task_id"], ctx["trial"], i))
        stream, code, timed_out = run_claude(cmd, ctx["workspace"], timeout_s, tpath)
        ctx["budget"].add(stream.cost_usd)
        fired = detect_activation(stream, kind, name)
        infra = timed_out or code == 143 or stream.api_retries > 0
        if infra and not fired:
            # Infra fairness (same doctrine as trials): a probe disturbed by
            # timeout/api_retry that did NOT fire proves nothing — exclude it
            # from the precision/recall denominators instead of scoring it.
            unverified += 1
            details.append("UNVERIFIED probe[%d] (infra: timeout=%s retries=%d)"
                           % (i, timed_out or code == 143, stream.api_retries))
            continue
        if expect_fire and fired:
            tp += 1
        elif expect_fire:
            fn += 1
            details.append("MISS should[%d]: %r" % (i, prompt[:80]))
        elif fired:
            fp += 1
            details.append("FALSE-FIRE should_not[%d]: %r" % (i - len(should), prompt[:80]))
        else:
            tn += 1
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    ctx["log"].emit("metric", name="trigger_precision", value=round(precision, 4),
                    task=ctx["task_id"], trial=ctx["trial"], component=name)
    ctx["log"].emit("metric", name="trigger_recall", value=round(recall, 4),
                    task=ctx["task_id"], trial=ctx["trial"], component=name)
    ctx["trigger_stats"].append({"task": ctx["task_id"], "component": name,
                                 "precision": precision, "recall": recall,
                                 "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                                 "unverified": unverified})
    ok = (precision >= float(grader.get("min_precision", 1.0)) and
          recall >= float(grader.get("min_recall", 1.0)))
    return ok, "precision=%.2f recall=%.2f %s" % (precision, recall,
                                                  "; ".join(details[:4]))


GRADERS = {
    "workspace": grade_workspace,
    "transcript": grade_transcript,
    "state_check": grade_state_check,
    "judge": grade_judge,
    "trigger": grade_trigger,
}


# --------------------------------------------------------------------------
# cost budget
# --------------------------------------------------------------------------

class Budget:
    """Cumulative total_cost_usd across trial runs and judge calls.
    When --max-cost-usd is crossed, `exceeded` flips and the run aborts:
    no new work is scheduled, remaining tasks record status=skipped."""

    def __init__(self, max_cost_usd=None):
        self.max = max_cost_usd
        self.total = 0.0
        self._lock = threading.Lock()
        self.exceeded = False

    def add(self, cost):
        with self._lock:
            self.total += float(cost or 0.0)
            if self.max is not None and self.total > self.max:
                self.exceeded = True
            return self.total


# --------------------------------------------------------------------------
# trial + task execution
# --------------------------------------------------------------------------

def run_trial(task, trial, target, args, paths, log, budget, trigger_stats,
              reference_mode=False):
    """Execute one task×trial: stage isolation, launch claude (unless
    reference mode), grade, teardown (finally). Returns a trial record."""
    task_id = task["id"]
    rec = {"task": task_id, "trial": trial, "status": "error", "cost_usd": 0.0,
           "turns": None, "tokens": None, "duration_s": 0.0,
           "checks": [], "unverified_reason": None}
    t0 = time.time()
    task = dict(task)
    task["_trial"] = trial
    ws = Workspace(task, paths["work"], paths["worktree_ledger"])
    try:
        workspace = ws.stage()
        answers = task.get("elicitation_answers")
        if isinstance(answers, dict) and answers:
            # Contract with generated Elicitation auto-answer hooks: the harness
            # stages the task's canned answers where the hook looks for them.
            ed = os.path.join(workspace, ".forge-eval")
            os.makedirs(ed, exist_ok=True)
            with open(os.path.join(ed, "elicitation-answers.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(answers, fh, indent=2)
        if reference_mode:
            _overlay_reference(task, workspace)
        stream, exit_code, timed_out = None, 0, False
        if not reference_mode and task.get("launch", "claude") != "none":
            instruction = task.get("_instruction") or task.get("desc", "")
            if not target.get("plugin", True):
                # No-plugin (RED-baseline) sessions cannot expand the plugin's
                # slash invocation — the CLI hard-fails "Unknown command" at
                # turn 0, measuring nothing. Strip a leading /plugin:skill
                # token so bare Claude genuinely attempts the identical
                # problem text (the honest with/without-plugin denominator).
                instruction = re.sub(r"\A/[A-Za-z0-9:_-]+[ \t]*", "",
                                     instruction, count=1)
            cmd = build_claude_cmd(target, instruction, args.plugin_dir,
                                   paths["evals_dir"])
            tpath = os.path.join(paths["transcripts"],
                                 "%s-t%d.jsonl" % (task_id, trial))
            stream, exit_code, timed_out = run_claude(
                cmd, workspace, int(task.get("timeout_s", DEFAULT_TIMEOUT_S)), tpath)
            rec["cost_usd"] = stream.cost_usd
            rec["turns"] = stream.num_turns
            rec["tokens"] = stream.total_tokens
            budget.add(stream.cost_usd)
            # --- system/init gate -----------------------------------------
            gate_reason = _init_gate_reason(stream, target, args.plugin_dir,
                                            paths["evals_dir"])
            if gate_reason:
                rec["status"] = "aborted"
                rec["unverified_reason"] = gate_reason
                log.emit("error", where="init-gate", task=task_id, trial=trial,
                         message=gate_reason)
                return rec
            if timed_out or exit_code == 143:
                rec["status"] = "timeout"
                log.emit("error", where="timeout", task=task_id, trial=trial,
                         message="SIGTERM after %ss (exit 143)" % task.get("timeout_s"))
                return rec
            if stream.api_retries > 0:
                rec["status"] = "unverified"
                rec["unverified_reason"] = ("%d api_retry events — infra noise, "
                                            "excluded from pass rates"
                                            % stream.api_retries)
                return rec
        # --- grading ------------------------------------------------------
        ctx = {
            "workspace": workspace, "stream": stream, "exit_code": exit_code,
            "evals_dir": paths["evals_dir"], "task": task, "task_id": task_id,
            "trial": trial, "instruction": task.get("_instruction") or "",
            "target": target, "plugin_dir": args.plugin_dir, "log": log,
            "budget": budget, "transcripts_dir": paths["transcripts"],
            "trigger_stats": trigger_stats,
            "completion_override": _reference_completion(task) if reference_mode else None,
        }
        weighted_total = weighted_earned = 0.0
        all_pass = True
        for gi, grader in enumerate(task["graders"]):
            gtype = grader["type"]
            if reference_mode and gtype in ("transcript", "trigger"):
                rec["checks"].append({"grader": gi, "type": gtype,
                                      "passed": None, "detail": "skipped in reference mode"})
                continue
            if budget.exceeded:
                rec["checks"].append({"grader": gi, "type": gtype,
                                      "passed": None, "detail": "skipped: cost budget exceeded"})
                all_pass = False
                continue
            try:
                passed, detail = GRADERS[gtype](grader, ctx)
            except HarnessError as exc:
                passed, detail = False, "grader error: %s" % exc
                log.emit("error", where="grader", task=task_id, trial=trial,
                         message=str(exc))
            weight = float(grader.get("weight", 1.0))
            weighted_total += weight
            weighted_earned += weight if passed else 0.0
            all_pass = all_pass and bool(passed)
            rec["checks"].append({"grader": gi, "type": gtype,
                                  "check": grader.get("check"),
                                  "passed": bool(passed), "detail": detail})
            log.emit("check", task=task_id, trial=trial, grader=gi,
                     check=grader.get("check", gtype), passed=bool(passed),
                     detail=detail)
        if str(task.get("scoring", "binary")).startswith("weighted"):
            threshold = float(task.get("threshold", 1.0))
            score = (weighted_earned / weighted_total) if weighted_total else 0.0
            rec["score"] = round(score, 4)
            rec["status"] = "pass" if score >= threshold else "fail"
        else:
            rec["status"] = "pass" if all_pass else "fail"
        return rec
    except subprocess.CalledProcessError as exc:
        rec["status"] = "error"
        log.emit("error", where="trial", task=task_id, trial=trial,
                 message="subprocess failed: %s | %s" % (exc, (exc.stderr or "")[:300]))
        return rec
    except HarnessError as exc:
        rec["status"] = "error"
        log.emit("error", where="trial", task=task_id, trial=trial, message=str(exc))
        return rec
    finally:
        rec["duration_s"] = round(time.time() - t0, 1)
        ws.teardown()  # MANDATORY teardown, even on crash paths
        for metric in ("cost_usd", "turns", "tokens"):
            if rec.get(metric) is not None:
                log.emit("metric", name=metric, value=rec[metric],
                         task=task_id, trial=trial)
        log.emit("sample", task=task_id, trial=trial, status=rec["status"],
                 cost_usd=rec["cost_usd"], turns=rec["turns"],
                 tokens=rec["tokens"], duration_s=rec["duration_s"],
                 unverified_reason=rec["unverified_reason"])


def _effective_plugin_dir(target, plugin_dir, evals_dir):
    """The plugin dir a trial actually loads: CLI --plugin-dir wins; else a
    string plugin_dir in the target yaml (resolved against evals/) lets
    vendored suites run standalone. None when target sets plugin: false or
    no path is available."""
    if not target.get("plugin", True):
        return None
    eff = plugin_dir or target.get("plugin_dir")
    if not eff or not isinstance(eff, str):
        return None
    if not os.path.isabs(eff) and not plugin_dir:
        eff = os.path.join(evals_dir, eff)
    return os.path.abspath(eff)


def _init_gate_reason(stream, target, plugin_dir, evals_dir=None):
    """Abort reason if the system/init gate fails, else None. Keys omitted in
    the init event mean clean (per docs) — only non-empty arrays fail."""
    if stream.init is None:
        return "no system/init event in stream (claude failed to start?)"
    if stream.plugin_errors:
        return "plugin_errors non-empty: %s" % json.dumps(stream.plugin_errors)[:400]
    if stream.mcp_server_errors:
        return "mcp_server_errors non-empty: %s" % json.dumps(stream.mcp_server_errors)[:400]
    eff = _effective_plugin_dir(target, plugin_dir, evals_dir or os.getcwd())
    if eff:
        expected = _plugin_name(eff)
        if expected and not stream.plugin_loaded(expected):
            return "plugin %r absent from system/init plugins[]" % expected
    return None


def _plugin_name(plugin_dir):
    manifest = read_json(os.path.join(plugin_dir, ".claude-plugin", "plugin.json"))
    if isinstance(manifest, dict):
        return manifest.get("name")
    return None


def _overlay_reference(task, workspace):
    """reference mode: copy tasks/<id>/reference/ over the staged fixtures,
    simulating a completed solution. reference/ itself is never visible to
    agents — it lives outside every staged workspace."""
    ref = os.path.join(task["_dir"], str(task.get("reference", "./reference/")).strip("./"))
    if not os.path.isdir(ref):
        raise HarnessError("task %r has no reference/ directory — every task "
                           "requires a reference solution" % task["id"])
    for dirpath, _dirnames, filenames in os.walk(ref):
        for fn in filenames:
            src = os.path.join(dirpath, fn)
            rel = os.path.relpath(src, ref)
            dst = os.path.join(workspace, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)


def _reference_completion(task):
    """Text handed to judge graders in reference mode."""
    for name in ("solution.md", "solution.txt", "README.md"):
        p = os.path.join(task["_dir"], "reference", name)
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                return fh.read()
    return "(reference artifacts staged into workspace)"


# --------------------------------------------------------------------------
# aggregation + reporting
# --------------------------------------------------------------------------

def aggregate(task_order, trial_records, red_mode=False):
    """Fold trial records into per-task and suite-level stats."""
    by_task = {}
    for rec in trial_records:
        by_task.setdefault(rec["task"], []).append(rec)
    tasks_out = {}
    n_pass_all = n_pass_any = n_graded = 0
    for tid in task_order:
        recs = sorted(by_task.get(tid, []), key=lambda r: r["trial"])
        verified = [r for r in recs if r["status"] in ("pass", "fail", "timeout")]
        passes = [r for r in verified if r["status"] == "pass"]
        entry = {
            "trials": len(recs),
            "verified_trials": len(verified),
            "unverified_trials": len([r for r in recs if r["status"] == "unverified"]),
            "statuses": [r["status"] for r in recs],
            "cost_usd": round(sum(r["cost_usd"] for r in recs), 4),
            "turns": [r["turns"] for r in recs],
            "tokens": [r["tokens"] for r in recs],
            "pass_rate": round(len(passes) / len(verified), 4) if verified else None,
        }
        if not verified:
            entry["outcome"] = "unverified"
            tasks_out[tid] = entry
            continue
        n_graded += 1
        pass_all = len(passes) == len(verified)
        pass_any = len(passes) >= 1
        n_pass_all += 1 if pass_all else 0
        n_pass_any += 1 if pass_any else 0
        entry["pass_all_trials"] = pass_all
        entry["pass_any_trial"] = pass_any
        tasks_out[tid] = entry
    return tasks_out, n_graded, n_pass_all, n_pass_any


def finalize_run(args, suite, version, tasks, trial_records, trigger_stats,
                 paths, log, budget, red_mode=False):
    """Compute summary.json, report.html, scoreboard; return (line, exit_code)."""
    task_order = [t["id"] for t in tasks]
    task_meta = {t["id"]: t for t in tasks}
    tasks_out, n_graded, n_pass_all, n_pass_any = aggregate(task_order, trial_records)

    # per-task verdict per its own metric
    n_task_pass = 0
    for tid, entry in tasks_out.items():
        if entry.get("outcome") == "unverified":
            entry["passed"] = False
            continue
        metric = str(task_meta[tid].get("metric", "pass^k"))
        entry["metric"] = metric
        entry["passed"] = entry["pass_any_trial"] if metric.startswith("pass@") \
            else entry["pass_all_trials"]
        n_task_pass += 1 if entry["passed"] else 0

    k = args.trials or max((t.get("trials", DEFAULT_TRIALS) for t in tasks),
                           default=DEFAULT_TRIALS)
    pass_at_k = (n_pass_any / n_graded) if n_graded else 0.0
    pass_pow_k = (n_pass_all / n_graded) if n_graded else 0.0

    if red_mode:
        # RED baseline semantics: PASS means NOTHING passed without the plugin.
        no_signal = [tid for tid, e in tasks_out.items() if e.get("pass_any_trial")]
        result = "PASS" if (n_graded > 0 and not no_signal and not budget.exceeded) else "FAIL"
    else:
        result = "PASS" if (n_graded == len(task_order) and n_graded > 0 and
                            n_task_pass == n_graded and not budget.exceeded) else "FAIL"
        no_signal = []

    trig_agg = None
    if trigger_stats:
        trig_agg = {
            "precision": round(sum(s["precision"] for s in trigger_stats) /
                               len(trigger_stats), 4),
            "recall": round(sum(s["recall"] for s in trigger_stats) /
                            len(trigger_stats), 4),
            "per_component": trigger_stats,
        }

    line = SCOREBOARD_FMT.format(suite=suite["name"], version=version,
                                 passed=n_task_pass, total=len(task_order),
                                 k=k, passk=pass_pow_k, cost=budget.total,
                                 result=result)
    summary = {
        "suite": suite["name"], "version": "v%d" % version,
        "target": args.target, "mode": "red" if red_mode else args.command,
        "started": paths["started"], "finished": now_iso(),
        "plugin_dir": args.plugin_dir,
        "trials_default": k,
        "tasks": tasks_out,
        "pass_at_k": round(pass_at_k, 4),
        "pass_pow_k": round(pass_pow_k, 4),
        "tasks_passed": n_task_pass, "tasks_total": len(task_order),
        "tasks_graded": n_graded,
        "no_signal_tasks": no_signal,
        "trigger": trig_agg,
        "cost_usd": round(budget.total, 4),
        "budget_exceeded": budget.exceeded,
        "max_cost_usd": budget.max,
        "result": result,
        "scoreboard": line,
    }
    write_json(paths["summary"], summary)
    write_report_html(paths["report"], summary, trial_records)
    _append_scoreboard(line)
    return line, (0 if result == "PASS" else 1)


def _append_scoreboard(line):
    forge_dir = os.path.join(os.getcwd(), ".forge")
    try:
        os.makedirs(forge_dir, exist_ok=True)
        with open(os.path.join(forge_dir, "last-scoreboard.txt"), "a",
                  encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass  # scoreboard file is best-effort; stdout line is the contract


_STATUS_COLORS = {"pass": "#1a7f37", "fail": "#cf222e", "timeout": "#9a6700",
                  "unverified": "#6e7781", "error": "#cf222e",
                  "aborted": "#cf222e", "skipped": "#6e7781"}


def write_report_html(path, summary, trial_records):
    """Self-contained report: inline CSS only, zero external assets."""
    e = _html.escape
    by_task = {}
    for rec in trial_records:
        by_task.setdefault(rec["task"], []).append(rec)
    rows = []
    for tid in summary["tasks"]:
        entry = summary["tasks"][tid]
        cells = []
        for rec in sorted(by_task.get(tid, []), key=lambda r: r["trial"]):
            color = _STATUS_COLORS.get(rec["status"], "#6e7781")
            checks = "".join(
                "<li>%s <b>%s</b>: %s</li>" % (
                    e(str(c.get("type"))),
                    "PASS" if c.get("passed") else
                    ("skip" if c.get("passed") is None else "FAIL"),
                    e(str(c.get("detail", ""))[:300]))
                for c in rec.get("checks", []))
            cells.append(
                "<td style='border:1px solid #d0d7de;padding:6px;vertical-align:top'>"
                "<span style='color:%s;font-weight:600'>%s</span>"
                "<br><small>$%.3f · %s turns · %s tok · %.0fs</small>"
                "<details><summary>checks</summary><ul style='margin:4px 0;"
                "padding-left:18px;font-size:12px'>%s</ul></details></td>"
                % (color, e(rec["status"]), rec["cost_usd"],
                   rec["turns"] if rec["turns"] is not None else "?",
                   rec["tokens"] if rec["tokens"] is not None else "?",
                   rec["duration_s"], checks))
        verdict = "PASS" if entry.get("passed") else "FAIL"
        vcolor = _STATUS_COLORS["pass" if entry.get("passed") else "fail"]
        rows.append("<tr><td style='border:1px solid #d0d7de;padding:6px'>"
                    "<b>%s</b><br><span style='color:%s'>%s</span> "
                    "<small>(%s)</small></td>%s</tr>"
                    % (e(tid), vcolor, verdict, e(str(entry.get("metric", ""))),
                       "".join(cells)))
    trig = summary.get("trigger")
    trig_html = ""
    if trig:
        trig_html = ("<p><b>Trigger:</b> precision %.2f · recall %.2f "
                     "over %d component measurements</p>"
                     % (trig["precision"], trig["recall"],
                        len(trig["per_component"])))
    rcolor = _STATUS_COLORS["pass" if summary["result"] == "PASS" else "fail"]
    doc = """<!doctype html><html><head><meta charset="utf-8">
<title>FORGE_EVAL %s %s</title>
<style>body{font-family:-apple-system,system-ui,Segoe UI,sans-serif;margin:24px;
max-width:1100px}table{border-collapse:collapse;width:100%%;font-size:14px}
code{background:#f6f8fa;padding:2px 5px;border-radius:4px}
@media (prefers-color-scheme: dark){body{background:#0d1117;color:#e6edf3}
code{background:#161b22}td,th{border-color:#30363d!important}}</style></head><body>
<h1>FORGE_EVAL — suite <code>%s</code> %s</h1>
<p style="font-size:20px;color:%s;font-weight:700">%s</p>
<p><code>%s</code></p>
<p>pass@k=%.2f · pass^k=%.2f · tasks %d/%d · cost $%.2f%s · %s → %s</p>
%s
<table><tr><th style="border:1px solid #d0d7de;padding:6px;text-align:left">task</th>
<th style="border:1px solid #d0d7de;padding:6px;text-align:left" colspan="12">trials</th></tr>
%s</table>
<p><small>Generated by plugin-forge run.py — events.jsonl and transcripts/ sit
next to this file. Unverified trials (api_retry infra noise) are excluded from
all pass-rate denominators.</small></p></body></html>""" % (
        e(summary["suite"]), e(summary["version"]), e(summary["suite"]),
        e(summary["version"]), rcolor, e(summary["result"]),
        e(summary["scoreboard"]), summary["pass_at_k"], summary["pass_pow_k"],
        summary["tasks_passed"], summary["tasks_total"], summary["cost_usd"],
        (" (BUDGET EXCEEDED, max $%.2f)" % summary["max_cost_usd"])
        if summary.get("budget_exceeded") else "",
        e(summary["started"]), e(summary["finished"]), trig_html, "".join(rows))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(doc)


# --------------------------------------------------------------------------
# subcommand: run / red / reference
# --------------------------------------------------------------------------

def cmd_run(args):
    evals_dir = os.path.abspath(args.evals_dir or default_evals_dir())
    if not os.path.isdir(evals_dir):
        raise HarnessError("evals dir not found: %s (use --evals-dir)" % evals_dir)
    suite, version = resolve_suite(evals_dir, args.suite)
    red_mode = args.command == "red"
    reference_mode = args.command == "reference"
    target_name = args.target or ("no-plugin" if red_mode else "default")
    if reference_mode:
        target = {"name": "reference", "plugin": False, "bare": True,
                  "_path": os.path.join(evals_dir, "targets", "reference.yaml")}
    else:
        target = load_target(evals_dir, target_name)
    if red_mode and target.get("plugin", True):
        target = dict(target)
        target["plugin"] = False  # red baseline NEVER loads the plugin under test

    task_ids = [str(t) for t in suite["tasks"]]
    if args.task:
        if args.task not in task_ids:
            raise HarnessError("task %r not in suite %r (tasks: %s)" %
                               (args.task, args.suite, task_ids))
        task_ids = [args.task]
    if args.dry_run:
        task_ids = task_ids[:1]
    tasks = [load_task(evals_dir, tid) for tid in task_ids]  # validates ALL

    ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = os.path.abspath(args.out or os.path.join("runs", ts))
    # Trial workspaces are staged OUTSIDE the project tree: a workspace under
    # runs/<ts>/work would let a trial agent traverse ../../.. into
    # evals*/tasks/*/reference/ and copy golden marker strings (Audit 5 /
    # L03-at-runtime). The ledger stays under runs/ so `doctor` can reap.
    work_root = os.path.join(tempfile.mkdtemp(prefix="forge-eval-work-"),
                             "trials")
    paths = {
        "out": out_dir,
        "work": work_root,
        "transcripts": os.path.join(out_dir, "transcripts"),
        "events": os.path.join(out_dir, "events.jsonl"),
        "summary": os.path.join(out_dir, "summary.json"),
        "report": os.path.join(out_dir, "report.html"),
        "worktree_ledger": os.path.join(out_dir, "work", ".worktrees.jsonl"),
        "evals_dir": evals_dir,
        "started": now_iso(),
    }
    for key in ("out", "work", "transcripts"):
        os.makedirs(paths[key], exist_ok=True)
    log = EventLog(paths["events"])
    budget = Budget(args.max_cost_usd)
    trigger_stats = []
    trial_records = []
    rec_lock = threading.Lock()

    units = []
    for task in tasks:
        n_trials = 1 if (args.dry_run or reference_mode) else \
            int(args.trials or task.get("trials", DEFAULT_TRIALS))
        for trial in range(1, n_trials + 1):
            units.append((task, trial))

    def _one(unit):
        task, trial = unit
        if budget.exceeded:
            rec = {"task": task["id"], "trial": trial, "status": "skipped",
                   "cost_usd": 0.0, "turns": None, "tokens": None,
                   "duration_s": 0.0, "checks": [],
                   "unverified_reason": "cost budget exceeded"}
            log.emit("sample", task=task["id"], trial=trial, status="skipped",
                     cost_usd=0.0, turns=None, tokens=None, duration_s=0.0,
                     unverified_reason="cost budget exceeded")
        else:
            rec = run_trial(task, trial, target, args, paths, log, budget,
                            trigger_stats, reference_mode=reference_mode)
        with rec_lock:
            trial_records.append(rec)

    jobs = min(max(1, args.jobs or 1), MAX_JOBS)
    if jobs == 1 or len(units) == 1:
        for unit in units:
            _one(unit)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
            list(pool.map(_one, units))

    if budget.exceeded:
        log.emit("error", where="budget",
                 message="cumulative cost $%.2f crossed --max-cost-usd %.2f — run aborted"
                 % (budget.total, budget.max))
    line, code = finalize_run(args, suite, version, tasks, trial_records,
                              trigger_stats, paths, log, budget,
                              red_mode=red_mode)
    log.close()
    if red_mode:
        summary = read_json(paths["summary"]) or {}
        for tid in summary.get("no_signal_tasks", []):
            print("NO-SIGNAL: task %s passes WITHOUT the plugin — harden or "
                  "drop it before arming" % tid)
    print("run artifacts: %s" % out_dir)
    print(line)
    return code


# --------------------------------------------------------------------------
# subcommand: smoke
# --------------------------------------------------------------------------

def cmd_smoke(args):
    """Delegate to ../smoke/smoke.py relative to this install (plugin layout:
    scripts/harness/run.py → scripts/smoke/smoke.py). The vendored copy
    (evals/bin/run.py) usually has no sibling smoke/, so a built-in minimal
    init-gate check runs instead."""
    here = os.path.dirname(os.path.abspath(__file__))
    smoke_py = os.path.join(os.path.dirname(here), "smoke", "smoke.py")
    if os.path.isfile(smoke_py):
        argv = [sys.executable, smoke_py]
        if args.plugin_dir:
            argv += ["--plugin-dir", args.plugin_dir]
        argv += args.smoke_args or []
        return subprocess.call(argv)
    # built-in minimal gate: does the plugin load cleanly in a bare session?
    if not args.plugin_dir:
        raise HarnessError("smoke needs --plugin-dir")
    print("smoke: no ../smoke/smoke.py found — running built-in init gate")
    cmd = ["claude", "-p", "Reply with exactly: OK", "--bare",
           "--plugin-dir", os.path.abspath(args.plugin_dir),
           "--output-format", "stream-json", "--verbose"]
    stream, code, timed_out = run_claude(cmd, os.getcwd(), 180)
    reason = _init_gate_reason(stream, {"plugin": True}, args.plugin_dir)
    name = _plugin_name(args.plugin_dir) or os.path.basename(args.plugin_dir)
    if reason:
        print("SMOKE FAIL: %s" % reason)
        print("FORGE_EVAL: suite=smoke version=v0 passed=0/1 pass^1=0.00 "
              "cost_usd=%.2f RESULT=FAIL" % stream.cost_usd)
        return 1
    print("SMOKE OK: plugin %r loaded, no plugin_errors/mcp_server_errors" % name)
    print("FORGE_EVAL: suite=smoke version=v0 passed=1/1 pass^1=1.00 "
          "cost_usd=%.2f RESULT=PASS" % stream.cost_usd)
    return 0


# --------------------------------------------------------------------------
# subcommand: metaeval  (judge-vs-human-labels agreement)
# --------------------------------------------------------------------------

def cmd_metaeval(args):
    """labels/labels.jsonl lines: {"judge": "<spec basename or path>",
    "input": "...", "completion": "...", "criteria": "...", "label": "<choice>"}.
    Runs each labeled sample through its judge spec; agreement = fraction of
    samples where judge choice == human label. Gate: ≥ 0.85 (arm-evals
    refuses to freeze uncalibrated judges)."""
    evals_dir = os.path.abspath(args.evals_dir or default_evals_dir())
    labels_path = os.path.join(evals_dir, "labels", "labels.jsonl")
    if not os.path.isfile(labels_path):
        raise HarnessError("no labels file at %s — hand-label 10–20 transcripts "
                           "first (see arm-evals gate 3)" % labels_path)
    samples = []
    with open(labels_path, "r", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            try:
                samples.append(json.loads(line))
            except ValueError:
                raise HarnessError("labels.jsonl line %d is not valid JSON" % (i + 1))
    if args.judge:
        samples = [s for s in samples
                   if args.judge in str(s.get("judge", ""))]
    if not samples:
        raise HarnessError("no labeled samples%s" %
                           (" for judge %r" % args.judge if args.judge else ""))
    budget = Budget(args.max_cost_usd)
    per_judge = {}
    for s in samples:
        spec_name = str(s.get("judge", ""))
        spec = load_judge_spec(evals_dir, spec_name if "/" in spec_name
                               else os.path.join("judges", spec_name))
        verdict = run_judge(spec, {
            "input": s.get("input", ""),
            "completion": s.get("completion", ""),
            "criteria": s.get("criteria", spec.get("criteria", "")),
        }, {})
        budget.add(verdict["cost_usd"])
        agree = str(verdict["choice"]) == str(s.get("label"))
        bucket = per_judge.setdefault(spec_name, {"n": 0, "agree": 0,
                                                  "disagreements": []})
        bucket["n"] += 1
        bucket["agree"] += 1 if agree else 0
        if not agree:
            bucket["disagreements"].append(
                {"human": s.get("label"), "judge": verdict["choice"],
                 "rationale": verdict["rationale"][:200],
                 "input": str(s.get("input", ""))[:120]})
        if budget.exceeded:
            print("metaeval aborted: --max-cost-usd crossed", file=sys.stderr)
            break
    overall_n = sum(b["n"] for b in per_judge.values())
    overall_agree = sum(b["agree"] for b in per_judge.values())
    agreement = overall_agree / overall_n if overall_n else 0.0
    all_pass = True
    for name, b in sorted(per_judge.items()):
        a = b["agree"] / b["n"] if b["n"] else 0.0
        flag = "OK" if a >= 0.85 else "BELOW GATE (0.85)"
        all_pass = all_pass and a >= 0.85
        print("FORGE_METAEVAL: judge=%s agreement=%.2f n=%d %s" % (name, a, b["n"], flag))
        for d in b["disagreements"][:5]:
            print("  disagreement: human=%s judge=%s | %s" %
                  (d["human"], d["judge"], d["rationale"]))
    result = "PASS" if (all_pass and overall_n > 0) else "FAIL"
    print("FORGE_EVAL: suite=metaeval version=v0 passed=%d/%d pass^1=%.2f "
          "cost_usd=%.2f RESULT=%s" % (overall_agree, overall_n, agreement,
                                       budget.total, result))
    return 0 if result == "PASS" else 1


# --------------------------------------------------------------------------
# subcommand: graduate  (saturation doctrine)
# --------------------------------------------------------------------------

def _emit_simple_yaml(obj, indent=0):
    """Emit the flat suite-file shape (scalars + string lists) we round-trip."""
    lines = []
    pad = "  " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).startswith("_"):
                continue
            if isinstance(v, list):
                lines.append("%s%s:" % (pad, k))
                for item in v:
                    lines.append("%s  - %s" % (pad, item))
            elif isinstance(v, dict):
                lines.append("%s%s:" % (pad, k))
                lines.extend(_emit_simple_yaml(v, indent + 1))
            elif isinstance(v, bool):
                lines.append("%s%s: %s" % (pad, k, "true" if v else "false"))
            elif v is None:
                lines.append("%s%s: null" % (pad, k))
            else:
                lines.append("%s%s: %s" % (pad, k, v))
    return lines


def cmd_graduate(args):
    """Move capability tasks whose pass rate exceeded --threshold (default
    0.9) in the most recent run into the regression suite. arm-evals bumps
    the registry version on the next re-arm; this only edits suite files."""
    evals_dir = os.path.abspath(args.evals_dir or default_evals_dir())
    runs_root = os.path.join(os.getcwd(), "runs")
    latest = None
    if os.path.isdir(runs_root):
        candidates = sorted(os.listdir(runs_root), reverse=True)
        for c in candidates:
            s = os.path.join(runs_root, c, "summary.json")
            if os.path.isfile(s):
                latest = s
                break
    if not latest:
        raise HarnessError("no runs/<ts>/summary.json found — run the "
                           "capability suite first")
    summary = read_json(latest) or {}
    if summary.get("suite") != "capability":
        print("note: latest run is suite %r, graduate reads capability runs"
              % summary.get("suite"))
    threshold = args.threshold
    saturated = []
    for tid, entry in (summary.get("tasks") or {}).items():
        rate = entry.get("pass_rate")
        if isinstance(rate, (int, float)) and rate > threshold:
            saturated.append(tid)
    if not saturated:
        print("graduate: no tasks above %.0f%% pass rate in %s — nothing to move"
              % (threshold * 100, latest))
        return 0
    cap, _v = resolve_suite(evals_dir, "capability")
    reg, _v2 = resolve_suite(evals_dir, "regression")
    moving = [t for t in saturated if t in [str(x) for x in cap["tasks"]]]
    if not moving:
        print("graduate: saturated tasks %s are not in the capability suite" % saturated)
        return 0
    print("graduate: moving %s (pass rate > %.2f in %s)" % (moving, threshold, latest))
    if args.dry_run:
        print("graduate: --dry-run, suite files unchanged")
        return 0
    cap["tasks"] = [t for t in cap["tasks"] if str(t) not in moving]
    reg["tasks"] = list(reg["tasks"]) + [t for t in moving
                                         if t not in [str(x) for x in reg["tasks"]]]
    for suite in (cap, reg):
        path = suite["_path"]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# rewritten by forge-eval graduate on %s\n" % now_iso())
            fh.write("\n".join(_emit_simple_yaml(suite)) + "\n")
        print("graduate: wrote %s" % path)
    print("graduate: re-run /plugin-forge:arm-evals to re-version and "
          "re-freeze the edited suites")
    return 0


# --------------------------------------------------------------------------
# subcommand: doctor
# --------------------------------------------------------------------------

def cmd_doctor(args):
    """Repair stuck forge state: (1) reset a stale phase=building to armed,
    (2) remove leaked forge-build-* worktrees in this repo, (3) reap fixture
    worktrees recorded in runs/*/work/.worktrees.jsonl ledgers, (4) prune."""
    fixed = []
    root = os.getcwd()
    dry = args.dry_run

    state_path = os.path.join(root, ".forge", "state.json")
    state = read_json(state_path)
    stuck = False
    if isinstance(state, dict) and state.get("phase") == "building":
        stuck = True
    elif isinstance(state, dict) and state.get("phase") == "smoke":
        # smoke is only stuck if there is NO green scoreboard backing it —
        # a healthy post-build state must not be silently voided (that would
        # force a paid rebuild). Artifact ground-truth rule from phase-gates.md.
        sb = os.path.join(root, ".forge", "last-scoreboard.txt")
        green = False
        if os.path.isfile(sb):
            with open(sb, "r", encoding="utf-8") as fh:
                lines = [l for l in fh.read().splitlines() if l.strip()]
            green = bool(lines) and "RESULT=PASS" in lines[-1]
        if green:
            print("doctor: phase=smoke with a green scoreboard — healthy, "
                  "leaving state alone (run /plugin-forge:verify next)")
        else:
            stuck = True
    if stuck:
        target_phase = "armed" if os.path.isfile(
            os.path.join(root, ".forge", "freeze.json")) else "evals"
        print("doctor: .forge/state.json is stuck at phase=%r → resetting to %r"
              % (state["phase"], target_phase))
        if not dry:
            state["phase"] = target_phase
            state["updated"] = now_iso()
            write_json(state_path, state)
        fixed.append("state-phase")
    elif isinstance(state, dict):
        print("doctor: phase=%r looks healthy" % state.get("phase"))
    else:
        print("doctor: no .forge/state.json here — nothing to clear")

    # leaked forge-build worktrees in the project repo
    proc = subprocess.run(["git", "worktree", "list", "--porcelain"],
                          capture_output=True, text=True, cwd=root)
    if proc.returncode == 0:
        for block in proc.stdout.split("\n\n"):
            m = re.search(r"^worktree (.+)$", block, re.MULTILINE)
            if not m:
                continue
            wt = m.group(1)
            if re.search(r"\.claude/worktrees/forge-build-\d{8}-\d{6}$", wt):
                print("doctor: leaked build worktree %s" % wt)
                if not dry:
                    subprocess.run(["git", "worktree", "remove", "--force", wt],
                                   capture_output=True, text=True, cwd=root)
                fixed.append(wt)
        if not dry:
            subprocess.run(["git", "worktree", "prune"], capture_output=True,
                           text=True, cwd=root)

    # fixture worktrees recorded by crashed runs
    runs_root = os.path.join(root, "runs")
    if os.path.isdir(runs_root):
        for run_id in sorted(os.listdir(runs_root)):
            ledger = os.path.join(runs_root, run_id, "work", ".worktrees.jsonl")
            if not os.path.isfile(ledger):
                continue
            live = {}
            with open(ledger, "r", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    if rec.get("action") == "add":
                        live[rec["worktree"]] = rec.get("fixture_repo")
                    elif rec.get("action") == "remove":
                        live.pop(rec.get("worktree"), None)
            for wt, repo in live.items():
                if not os.path.isdir(wt):
                    continue
                print("doctor: leaked fixture worktree %s (run %s)" % (wt, run_id))
                if not dry:
                    if repo and os.path.isdir(repo):
                        subprocess.run(["git", "-C", repo, "worktree", "remove",
                                        "--force", wt], capture_output=True, text=True)
                        subprocess.run(["git", "-C", repo, "worktree", "prune"],
                                       capture_output=True, text=True)
                    shutil.rmtree(wt, ignore_errors=True)
                fixed.append(wt)

    if dry and fixed:
        print("doctor: --dry-run — found %d issue(s), fixed nothing" % len(fixed))
    elif fixed:
        print("doctor: fixed %d issue(s)" % len(fixed))
    else:
        print("doctor: nothing to fix")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="forge-eval",
        description="plugin-forge eval harness (see module docstring). "
                    "Exit code 0 iff RESULT=PASS.")
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp, needs_suite=True):
        if needs_suite:
            sp.add_argument("--suite", required=True, help="suite name (suites/<S>.yaml)")
        sp.add_argument("--plugin-dir", default=None,
                        help="path to the plugin under test")
        sp.add_argument("--target", default=None,
                        help="target config name (targets/<T>.yaml)")
        sp.add_argument("--trials", type=int, default=None,
                        help="override per-task trials")
        sp.add_argument("--jobs", type=int, default=1,
                        help="parallel task-trials (max %d)" % MAX_JOBS)
        sp.add_argument("--task", default=None, help="run a single task id")
        sp.add_argument("--max-cost-usd", type=float, default=None,
                        help="abort when cumulative total_cost_usd crosses this")
        sp.add_argument("--dry-run", action="store_true",
                        help="first task only, 1 trial")
        sp.add_argument("--out", default=None, help="output dir (default runs/<ts>)")
        sp.add_argument("--evals-dir", default=None,
                        help="evals root (default: auto-detected)")

    common(sub.add_parser("run", help="run a suite against a target"))
    common(sub.add_parser("red", help="RED baseline: suite on the no-plugin "
                                      "target; PASS = zero tasks pass bare"))
    common(sub.add_parser("reference", help="grade reference solutions with "
                                            "each task's own graders"))

    sp = sub.add_parser("smoke", help="init-gate smoke check (delegates to "
                                      "scripts/smoke/smoke.py when present)")
    sp.add_argument("--plugin-dir", default=None)
    sp.add_argument("smoke_args", nargs="*", help="extra args passed to smoke.py")

    sp = sub.add_parser("metaeval", help="judge-vs-human-labels agreement")
    sp.add_argument("--judge", default=None, help="restrict to one judge spec")
    sp.add_argument("--evals-dir", default=None)
    sp.add_argument("--max-cost-usd", type=float, default=None)

    sp = sub.add_parser("graduate", help="move >threshold capability tasks to regression")
    sp.add_argument("--threshold", type=float, default=0.9)
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--evals-dir", default=None)

    sp = sub.add_parser("doctor", help="clear stuck .forge state; reap leaked worktrees")
    sp.add_argument("--dry-run", action="store_true")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    handlers = {"run": cmd_run, "red": cmd_run, "reference": cmd_run,
                "smoke": cmd_smoke, "metaeval": cmd_metaeval,
                "graduate": cmd_graduate, "doctor": cmd_doctor}
    try:
        return handlers[args.command](args)
    except HarnessError as exc:
        print("forge-eval: error: %s" % exc, file=sys.stderr)
        suite = getattr(args, "suite", None) or args.command
        print("FORGE_EVAL: suite=%s version=v0 passed=0/0 pass^0=0.00 "
              "cost_usd=0.00 RESULT=FAIL" % suite)
        return 1
    except KeyboardInterrupt:
        print("forge-eval: interrupted — run `forge-eval doctor` to reap any "
              "leaked worktrees", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
