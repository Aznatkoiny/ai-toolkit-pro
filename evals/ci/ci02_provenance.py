import os
bad = []
for d, _, fs in os.walk("../knowledge"):
    for f in fs:
        if not f.endswith(".md") or f in ("index.md", "log.md"):
            continue
        t = open(os.path.join(d, f)).read()
        if "status: stable" in t and "resource:" not in t:
            bad.append(f)
print("OK" if not bad else bad)
