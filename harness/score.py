#!/usr/bin/env python3
"""Score every system against ground truth and print the benchmark tables.

Reading order (Kendall tau) is only reported for a page where the system matched
enough lines to make an order meaningful: >= 60% of GT lines AND >= 15 lines.
Otherwise the cell reads 'det-fail' with the mean matched fraction. German is
excluded from scoring because its ground truth is under-annotated (see
data_note/SOURCES.md).
"""
import glob, os, json
from bench_lib import load_gt, evaluate

TOOLS = ["kraken", "yolo", "tesseract", "surya", "doctr"]
# scored languages, grouped by layout; German ('deu') excluded on purpose
MULTICOL = ["eng", "swe", "frm"]
SINGLECOL = ["spa", "ita", "fra", "frp", "cat"]
NAME = {"eng": "English", "swe": "Swedish", "frm": "Middle-French",
        "spa": "Spanish", "ita": "Italian", "fra": "French",
        "frp": "Franco-prov", "cat": "Catalan"}
MIN_FRAC, MIN_N = 0.60, 15  # reading-order validity guard

def cell(lang, tool):
    Fs, taus, fracs = [], [], []
    for xml in sorted(glob.glob(f"bench/gt/{lang}_*.xml")):
        base = os.path.basename(xml)[:-4]
        gt = load_gt(xml); ng = len(gt)
        pf = f"bench/pred/{tool}/{base}.json"
        if not os.path.exists(pf):
            continue
        e = evaluate(gt, json.load(open(pf))["lines"])
        Fs.append(e["F"]); fracs.append(e["matched"] / ng if ng else 0)
        if e["matched"] >= MIN_FRAC * ng and e["matched"] >= MIN_N:
            taus.append(e["tau"])
    if not Fs:
        return None
    F = sum(Fs) / len(Fs)
    if taus:
        return f"{F:.2f} / {sum(taus)/len(taus):.2f}[{len(taus)}/5]"
    return f"{F:.2f} / det-fail({sum(fracs)/len(fracs)*100:.0f}%)"

def block(title, langs):
    print(f"\n### {title}")
    print(f"{'lang':<14}" + "".join(f"{t:>22}" for t in TOOLS))
    for l in langs:
        print(f"{NAME[l]:<14}" + "".join(f"{(cell(l,t) or '-'):>22}" for t in TOOLS))

print("Historical reading-order benchmark  —  F / tau[valid-pages]")
block("Multi-column / complex layout", MULTICOL)
block("Single-column / simple layout (control)", SINGLECOL)

print("\n### Overall (eight scored languages)")
for t in TOOLS:
    Fs, taus, times = [], [], []
    for l in MULTICOL + SINGLECOL:
        for xml in sorted(glob.glob(f"bench/gt/{l}_*.xml")):
            base = os.path.basename(xml)[:-4]; gt = load_gt(xml); ng = len(gt)
            pf = f"bench/pred/{t}/{base}.json"
            if not os.path.exists(pf):
                continue
            j = json.load(open(pf)); e = evaluate(gt, j["lines"])
            Fs.append(e["F"]); times.append(j.get("time", 0))
            if e["matched"] >= MIN_FRAC * ng and e["matched"] >= MIN_N:
                taus.append(e["tau"])
    F = sum(Fs)/len(Fs) if Fs else 0
    tau = sum(taus)/len(taus) if taus else float("nan")
    spd = sum(times)/len(times) if times else 0
    print(f"  {t:<10} F={F:.2f}  tau={tau:.2f} ({len(taus)} valid pages)  {spd:.1f}s/page")
