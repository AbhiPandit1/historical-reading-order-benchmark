import glob,os,json,sys,re,random
import xml.etree.ElementTree as ET
sys.path.insert(0,"historical-reading-order-benchmark/harness"); sys.path.insert(0,"exp")
from bench_lib import load_gt, match, evaluate
from ordering import METHODS
random.seed(12345)

def load_gt_text(xmlf):
    r=ET.parse(xmlf).getroot(); m=re.match(r'\{(.*)\}',r.tag); ns={'p':m.group(1)} if m else {}
    lines=r.findall(".//p:TextLine",ns) if ns else r.findall(".//TextLine"); out=[]
    for i,L in enumerate(lines):
        a=L.attrib
        if all(k in a for k in ("HPOS","VPOS","WIDTH","HEIGHT")):
            x=float(a["HPOS"]);y=float(a["VPOS"]);w=float(a["WIDTH"]);h=float(a["HEIGHT"]); bbox=[x,y,x+w,y+h]
            ss=L.findall(".//p:String",ns) if ns else L.findall(".//String"); txt=" ".join(s.get("CONTENT","") for s in ss).strip()
        else:
            c=L.find("p:Coords",ns) if ns else L.find("Coords")
            if c is None or not c.get("points"): continue
            pts=[tuple(map(float,p.split(','))) for p in c.get("points").split()]
            xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; bbox=[min(xs),min(ys),max(xs),max(ys)]
            u=L.find(".//p:Unicode",ns) if ns else L.find(".//Unicode"); txt=(u.text or "").strip() if u is not None else ""
        out.append({"bbox":bbox,"order":i,"text":txt})
    return out

def wer(ref,hyp):
    n,mm=len(ref),len(hyp)
    if n==0: return 0.0
    dp=list(range(mm+1))
    for i in range(1,n+1):
        prev=dp[0]; dp[0]=i
        for j in range(1,mm+1):
            cur=dp[j]; dp[j]=min(dp[j]+1,dp[j-1]+1,prev+(ref[i-1]!=hyp[j-1])); prev=cur
    return dp[mm]/n

# collect Swedish pages: existing swe_* (bench) + new gotas_/trolls_ (scale_eval)
pages=[]
for xml in sorted(glob.glob("bench/gt/swe_*.xml")):
    b=os.path.basename(xml)[:-4]; pages.append((b,xml,"bench"))
for xml in sorted(glob.glob("scale_eval/gt/*.xml")):
    b=os.path.basename(xml)[:-4]; pages.append((b,xml,"scale_eval"))

def yolo_boxes(root,b): return [l["bbox"] for l in json.load(open(f"{root}/pred/yolo/{b}.json"))["lines"]]
def kraken_pred(root,b): return json.load(open(f"{root}/pred/kraken/{b}.json"))["lines"]

taus={"naive":[],"columns":[],"kraken":[]}; wers={"naive":[],"columns":[],"kraken":[]}
used=0
for b,xml,root in pages:
    kp=f"{root}/pred/kraken/{b}.json"
    if not os.path.exists(kp): continue      # skip if kraken not ready
    gt=load_gt(xml); gtt=load_gt_text(xml); ng=len(gt)
    yb=yolo_boxes(root,b)
    def tau_wer(pred_boxes,order_idx):
        pred=[{"bbox":pred_boxes[i],"order":r} for r,i in enumerate(order_idx)]
        e=evaluate(gt,pred)
        if e["matched"]<15 or e["matched"]<0.6*ng: return None,None
        pairs=match(gtt,pred); prank={gi:pred[pj]["order"] for gi,pj in pairs}
        gis=list(prank); true_seq=sorted(gis); pred_seq=sorted(gis,key=lambda g:prank[g])
        ref=" ".join(gtt[g]["text"] for g in true_seq).split(); hyp=" ".join(gtt[g]["text"] for g in pred_seq).split()
        return e["tau"], wer(ref,hyp)
    tn,wn=tau_wer(yb,METHODS["topbottom"](yb))
    tc,wc=tau_wer(yb,METHODS["columns"](yb))
    kb=kraken_pred(root,b); ke=evaluate(gt,kb)
    kt_=ke["tau"] if (ke["matched"]>=15 and ke["matched"]>=0.6*ng) else None
    # kraken WER
    kw=None
    if kt_ is not None:
        pairs=match(gtt,kb); prank={gi:kb[pj]["order"] for gi,pj in pairs}
        gis=list(prank); ref=" ".join(gtt[g]["text"] for g in sorted(gis)).split()
        hyp=" ".join(gtt[g]["text"] for g in sorted(gis,key=lambda g:prank[g])).split(); kw=wer(ref,hyp)
    if None in (tn,tc,kt_): continue
    taus["naive"].append(tn); taus["columns"].append(tc); taus["kraken"].append(kt_)
    wers["naive"].append(wn); wers["columns"].append(wc); wers["kraken"].append(kw); used+=1

def ci(v,n=5000):
    m=sum(v)/len(v); bs=[]
    for _ in range(n): s=[v[random.randrange(len(v))] for _ in v]; bs.append(sum(s)/len(s))
    bs.sort(); return m,bs[int(.025*n)],bs[int(.975*n)]
print(f"=== SCALED Swedish set: n={used} pages (gota_hovratt + trolldomskommissionen + orig) ===\n")
print("reading-order tau  [95% CI]:")
for k in ["naive","columns","kraken"]:
    m,lo,hi=ci(taus[k]); print(f"  YOLO+{k:<8}" if k!="kraken" else "  kraken   ", f"{m:.2f} [{lo:.2f},{hi:.2f}]")
print("\norder-induced WER  [95% CI]:")
for k in ["naive","columns","kraken"]:
    m,lo,hi=ci(wers[k]); print(f"  {k:<8}", f"{m*100:.0f}% [{lo*100:.0f}%,{hi*100:.0f}%]")
