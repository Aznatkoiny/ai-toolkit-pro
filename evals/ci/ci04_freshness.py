import datetime, os, re
today = datetime.date.today()
bad = []
for d, _, fs in os.walk("../knowledge"):
    for f in fs:
        if not f.endswith(".md") or f in ("index.md", "log.md"):
            continue
        t = open(os.path.join(d, f)).read()
        if "status: stable" not in t:
            continue
        m = re.search(r"^stale_after:\s*(\d{4}-\d{2}-\d{2})", t, re.M)
        if m and today >= datetime.date.fromisoformat(m.group(1)):
            bad.append(f)
print("OK" if not bad else bad)
