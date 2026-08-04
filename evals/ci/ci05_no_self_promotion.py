import json, subprocess
verdicts = []
for tid in ("T25", "T26", "T27"):
    c = open("../evals/tasks/%s/reference/MODEL_PLAN.md" % tid).read()
    e = json.dumps({"tool_name": "Write", "cwd": "..",
                    "tool_input": {"file_path": "MODEL_PLAN.md", "content": c}})
    p = subprocess.run(["python3", "skills/advise/scripts/lint_outputs.py"],
                       input=e, capture_output=True, text=True)
    verdicts.append("PASS" if "VERDICT=PASS" in p.stdout else "FAIL:" + tid)
print("OK" if all(v == "PASS" for v in verdicts) else verdicts)
