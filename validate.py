#!/usr/bin/env python3
"""
Thorough validator for drugs.json.

Usage:
    python3 validate.py                 # check ./drugs.json
    python3 validate.py path/to/file    # check another file
    python3 validate.py --strict        # treat warnings as errors (exit code 1)
    python3 validate.py --info          # also print informational notes
    python3 validate.py --max 15        # show at most N lines per check (default 25)

Severity levels
    ERROR    Will break the page or violates the data format. Fix these.
    WARNING  Probably a mistake or an inconsistency. Review these.
    INFO     Useful for review (e.g. which warnings the page will show).
"""
import argparse, difflib, json, re, sys
from collections import Counter, defaultdict
from datetime import date, datetime

# ---------------------------------------------------------------- schema ---
STR_FIELDS = ["id", "name", "brand", "cls", "sub", "target", "moa", "resp", "verified"]
LIST_FIELDS = ["ind", "contra", "common", "severe", "lethal"]
SUS = ["allergy", "sex", "age", "genetic", "liver", "kidney", "pregnancy", "breastfeeding"]
PK = ["bio", "dist", "met", "t12", "exc"]
REG = ["dose", "route", "form", "freq", "timing", "stop"]
OBJ_FIELDS = {"sus": SUS, "pk": PK, "reg": REG}
ALLOWED_TOP = set(STR_FIELDS + LIST_FIELDS + ["ddi", "sus", "pk", "reg"])
RISK_VALUES = {"avoid", "caution", "ok", "note", "none"}
MAY_BE_EMPTY = {"verified"}                   # "" means "not yet verified"

# ------------------------------------------------------- style conventions ---
ROUTES = {"PO", "IV", "IM", "SC", "SL", "PR", "PV", "ID", "IT", "MDI", "DPI"}
ROUTE_WORDS = {"inhaled", "topical", "intranasal", "ophthalmic", "buccal", "local",
               "vaginal", "transdermal", "oral", "nasal", "neb", "iv", "po", "intrathecal",
               "(lar)", "(induction)", "(maintenance)", "(systemic)", "(c.", "difficile)",
               "deep", "intravitreal", "odt", "systemic", "c.", "difficile", "induction", "maintenance", "xr", "mr", "er"}
FREQ_OK = re.compile(
    r"(OD|BD|TDS|QID|PRN|nocte|mane|weekly|monthly|daily|single|once|continuous|bolus|infusion|"
    r"q\d+(–\d+)?\s?(h|wk|mo|d)|wk|mo|\bd\b|dose|split|then|or|and|\(|\)|;|,|/|\d|[A-Za-z]+)",
    re.I)
US_SPELLINGS = {
    "hemorrhage": "haemorrhage", "anemia": "anaemia", "edema": "oedema",
    "esophag": "oesophag", "diarrhea": "diarrhoea", "leukopenia": "leucopenia",
    "hypoglycemia": "hypoglycaemia", "hyperglycemia": "hyperglycaemia",
    "hyperkalemia": "hyperkalaemia", "hypokalemia": "hypokalaemia",
    "hyponatremia": "hyponatraemia", "hypernatremia": "hypernatraemia",
    "hypocalcemia": "hypocalcaemia", "hypercalcemia": "hypercalcaemia",
    "pediatric": "paediatric", "estrogen": "oestrogen", "anesthe": "anaesthe",
    "ischemi": "ischaemi", "hematolog": "haematolog",
}
WORD_ARROWS = [(r"\b(increases?|increased|elevated|raises?)\b", "↑"),
               (r"\b(decreases?|decreased|reduces?|reduced|lowers?|lowered)\b", "↓")]
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# page keyword rules (mirror app.js so we can report what the page will show)
def risk(sus, key):
    ov = (sus.get("risk") or {}).get(key)
    if ov:
        return ov
    v = sus.get(key, "—")
    if v == "—":
        return "none"
    if key == "allergy" or re.match(r"^avoid|contraindicated", v, re.I) or re.search(r"contraindicated", v, re.I):
        return "avoid"
    if re.search(r"caution|↓ dose|↑|monitor|essential|limited", v, re.I):
        return "caution"
    return "ok" if key in ("liver", "kidney", "pregnancy", "breastfeeding") else "note"


class Report:
    def __init__(self, cap):
        self.items = defaultdict(list)   # (level, check) -> [messages]
        self.cap = cap

    def add(self, level, check, msg):
        self.items[(level, check)].append(msg)

    def count(self, level):
        return sum(len(v) for (lv, _), v in self.items.items() if lv == level)

    def show(self, show_info):
        order = {"ERROR": 0, "WARNING": 1, "INFO": 2}
        for (lv, check), msgs in sorted(self.items.items(), key=lambda x: (order[x[0][0]], x[0][1])):
            if lv == "INFO" and not show_info:
                continue
            print(f"\n[{lv}] {check}  ({len(msgs)})")
            for m in msgs[: self.cap]:
                print("   -", m)
            if len(msgs) > self.cap:
                print(f"   ... and {len(msgs) - self.cap} more (use --max to show more)")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def check_text(rep, who, label, text):
    """Generic hygiene checks for any string."""
    if text != text.strip():
        rep.add("WARNING", "Leading/trailing whitespace", f"{who}: {label}")
    if "  " in text:
        rep.add("WARNING", "Double spaces", f"{who}: {label}")
    if re.search(r"\s[,;.]", text):
        rep.add("WARNING", "Space before punctuation", f"{who}: {label}: {text[:60]!r}")
    if text.endswith(".") and not text.endswith(("...", "etc.", "spp.", "d.", "c.")):
        rep.add("INFO", "Trailing full stop", f"{who}: {label}")
    if re.search(r"\d\s*-\s*\d", text) and not re.search(r"\d+-(HT|OH|ASA|[A-Za-z])", text):
        rep.add("WARNING", "Hyphen used for a numeric range (use en dash –)", f"{who}: {label}: {text[:60]!r}")
    for pat, arrow in WORD_ARROWS:
        m = re.search(pat, text, re.I)
        if m:
            rep.add("INFO", "Word that could be an arrow", f"{who}: {label}: '{m.group(0)}' -> {arrow}")
    low = text.lower()
    for us, uk in US_SPELLINGS.items():
        if re.search(r"\b" + re.escape(us), low):
            rep.add("WARNING", "US spelling (project uses British / Australian)", f"{who}: {label}: '{us}' -> '{uk}'")
    if re.search(r"[“”‘’]", text):
        rep.add("INFO", "Typographic quotes in data", f"{who}: {label}")


def validate(path, cap, today):
    rep = Report(cap)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {path}"); sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}"); sys.exit(2)

    if not isinstance(data, list):
        print("ERROR: top level must be a list of drug objects"); sys.exit(2)

    ids, names = Counter(), Counter()
    by_sub = defaultdict(list)

    for i, d in enumerate(data):
        if not isinstance(d, dict):
            rep.add("ERROR", "Entry is not an object", f"index {i}"); continue
        who = d.get("id") or f"<index {i}>"

        # ---- structure ------------------------------------------------
        for k in STR_FIELDS + LIST_FIELDS + ["ddi", "sus", "pk", "reg"]:
            if k not in d:
                rep.add("ERROR", "Missing key", f"{who}: '{k}'")
        for k in d:
            if k not in ALLOWED_TOP:
                rep.add("WARNING", "Unknown top-level key (typo?)", f"{who}: '{k}'")

        # ---- strings --------------------------------------------------
        for k in STR_FIELDS:
            v = d.get(k)
            if v is None:
                continue
            if not isinstance(v, str):
                rep.add("ERROR", "Wrong type (expected string)", f"{who}: '{k}'"); continue
            if not v.strip() and k not in MAY_BE_EMPTY:
                rep.add("ERROR", "Empty string", f"{who}: '{k}'")
            if v and k != "verified":
                check_text(rep, who, k, v)
        if d.get("moa") and len(d["moa"]) > 420:
            rep.add("WARNING", "Very long mechanism of action (>420 chars)", f"{who}: {len(d['moa'])} chars")
        if d.get("moa") and not d["moa"][0].isupper():
            rep.add("WARNING", "Does not start with a capital", f"{who}: moa")

        # ---- id / name ------------------------------------------------
        if isinstance(d.get("id"), str):
            ids[d["id"]] += 1
            if not ID_RE.match(d["id"]):
                rep.add("ERROR", "Bad id (lowercase letters, digits and single hyphens only)", f"{who}")
            elif d.get("name") and slug(d["name"]) != d["id"]:
                rep.add("INFO", "id differs from slug of name", f"{who} vs '{d['name']}'")
        if isinstance(d.get("name"), str):
            names[d["name"].lower()] += 1

        # ---- lists ----------------------------------------------------
        for k in LIST_FIELDS:
            v = d.get(k)
            if v is None:
                continue
            if not isinstance(v, list):
                rep.add("ERROR", "Wrong type (expected list)", f"{who}: '{k}'"); continue
            if not v:
                rep.add("WARNING", "Empty list", f"{who}: '{k}'")
            seen = set()
            for item in v:
                if not isinstance(item, str) or not item.strip():
                    rep.add("ERROR", "List item is not a non-empty string", f"{who}: '{k}'"); continue
                if item.lower() in seen:
                    rep.add("WARNING", "Duplicate within list", f"{who}: '{k}': {item!r}")
                seen.add(item.lower())
                if len(item) > 130:
                    rep.add("WARNING", "Very long list item (>130 chars)", f"{who}: '{k}': {item[:50]!r}...")
                if not item[0].isupper() and not item[0].isdigit() and not item[0] in "↑↓":
                    rep.add("WARNING", "List item does not start with a capital", f"{who}: '{k}': {item[:40]!r}")
                check_text(rep, who, k, item)
        # the same effect should not appear in two tiers
        tiers = {t: {x.lower() for x in d.get(t, []) if isinstance(x, str)} for t in ("common", "severe", "lethal")}
        for a, b in (("common", "severe"), ("severe", "lethal"), ("common", "lethal")):
            for x in tiers[a] & tiers[b]:
                rep.add("WARNING", "Same adverse effect in two tiers", f"{who}: {x!r} in {a} and {b}")

        # ---- interactions ---------------------------------------------
        ddi = d.get("ddi")
        if ddi is not None:
            if not isinstance(ddi, list) or not ddi:
                rep.add("ERROR", "ddi must be a non-empty list", who)
            else:
                seen = set()
                for r in ddi:
                    if not (isinstance(r, dict) and set(r) == {"drug", "mech"}):
                        rep.add("ERROR", "ddi row must be {'drug','mech'}", f"{who}: {r}"); continue
                    if not r["drug"].strip() or not r["mech"].strip():
                        rep.add("ERROR", "ddi row has empty drug / mech", who)
                    if r["drug"].lower() in seen:
                        rep.add("WARNING", "Duplicate interacting drug", f"{who}: {r['drug']!r}")
                    seen.add(r["drug"].lower())
                    if r["mech"] == "—" and "none" not in r["drug"].lower():
                        rep.add("WARNING", "Interaction mechanism is '—'", f"{who}: {r['drug']!r}")
                    if r["mech"].lower().startswith(("mechanism unclear", "unknown")):
                        rep.add("INFO", "Interaction mechanism vague (fill in if you can)", f"{who}: {r['drug']!r}")
                    check_text(rep, who, "ddi.mech", r["mech"])

        # ---- sus / pk / reg -------------------------------------------
        for obj, keys in OBJ_FIELDS.items():
            o = d.get(obj)
            if o is None:
                continue
            if not isinstance(o, dict):
                rep.add("ERROR", "Wrong type (expected object)", f"{who}: '{obj}'"); continue
            for k in keys:
                if k not in o:
                    rep.add("ERROR", "Missing key", f"{who}: {obj}.{k}")
                elif not isinstance(o[k], str) or not o[k].strip():
                    rep.add("ERROR", "Empty / non-string value (use '—' if none)", f"{who}: {obj}.{k}")
                else:
                    check_text(rep, who, f"{obj}.{k}", o[k])
            for k in o:
                if k not in keys and not (obj == "sus" and k == "risk"):
                    rep.add("WARNING", "Unknown key (typo?)", f"{who}: {obj}.{k}")
        sus = d.get("sus") if isinstance(d.get("sus"), dict) else {}
        for k, v in (sus.get("risk") or {}).items():
            if k not in SUS or v not in RISK_VALUES:
                rep.add("ERROR", "Bad sus.risk override", f"{who}: {k}={v!r}")

        # ---- regimen conventions --------------------------------------
        reg = d.get("reg") if isinstance(d.get("reg"), dict) else {}
        route = reg.get("route", "")
        for tok in re.split(r"[ /;,()]+", route):
            if tok and tok.upper() not in ROUTES and tok.lower() not in ROUTE_WORDS and not tok.isdigit():
                rep.add("INFO", "Unusual route token", f"{who}: reg.route has {tok!r}")
        freq = reg.get("freq", "")
        if re.search(r"\b(daily|twice|three times|four times|once)\b", freq, re.I) and not re.search(r"\b(OD|BD|TDS|QID)\b", freq):
            rep.add("WARNING", "Use abbreviations in reg.freq (OD / BD / TDS / QID)", f"{who}: {freq!r}")

        # ---- cross-checks: contra vs susceptibilities -------------------
        contra_txt = " ".join(x for x in d.get("contra", []) if isinstance(x, str)).lower()
        for key, word in (("pregnancy", "pregnan"), ("breastfeeding", "breastfeed")):
            if word in contra_txt and sus.get(key):
                r = risk(sus, key)
                if r in ("ok", "caution"):
                    rep.add("WARNING", "Contraindication mentions it but sus shows OK / caution",
                            f"{who}: {key} -> {r} ({sus[key]!r})")
        for key in ("liver", "kidney"):
            if sus.get(key) and risk(sus, key) == "ok" and re.search(rf"\bsevere {key}|{key} (failure|impairment)|hepatic impairment|renal impairment", contra_txt):
                if (key == "liver" and "hepatic" in contra_txt) or (key == "kidney" and "renal" in contra_txt):
                    rep.add("INFO", "Contraindication mentions organ impairment but sus shows OK", f"{who}: {key}")

        # ---- page warning-level preview ---------------------------------
        for key in ("liver", "kidney", "pregnancy", "breastfeeding"):
            v = sus.get(key, "")
            if v and v.lower().startswith("acceptable") and risk(sus, key) == "caution":
                rep.add("INFO", "Starts 'Acceptable' but the page will show CAUTION (keyword)", f"{who}: {key}: {v!r}")

        # ---- verified ---------------------------------------------------
        v = d.get("verified", "")
        if isinstance(v, str) and v:
            if not DATE_RE.match(v):
                rep.add("ERROR", "verified must be '' or YYYY-MM-DD", f"{who}: {v!r}")
            else:
                try:
                    dt = datetime.strptime(v, "%Y-%m-%d").date()
                    if dt > today:
                        rep.add("ERROR", "verified date is in the future", f"{who}: {v}")
                    elif (today - dt).days > 365:
                        rep.add("WARNING", "Verified more than a year ago", f"{who}: {v}")
                except ValueError:
                    rep.add("ERROR", "verified is not a real date", f"{who}: {v!r}")

        if isinstance(d.get("sub"), str) and isinstance(d.get("cls"), str):
            by_sub[(d["cls"], d["sub"])].append(d)

    # ---- global checks ---------------------------------------------------
    for k, n in ids.items():
        if n > 1:
            rep.add("ERROR", "Duplicate id", f"{k!r} appears {n} times")
    for k, n in names.items():
        if n > 1:
            rep.add("WARNING", "Duplicate drug name", f"{k!r} appears {n} times")

    # near-identical class / subclass names
    classes = sorted({c for c, _ in by_sub})
    subs = sorted({s for _, s in by_sub})
    for pool, label in ((classes, "class"), (subs, "subclass")):
        for a in pool:
            for b in pool:
                norm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower()).rstrip("s")
                if a < b and (norm(a) == norm(b) or difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.97):
                    rep.add("WARNING", f"Near-identical {label} names (typo?)", f"{a!r} vs {b!r}")
    sub_to_cls = defaultdict(set)
    for c, s in by_sub:
        sub_to_cls[s].add(c)
    for s, cs in sub_to_cls.items():
        if len(cs) > 1:
            rep.add("WARNING", "Same subclass name under different classes", f"{s!r}: {sorted(cs)}")
    for (c, s), ds in by_sub.items():
        if len(ds) == 1:
            rep.add("INFO", "Subclass contains a single drug", f"{c} > {s}: {ds[0]['id']}")

    # wording consistency inside a subclass (nearly-identical but not identical)
    for (c, s), ds in by_sub.items():
        for field in ("target", "moa", "resp"):
            for a_i in range(len(ds)):
                for b_i in range(a_i + 1, len(ds)):
                    a, b = ds[a_i].get(field), ds[b_i].get(field)
                    if isinstance(a, str) and isinstance(b, str) and a != b and len(a) > 25:
                        r = difflib.SequenceMatcher(None, a, b).ratio()
                        if r >= 0.88:
                            rep.add("WARNING", "Near-identical wording in the same subclass (make identical or genuinely different)",
                                    f"{c} > {s}: {ds[a_i]['id']} vs {ds[b_i]['id']} [{field}] similarity {r:.2f}")

    # ---- summary ---------------------------------------------------------
    total = len(data)
    vcount = sum(1 for d in data if isinstance(d, dict) and d.get("verified"))
    rl = Counter()
    for d in data:
        if isinstance(d, dict) and isinstance(d.get("sus"), dict):
            for k in ("liver", "kidney", "pregnancy", "breastfeeding"):
                rl[risk(d["sus"], k)] += 1
    rep.add("INFO", "Summary", f"{total} drugs, {len(classes)} classes, {len(subs)} subclasses, {vcount} verified")
    rep.add("INFO", "Page warning levels (liver / kidney / pregnancy / breastfeeding)",
            ", ".join(f"{k}: {v}" for k, v in sorted(rl.items())))
    return rep


def main():
    ap = argparse.ArgumentParser(description="Validate drugs.json")
    ap.add_argument("path", nargs="?", default="drugs.json")
    ap.add_argument("--strict", action="store_true", help="warnings count as failures")
    ap.add_argument("--info", action="store_true", help="show informational notes")
    ap.add_argument("--max", type=int, default=25, help="max lines to show per check")
    a = ap.parse_args()
    rep = validate(a.path, a.max, date.today())
    rep.show(a.info)
    e, w = rep.count("ERROR"), rep.count("WARNING")
    print(f"\n{e} error(s), {w} warning(s)")
    if not a.info:
        print("(run with --info for review notes and a summary)")
    sys.exit(1 if e or (a.strict and w) else 0)


if __name__ == "__main__":
    main()
