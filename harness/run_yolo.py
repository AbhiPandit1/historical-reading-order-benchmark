#!/usr/bin/env python3
"""Run the domain-adapted YOLO line detector over the benchmark images.

Writes one prediction file per page to pred/yolo/<doc>.json, with line boxes
ordered top-to-bottom (the naive reading order a box detector gives you).
"""
import glob, os, json, time, sys
sys.path.insert(0, "seg_repo")  # https://github.com/AbhiPandit1/danish-htr-line-segmenter
from segment import load_model

model = load_model()
os.makedirs("pred/yolo", exist_ok=True)

for img in sorted(glob.glob("images/*.*")):
    base = os.path.splitext(os.path.basename(img))[0]
    if not os.path.exists(f"gt/{base}.xml"):
        continue
    t = time.time()
    r = model.predict(img, conf=0.25, verbose=False)[0]
    dt = time.time() - t
    boxes = sorted(r.boxes.xyxy.tolist(), key=lambda z: z[1])  # top-to-bottom
    pred = [{"bbox": list(map(float, z)), "order": i} for i, z in enumerate(boxes)]
    json.dump({"lines": pred, "time": dt}, open(f"pred/yolo/{base}.json", "w"))
    print(base, "->", len(pred), "lines", f"{dt:.2f}s")
