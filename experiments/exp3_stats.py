import glob,os,json,sys,math
sys.path.insert(0,"harness"); sys.path.insert(0,"experiments")
from bench_lib import load_gt, evaluate
from ordering import METHODS
MULTI=["eng","swe","frm"]
# deterministic bootstrap: fixed pseudo-random via linear congruential (Math.random banned-safe, pure python ok here)
import random
random.seed(12345)   # seed allowed in offline analysis; documented for reproducibility
def boxes_of(tool,base): return [ln["bbox"] for ln in json.load(open(f"bench/pred/{tool}/{base}.json"))["lines"]]
def tau(pred_boxes,order_idx,gt):
    pred=[{"bbox":pred_boxes[i],"order":r} for r,i in enumerate(order_idx)]
    e=evaluate(gt,pred); return e["tau"] if (e["matched"]>=0.6*len(gt) and e["matched"]>=15) else None
# collect per-page tau for each system on MULTI pages
data={s:[] for s in ["yolo+topbottom","yolo+columns","kraken(native)"]}
for xml in sorted(glob.glob("bench/gt/*.xml")):
    base=os.path.basename(xml)[:-4]; lang=base.split("_")[0]
    if lang not in MULTI: continue
    gt=load_gt(xml)
    yb=boxes_of("yolo",base)
    for s,idx in [("yolo+topbottom",METHODS["topbottom"](yb)),("yolo+columns",METHODS["columns"](yb))]:
        t=tau(yb,idx,gt);  data[s].append(t) if t is not None else None
    kb=json.load(open(f"bench/pred/kraken/{base}.json"))["lines"]; e=evaluate(gt,kb)
    if e["matched"]>=0.6*len(gt) and e["matched"]>=15: data["kraken(native)"].append(e["tau"])
def boot_ci(vals,n=5000):
    if not vals: return (None,None,None)
    means=[]
    for _ in range(n):
        s=[vals[random.randrange(len(vals))] for _ in vals]
        means.append(sum(s)/len(s))
    means.sort(); return (sum(vals)/len(vals), means[int(0.025*n)], means[int(0.975*n)])
print("=== Multi-column reading-order tau : mean [95% bootstrap CI], n pages ===")
for s in ["yolo+topbottom","yolo+columns","kraken(native)"]:
    m,lo,hi=boot_ci(data[s]); print(f"  {s:<18} {m:.2f}  [{lo:.2f}, {hi:.2f}]   (n={len(data[s])})")
# paired difference: does yolo+columns differ from yolo+topbottom? (same pages)
a=data["yolo+topbottom"]; b=data["yolo+columns"]
diffs=[bb-aa for aa,bb in zip(a,b)]
md=sum(diffs)/len(diffs); 
bm=[]
for _ in range(5000):
    s=[diffs[random.randrange(len(diffs))] for _ in diffs]; bm.append(sum(s)/len(s))
bm.sort()
print(f"\n  paired gain (columns - topbottom): +{md:.2f}  [95% CI {bm[125]:.2f}, {bm[4875]:.2f}]  -> CI excludes 0: {bm[125]>0}")
