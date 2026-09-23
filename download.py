#!/usr/bin/env python3
"""Provenance / integrity helper for the benchmark data.

The pages are already bundled under bench/ for convenience, so the benchmark
runs out of the box. This script is the other half: it reads manifest.json and
either verifies the bundled data or prints, per page, exactly where the canonical
copy comes from so anyone can re-fetch from source under the original licence.

Usage:
  python download.py --check     # verify every manifest page is present locally
  python download.py --sources   # print the canonical source of each page
"""
import argparse, json, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "manifest.json")


def load():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def check(m):
    missing = []
    for p in m["pages"]:
        for key in ("image", "gt"):
            path = os.path.join(HERE, p[key])
            if not os.path.exists(path):
                missing.append(path)
    if missing:
        print(f"MISSING {len(missing)} files:")
        for x in missing:
            print("  ", x)
        sys.exit(1)
    print(f"OK: all {len(m['pages'])} pages present (images + ground truth).")


def sources(m):
    by_ds = defaultdict(list)
    for p in m["pages"]:
        by_ds[(p["source_dataset"], p["source_repo"], p.get("license", ""))].append(p)
    print(f"{m['dataset']} — {m['n_pages']} pages\n")
    for (ds, repo, lic), pages in sorted(by_ds.items()):
        langs = sorted({p["language"] for p in pages})
        print(f"* {ds}")
        print(f"    languages : {', '.join(langs)}")
        print(f"    pages     : {len(pages)}")
        print(f"    source    : {repo}")
        print(f"    licence   : {lic}")
        excl = [p['page'] for p in pages if p.get('excluded')]
        if excl:
            print(f"    note      : EXCLUDED from scoring ({pages[0]['excluded']})")
        print()
    print("To rebuild from source: fetch each dataset from the repo above under its\n"
          "own licence, keeping the same page basenames, into bench/ and bench/gt/.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify bundled data is complete")
    ap.add_argument("--sources", action="store_true", help="print canonical source per dataset")
    a = ap.parse_args()
    m = load()
    if a.check:
        check(m)
    elif a.sources:
        sources(m)
    else:
        ap.print_help()
