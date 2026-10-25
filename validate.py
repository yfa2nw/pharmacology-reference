import json, sys

REQUIRED = "id name brand cls sub ind target moa resp contra common severe lethal ddi sus pk reg verified".split()
SUS = "allergy sex age genetic liver kidney pregnancy breastfeeding".split()
PK = "bio dist met t12 exc".split()
REG = "dose route form freq timing stop".split()

data = json.load(open("drugs.json", encoding="utf-8"))
ids, problems = set(), []

for d in data:
    name = d.get("id", "<no id>")
    for k in REQUIRED:
        if k not in d: problems.append(f"{name}: missing '{k}'")
    if name in ids: problems.append(f"{name}: duplicate id")
    ids.add(name)
    for k in SUS:
        if k not in d.get("sus", {}): problems.append(f"{name}: sus.{k} missing")
    for k in PK:
        if k not in d.get("pk", {}): problems.append(f"{name}: pk.{k} missing")
    for k in REG:
        if k not in d.get("reg", {}): problems.append(f"{name}: reg.{k} missing")
    for k in ("ind", "contra", "common", "severe", "lethal"):
        if not d.get(k): problems.append(f"{name}: '{k}' is empty")
    if " " in name or name != name.lower(): problems.append(f"{name}: id should be lowercase-hyphenated")

print(f"{len(data)} drugs checked")
print("\n".join(problems) if problems else "No problems found")
sys.exit(1 if problems else 0)