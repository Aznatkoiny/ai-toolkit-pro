import glob, json, re
cat = {}
for p in sorted(glob.glob("../knowledge/foundations/*.md")):
    t = open(p).read()
    m = re.match(r"\A---\n(.*?)\n---\n", t, re.S)
    if not m or "type: Task Pairing" not in m.group(1):
        continue
    fm = m.group(1)
    tt = re.search(r'^task_type: "(.+)"', fm, re.M).group(1)
    act = re.search(r'^activation: "(.+)"', fm, re.M).group(1)
    loss = json.loads(re.search(r"^loss: (\[.*\])", fm, re.M).group(1).replace("'", '"'))
    cat[tt] = {"activation": act, "loss": loss}
art = json.load(open("skills/advise/data/pairings.json"))
sem = {k: {"activation": v["activation"], "loss": v["loss"]} for k, v in art.items()}
print("MATCH" if cat == sem else "DRIFT")
