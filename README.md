# Drug Reference

A small, fast, **data-driven pharmacology reference** for revision. All medication content lives in one JSON file; the web page reads that file and renders it, so **you only ever edit `drugs.json`**.

The page is designed to be read quickly: colour-blind-friendly colours, shape and border cues instead of colour alone, a mechanism flow diagram, tiered adverse effects, at-a-glance warnings for liver / kidney / pregnancy / breastfeeding, and an optional study mode that hides answers until you click.

> **Important:** this is a study aid, not a clinical tool. Much of the content was drafted with AI assistance and must be checked against an authoritative source (for example the Australian Medicines Handbook) before you rely on it. See [Disclaimer](#disclaimer) and [The `verified` field](#the-verified-field).

---

## Contents

- [Features](#features)
- [Quick start](#quick-start)
- [Project structure](#project-structure)
- [How it works](#how-it-works)
- [Data format](#data-format)
- [Writing conventions](#writing-conventions)
- [Tutorial: add your first drug](#tutorial-add-your-first-drug)
- [Tutorial: add a new class](#tutorial-add-a-new-class)
- [Tutorial: add a new field](#tutorial-add-a-new-field)
- [Tutorial: change the look](#tutorial-change-the-look)
- [The `verified` field](#the-verified-field)
- [Warning levels (OK / caution / avoid)](#warning-levels-ok--caution--avoid)
- [Validating your data](#validating-your-data)
- [Hosting](#hosting)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## Features

- **One source only:** the webpage is directly linked to the drugs.json file - the html, css, and js codes will parse the json file automatically.
- **Sidebar navigation:** drugs grouped as class → subclass → name (alphabetical), with counts, search, and collapse / expand all.
- **Search:** matches drug name, brand name, class, subclass and indications.
- **Mechanism flow:** Target → Mechanism → Response shown as three connected boxes.
- **Adverse effects in three tiers:** common (plain), severe (dashed orange), lethal (filled dark). Shape and fill carry the meaning, not just colour.
- **Susceptibility grid:** allergy, sex, age, genetic, liver, kidney, pregnancy and breastfeeding, each marked ✓ OK, ⚠ CAUTION, ⛔ AVOID or ℹ NOTE. The four high-stakes categories also appear as chips under the drug name.
- **Arrow badges:** every ↑ and ↓ in the data is automatically turned into a visible badge.
- **Study mode:** blurs indications, mechanism, adverse effects, interactions, kinetics and regimen values until you click them. "Reveal all" is available.
- **Verified tracking:** each drug can carry a "last verified" date, shown on the page and in the sidebar.
- **Light and dark mode** follow the system setting.
- **Accessible by design:** colours from the Okabe-Ito colour-blind-safe palette (because I'm red-green colour blind); warning states differ by label, icon, border style and fill.

---

## Quick start

1. Keep these four files **in the same folder**:

   ```bash
   index.html
   style.css
   app.js
   drugs.json
   ```

2. Serve the folder (browsers block a page from reading local files when you double-click it):

   ```bash
   cd path/to/this/folder
   python3 -m http.server 8000
   ```

   Then open <http://localhost:8000>.

   Other options: **VS Code "Live Server" (I personally use this option)**, `npx serve`, or any static host (see [Hosting](#hosting)).

3. **No server?** Double-click `index.html`. The page will show a **Choose drugs.json** button. Pick your file and it loads. The page remembers the last file you chose (in the browser's local storage), so you only need to do this again when the file changes.

---

## Project structure

| File | Purpose |
| --- | --- |
| `index.html` | Page skeleton: sidebar container and main content area. |
| `style.css` | All styling, driven by CSS variables (colours, light / dark mode). |
| `app.js` | Loads the JSON, builds the sidebar, renders each drug, handles search, collapse, study mode. |
| `drugs.json` | **The database.** An array of drug objects. |
| `README.md` | This file. |

---

## How it works

1. `app.js` fetches `drugs.json` (`cache: "no-store"` so edits show immediately).
2. If the fetch fails (for example when opened from `file://`), it falls back to the last copy saved in local storage, and otherwise shows the file picker.
3. Drugs are sorted by `cls` (class), then `sub` (subclass), then `name` (non-commercial drug name), and grouped into the sidebar.
4. Selecting a drug sets the URL hash (`#drug-id`) and renders the page for that drug. Because the hash is the drug's `id` (ID), you can bookmark or share a link to a single drug.
5. All text goes through an escaping function before it is inserted into the page. Only `↑` (blue) and `↓` (orange) are converted to badges.

Everything is plain HTML, CSS and JavaScript. Any modern browser should work (the CSS uses `color-mix()`, so use a reasonably recent version).

---

## Data format

`drugs.json` is an array. Each element is one drug. The template for an element is as follows:

```json
{
  "id": "example-drug",
  "name": "Example drug",
  "brand": "Brandname; Othername",
  "cls": "Example class (e.g., Cardiovascular)",
  "sub": "Example subclass (e.g., Class Ia antiarrhythmics)",
  "ind": ["Indication one", "Indication two", etc.],
  "target": "Receptor or process the drug acts on",
  "moa": "Mechanism of action, written as one sentence",
  "resp": "Physiological response / net effect",
  "contra": ["Contraindication one", etc.],
  "common": ["Common adverse effect", etc.],
  "severe": ["Severe adverse effect", etc.],
  "lethal": ["Potentially fatal adverse effect", etc.],
  "ddi": [
    { "drug": "Interacting drug(s)", "mech": "Mechanism, e.g. CYP3A4 inhibition ↑ levels" },
    etc.
  ],
  "sus": {
    "allergy": "—",
    "sex": "—",
    "age": "—",
    "genetic": "—",
    "liver": "—",
    "kidney": "—",
    "pregnancy": "—",
    "breastfeeding": "—"
  },
  "pk": {
    "bio": "Bioavailability",
    "dist": "Distribution",
    "met": "Metabolism (where)",
    "t12": "Half-life",
    "exc": "Excretion (where)"
  },
  "reg": {
    "dose": "Dose",
    "route": "PO / IV",
    "form": "Formulation",
    "freq": "OD",
    "timing": "Timing relative to food / other drugs",
    "stop": "Stopping rules, duration, monitoring"
  },
  "verified": ""
}
```

### Field reference

| Field | Type | Shown as |
| --- | --- | --- |
| `id` | string | URL hash and internal key. **Must be unique**, lowercase, hyphenated, no spaces. |
| `name` | string | Page title. |
| `brand` | string | Subtitle. Separate brands with `;`. |
| `cls` | string | Top-level group in the sidebar. |
| `sub` | string | Second-level group in the sidebar. |
| `ind` | string[] | Indication chips. |
| `target`, `moa`, `resp` | string | The three-box mechanism flow. |
| `contra` | string[] | Contraindications box. |
| `common`, `severe`, `lethal` | string[] | The three adverse-effect tiers. |
| `ddi` | `{drug, mech}[]` | Interaction table. Use one row saying "None clinically significant" if there are none. |
| `sus` | object | Susceptibility grid. Use `"—"` when nothing notable applies. |
| `pk` | object | Pharmacokinetics table. |
| `reg` | object | Regimen table. |
| `verified` | string | `""` (not verified) or a date `"YYYY-MM-DD"`. |

Optional: `sus.risk` can override the automatic warning level for a susceptibility (see [Warning levels](#warning-levels-ok--caution--avoid)).

---

## Writing conventions

Consistent wording is what makes revision fast, because identical text signals "same mechanism". Please follow these when adding or editing entries:

1. **Reuse exact wording within a subclass.** If two drugs share a mechanism, copy the mechanism sentence verbatim. Do the same for `target`, `resp`, `contra` and adverse-effect lists wherever they truly match. Only change the part that differs (for example, "prodrug converted to..." for one drug).
2. **Use the arrows** `↑` (increase) and `↓` (decrease) instead of words like "increases" or "reduces". They become badges on the page.
3. **Regimen abbreviations:** `PO`, `IV`, `IM`, `SC`, `SL`, `PR`, `OD`, `BD`, `TDS`, `QID`, `q4h` / `q6h` / `q8h` / `q12h`, `PRN`, `nocte`, `mane`, `d` (days), `wk`, `mo`, `y`.
4. **Keep list items short** (a phrase, not a sentence). Put detail after a semicolon or in brackets.
5. **Susceptibility text:** start with `Avoid` or `Contraindicated` for true prohibitions, `Caution` for caveats, `Acceptable` for safe-to-use. The page reads these words to pick the warning level.
6. **Use `"—"`** for an empty susceptibility, never an empty string.
7. **Spelling:** the existing entries use British / Australian spelling (for example "haemorrhage", "paracetamol"). Please match it.
8. **One idea per bullet.** Do not merge two adverse effects into one string unless they are genuinely one entity.

---

## Tutorial: add your first drug

**Goal:** add a drug called "Examplestatin" to the existing Statins subclass.

1. Open `drugs.json`.
2. Find a drug in the same subclass (for example `atorvastatin`) and copy its whole object.
3. Paste it at the end of the array (before the final `]`), and add a comma after the previous object.
4. Change the drug-specific fields:
   - `id` → `"examplestatin"` (unique)
   - `name`, `brand`
   - `ind`, `ddi`, `sus`, `pk`, `reg`
5. **Leave `cls`, `sub`, `target`, `moa`, `resp`, `contra`, `common`, `severe` and `lethal` untouched** if they are the same for this drug. Reusing identical text is the point.
6. Set `"verified": ""` until you have checked it against a source.
7. Save and reload the page. The drug appears in the sidebar under its class and subclass, in alphabetical order.

**If nothing appears:** the JSON is probably invalid. Paste the file into a JSON validator or run `python3 -m json.tool drugs.json` and fix the line it reports (usually a missing comma or a trailing comma).

### Bulk-adding with Python (optional)

If you are adding many related drugs, a script keeps shared text in one place. Sketch:

```python
import json

D = json.load(open("drugs.json"))

SHARED = dict(
    cls="Cardiovascular",
    sub="Statins (HMG-CoA reductase inhibitors)",
    target="HMG-CoA reductase (hepatic)",
    moa="Competitively inhibits HMG-CoA reductase, ↓ hepatic cholesterol synthesis and ↑ LDL receptor expression, ↑ LDL clearance from plasma",
    resp="↓ LDL-C (and triglycerides); ↓ CV events",
    contra=["Active liver disease / unexplained persistent ↑ ALT", "Pregnancy"],
    common=["Myalgia", "Headache"],
    severe=["Myopathy / myositis", "Rhabdomyolysis"],
    lethal=["Rhabdomyolysis with AKI"],
    verified="",
)

D.append(dict(
    id="examplestatin", name="Examplestatin", brand="Examplor",
    **SHARED,
    ind=["Primary / secondary CV prevention"],
    ddi=[{"drug": "Ciclosporin", "mech": "OATP inhibition ↑ statin levels"}],
    sus={"allergy": "—", "sex": "—", "age": "—", "genetic": "—",
         "liver": "Contraindicated in active liver disease", "kidney": "—",
         "pregnancy": "Avoid", "breastfeeding": "Avoid"},
    pk=dict(bio="~20%", dist="Hepatoselective", met="Liver (CYP3A4)", t12="~14 h", exc="Faeces"),
    reg=dict(dose="10 mg", route="PO", form="Tablet", freq="OD", timing="Any time",
             stop="Long term; lipids at 6–8 wk"),
))

json.dump(D, open("drugs.json", "w"), ensure_ascii=False, indent=1)
```

Note: do not pass the same key twice (once inside `**SHARED` and once explicitly) or Python raises "multiple values for keyword argument", and always back up `drugs.json` first.

---

## Tutorial: add a new class

Classes are not defined anywhere. They appear automatically from the `cls` and `sub` values.

1. Choose a name for the class and subclass, for example `"cls": "Endocrine"`, `"sub": "Biguanides"`.
2. Add a drug that uses those values.
3. Reload. A new group appears in the sidebar, sorted alphabetically.

Keep spellings identical across drugs. "Antibacterial" and "Antibacterials" would create two separate groups.

- The naming convention for classes is usually singular (e.g., Antibacterial).
- The naming convention for subclasses is usually plural (e.g., Antimycobacterial agents).

---

## Tutorial: add a new field

Suppose you want a **"Pregnancy category"** value shown in the regimen table.

1. **Add it to the data** (inside `reg`, for example):

   ```json
   "reg": { "dose": "10 mg", "...": "...", "pcat": "Category D" }
   ```

2. **Add it to the table.** In `app.js`, find the regimen table call inside `show(d)`:

   ```js
   ${rows(d.reg,[["dose","Dose"],["route","Route"],["form","Formulation"],["freq","Frequency"],["timing","Timing"],["stop","Stopping rules"]])}
   ```

   and add a pair to the list:

   ```js
   ["pcat","Pregnancy category"]
   ```

   The `rows()` helper shows `—` automatically when a drug has no value for the field, so you do not need to update every drug at once.

3. **For a brand-new section** (for example "Patient counselling"), add a new `<h2>` block in the template inside `show(d)` and render your field with the existing helpers:
   - `ul(array)` for a bulleted list
   - `rows(object, [[key, label], ...])` for a two-column table
   - `E(text)` to escape any text you insert yourself

4. **To make the new field searchable,** add it to the array in `list()` where the search text is built (`JSON.stringify([d.name,d.brand,d.cls,d.sub,d.ind])`).

---

## Tutorial: change the look

All colours are CSS variables at the top of `style.css`:

| Variable | Meaning |
| --- | --- |
| `--b` | Main accent (blue) used for headings, active drug and "OK" |
| `--o` | Caution colour (orange) |
| `--k` | Lethal / dark fill |
| `--bg`, `--pn`, `--tx`, `--mu`, `--ln` | Background, panel, text, muted text, lines |

Dark-mode values are in the `@media (prefers-color-scheme: dark)` block.

Guidelines if you change colours:

- Keep **meaning carried by more than colour**: labels, icons, border style and fill already do this for warnings and adverse-effect tiers.
- Stay with a colour-blind-safe palette (such as Okabe-Ito) and avoid pairing red with green.
- Check both light and dark mode.

---

## The `verified` field

Every drug has a `verified` field.

- `""` means **not yet checked**. The page shows a dashed "Not yet verified" badge and a ○ in the sidebar.
- `"2026-10-25"` (a `YYYY-MM-DD` date) means you checked the entry against a source on that date. The page shows a solid "Verified" badge and a ✓.

Suggested workflow:

1. Open the drug in your primary source (for example the Australian Medicines Handbook).
2. Compare each section and correct `drugs.json` as needed.
3. Set `verified` to today's date.
4. If you later edit the clinical content, clear or update the date so the badge stays honest.

---

## Warning levels (OK / caution / avoid)

Each susceptibility cell gets a level, worked out from its text:

| Level | Shown as | Triggered when |
| --- | --- | --- |
| Avoid | ⛔ AVOID | Text starts with "Avoid", contains "contraindicated", or the field is `allergy` with any text |
| Caution | ⚠ CAUTION | Text contains "caution", "↓ dose", "↑", "monitor", "essential" or "limited" |
| OK | ✓ OK | Anything else in liver, kidney, pregnancy or breastfeeding |
| Note | ℹ NOTE | Anything else in allergy / sex / age / genetic (not warnings) |
| None | (dimmed) | The value is `"—"` |

Because this is keyword-based, always sanity-check the result. If it is wrong, override it for that drug:

```json
"sus": {
  "pregnancy": "Acceptable if indicated",
  "risk": { "pregnancy": "caution" }
}
```

Valid override values: `avoid`, `caution`, `ok`, `note`, `none`.

---

## Validating your data

A quick check that catches the common mistakes (missing keys, duplicate ids, empty lists). Save as `validate.py` next to `drugs.json`:

```python
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
```

Run it with `python3 validate.py` before you commit or share changes.

---

## Hosting

The site is static, so anything that serves files works:

- **GitHub Pages:** push the four files to a repository, then Settings → Pages → deploy from the main branch.
- **Netlify / Vercel / Cloudflare Pages:** drag and drop the folder, or connect the repository. No build command is needed.
- **Local network:** `python3 -m http.server` from the folder.

When you publish, remember the [disclaimer](#disclaimer). Consider only making the site public once the entries you rely on are marked as verified.

---

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| Page shows "Load your database" | The page cannot fetch `drugs.json`. Serve the folder over HTTP, or use the file picker. |
| Page loads but shows old data | Your browser may be using the saved copy. Serve over HTTP so it fetches fresh data, or re-pick the file. |
| A new drug does not appear | `drugs.json` is invalid. Run `python3 -m json.tool drugs.json`. Check commas and quotes. |
| Two groups with almost the same name | Inconsistent spelling in `cls` or `sub`. Make them identical. |
| Link to a drug opens the first drug | `id` in the URL does not match any drug. Check spelling and hyphens. |
| Layout looks unstyled | `style.css` is not in the same folder as `index.html`. |
| Arrows look misaligned in a new section | The new section's CSS is restyling `<b>` tags. Add a rule such as `.mybox b.ar{display:inline-grid;font-size:inherit}`. |
| A class name clash (odd styling) | Two components share a CSS class name. Rename one of them. |

---

## Contributing

Contributions that improve accuracy and consistency are especially welcome.

1. **One topic per change:** a single drug, a single subclass, or a single bug fix.
2. **Cite your source** in the pull request (guideline, handbook edition, or label), and note the date you checked it.
3. Follow the [writing conventions](#writing-conventions). Reuse existing wording where mechanisms match.
4. Run `validate.py` and make sure `drugs.json` is valid JSON.
5. Only set `verified` when you have actually checked the entry against a source.
6. Keep code changes small and dependency-free. This project intentionally has no build step.

Good first contributions: verifying an existing drug, fixing a typo, filling a vague interaction mechanism, adding a missing drug to an existing subclass.

---

## Disclaimer

This project is for **education and revision only**. It is not a substitute for professional judgement, local guidelines or an authoritative drug reference, and it must not be used to make prescribing, dosing or treatment decisions.

Much of the content was drafted with AI assistance (Claude) from general pharmacology knowledge, not copied from a primary source. It may contain errors, outdated information or details that differ in your jurisdiction (availability, brands, doses, schedules and guidance change). Always check the current product information and your local guidelines. Treat any entry whose `verified` field is empty as unchecked.

---

## License

Choose a licence before sharing publicly. A common choice is the **MIT License** for the code (`index.html`, `style.css`, `app.js`). Decide separately how you want to license the content in `drugs.json` (for example CC BY-SA 4.0), and make sure nothing in it is copied from a copyrighted source.
