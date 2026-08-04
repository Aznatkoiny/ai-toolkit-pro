import os, re
bad = []
for d, _, fs in os.walk("../knowledge"):
    for f in fs:
        if not f.endswith(".md") or f in ("index.md", "log.md"):
            continue
        p = os.path.join(d, f)
        m = re.match(r"\A---\n(.*?)\n---\n", open(p).read(), re.S)
        if not m or not re.search(r"^type: \S", m.group(1), re.M):
            bad.append(p)
print("OK" if not bad else bad)
