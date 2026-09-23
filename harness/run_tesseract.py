#!/usr/bin/env python3
"""Run Tesseract layout analysis over the benchmark images.

Tesseract is a layout-aware OCR engine, not a pure detector: image_to_data
returns words tagged with block / paragraph / line numbers, and it orders those
in a column-aware reading order. We group words into lines by (block, par, line)
and keep Tesseract's own order, which is why it scores well on reading order for
the pages it manages to detect.

Writes one prediction file per page to bench/pred/tesseract/<doc>.json.
"""
import glob, os, json, time
from collections import OrderedDict
from PIL import Image
import pytesseract

os.makedirs("bench/pred/tesseract", exist_ok=True)

for img in sorted(glob.glob("bench/*.jp*g") + glob.glob("bench/*.png")):
    base = os.path.splitext(os.path.basename(img))[0]
    if not os.path.exists(f"bench/gt/{base}.xml"):
        continue
    if os.path.exists(f"bench/pred/tesseract/{base}.json"):
        continue  # SKIP-GUARD
    im = Image.open(img).convert("RGB")
    t = time.time()
    d = pytesseract.image_to_data(im, output_type=pytesseract.Output.DICT)
    dt = time.time() - t
    # group words into lines, preserving Tesseract's traversal order
    lines = OrderedDict()
    for i in range(len(d["text"])):
        if not d["text"][i].strip():
            continue
        key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        x, y, w, h = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
        if key not in lines:
            lines[key] = [x, y, x + w, y + h]
        else:
            b = lines[key]
            b[0] = min(b[0], x); b[1] = min(b[1], y)
            b[2] = max(b[2], x + w); b[3] = max(b[3], y + h)
    pred = [{"bbox": [float(v) for v in box], "order": i}
            for i, box in enumerate(lines.values())]
    json.dump({"lines": pred, "time": dt},
              open(f"bench/pred/tesseract/{base}.json", "w"))
    print(base, "->", len(pred), f"{dt:.1f}s", flush=True)
print("tesseract done")
