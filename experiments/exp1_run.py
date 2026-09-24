import glob,os,json,sys
sys.path.insert(0,"harness")
sys.path.insert(0,"experiments")
from bench_lib import load_gt, evaluate
from ordering import METHODS

MULTI=["eng","swe","frm"]; SINGLE=["spa","ita","fra","frp","cat"]
LANGS=MULTI+SINGLE
def boxes_of(tool,base):
    return [ln["bbox"] for ln in json.load(open(f"bench/pred/{tool}/{base}.json"))["lines"]]

def tau_for(pred_boxes, order_idx, gt):
    pred=[{"bbox":pred_boxes[i],"order":rank} for rank,i in enumerate(order_idx)]
    return evaluate(gt,pred)

# collect per (system, method) tau, split multi vs single
agg={}
for xml in sorted(glob.glob("bench/gt/*.xml")):
    base=os.path.basename(xml)[:-4]; lang=base.split("_")[0]
    if lang not in LANGS: continue
    gt=load_gt(xml); ng=len(gt)
    # detectors with geometric ordering
    for tool in ["yolo","surya"]:
        b=boxes_of(tool,base)
        for mname,mfn in METHODS.items():
            e=tau_for(b, mfn(b), gt)
            if e["matched"]>=0.6*ng and e["matched"]>=15:
                agg.setdefault((f"{tool}+{mname}",lang),[]).append(e["tau"])
    # kraken native (reference upper bound)
    kb=json.load(open(f"bench/pred/kraken/{base}.json"))["lines"]
    e=evaluate(gt,kb)
    if e["matched"]>=0.6*ng and e["matched"]>=15:
        agg.setdefault(("kraken(native)",lang),[]).append(e["tau"])

def group_mean(system, langs):
    vals=[v for l in langs for v in agg.get((system,l),[])]
    return sum(vals)/len(vals) if vals else None

SYSTEMS=["yolo+topbottom","yolo+columns","yolo+xycut",
         "surya+topbottom","surya+columns","surya+xycut","kraken(native)"]
print("=== Reading-order tau : effect of a geometric ordering stage ===\n")
print(f"{'system':<20}{'MULTI-col':>12}{'SINGLE-col':>12}")
for s in SYSTEMS:
    m=group_mean(s,MULTI); si=group_mean(s,SINGLE)
    print(f"{s:<20}{(f'{m:.2f}' if m else '-'):>12}{(f'{si:.2f}' if si else '-'):>12}")
print("\n=== per multi-column language (the money table) ===")
print(f"{'system':<20}"+"".join(f"{l:>8}" for l in MULTI))
for s in SYSTEMS:
    print(f"{s:<20}"+"".join(f"{(f'{group_mean(s,[l]):.2f}' if group_mean(s,[l]) is not None else '-'):>8}" for l in MULTI))
