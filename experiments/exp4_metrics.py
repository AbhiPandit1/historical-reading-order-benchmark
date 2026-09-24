# Robustness of the ordering-control result across multiple reading-order metrics.
import glob,os,json,sys
sys.path.insert(0,"harness"); sys.path.insert(0,"experiments")
from bench_lib import load_gt, match
from ordering import METHODS
MULTI=["eng","swe","frm"]
def boxes_of(tool,base): return [ln["bbox"] for ln in json.load(open(f"bench/pred/{tool}/{base}.json"))["lines"]]

def metrics(gt, pred_boxes, order_idx):
    pred=[{"bbox":pred_boxes[i],"order":r} for r,i in enumerate(order_idx)]
    pairs=match(gt,pred); 
    if len(pairs)<15 or len(pairs)<0.6*len(gt): return None
    prank={gi:pred[pj]["order"] for gi,pj in pairs}
    gis=sorted(prank)                          # true order (ascending gi)
    pred_positions=[prank[g] for g in gis]     # predicted order value at each true position
    n=len(gis)
    # rank of each item in predicted order (0..n-1)
    order_sorted=sorted(range(n), key=lambda k: pred_positions[k])
    pred_rank=[0]*n
    for r,k in enumerate(order_sorted): pred_rank[k]=r
    true_rank=list(range(n))
    # Kendall tau
    c=d=0
    for i in range(n):
        for j in range(i+1,n):
            if pred_positions[i]<pred_positions[j]: c+=1
            elif pred_positions[i]>pred_positions[j]: d+=1
    tau=(c-d)/(c+d) if c+d else 1.0
    # Spearman rho
    import statistics
    dsq=sum((pred_rank[i]-true_rank[i])**2 for i in range(n))
    rho=1-6*dsq/(n*(n*n-1)) if n>1 else 1.0
    # normalized Spearman footrule distance (0=perfect,1=worst)
    foot=sum(abs(pred_rank[i]-true_rank[i]) for i in range(n))
    norm=(n*n)//2 if n%2==0 else (n*n-1)//2
    footrule=foot/norm if norm else 0.0
    return tau,rho,footrule

agg={}
for xml in sorted(glob.glob("bench/gt/*.xml")):
    base=os.path.basename(xml)[:-4]; lang=base.split("_")[0]
    if lang not in MULTI: continue
    gt=load_gt(xml); yb=boxes_of("yolo",base)
    for s,idx in [("YOLO+naive",METHODS["topbottom"](yb)),("YOLO+columns",METHODS["columns"](yb))]:
        m=metrics(gt,yb,idx)
        if m: agg.setdefault(s,[]).append(m)
    kb=json.load(open(f"bench/pred/kraken/{base}.json"))["lines"]
    m=metrics(gt,[l["bbox"] for l in kb],[l["order"] for l in sorted(kb,key=lambda z:z["order"])])
    if m: agg.setdefault("kraken(native)",[]).append(m)

def mean(s,i): 
    v=[t[i] for t in agg[s]]; return sum(v)/len(v)
print("=== Multi-column: ordering-control robust across metrics ===\n")
print(f"{'system':<16}{'Kendall τ↑':>12}{'Spearman ρ↑':>13}{'footrule↓':>11}")
for s in ["YOLO+naive","YOLO+columns","kraken(native)"]:
    print(f"{s:<16}{mean(s,0):>12.2f}{mean(s,1):>13.2f}{mean(s,2):>11.2f}")
