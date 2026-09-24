import glob,os,json,time
from PIL import Image
from kraken import blla
for img in sorted(glob.glob("scale_eval/img/*.jpg")):
    base=os.path.splitext(os.path.basename(img))[0]
    out=f"scale_eval/pred/kraken/{base}.json"
    if os.path.exists(out): continue
    im=Image.open(img).convert("RGB")
    t=time.time(); seg=blla.segment(im); dt=time.time()-t
    lines=[]
    for i,l in enumerate(seg.lines):
        # bounding box from baseline/boundary
        pts=l.boundary if getattr(l,"boundary",None) else l.baseline
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        lines.append({"bbox":[min(xs),min(ys),max(xs),max(ys)],"order":i})
    json.dump({"lines":lines,"time":dt},open(out,"w"))
    print(base,len(lines),f"{dt:.1f}s",flush=True)
print("kraken scale done; total:",len(glob.glob("scale_eval/pred/kraken/*.json")))
