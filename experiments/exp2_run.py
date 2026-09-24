import glob,os,json,sys,re
import xml.etree.ElementTree as ET
sys.path.insert(0,"harness")
sys.path.insert(0,"experiments")
from bench_lib import match
from ordering import METHODS

def load_gt_text(xmlf):
    r=ET.parse(xmlf).getroot(); m=re.match(r'\{(.*)\}',r.tag); ns={'p':m.group(1)} if m else {}
    def find(el,tag): return el.findall(f"p:{tag}",ns) if ns else el.findall(tag)
    out=[]
    lines=r.findall(".//p:TextLine",ns) if ns else r.findall(".//TextLine")
    for i,L in enumerate(lines):
        a=L.attrib
        if all(k in a for k in ("HPOS","VPOS","WIDTH","HEIGHT")):  # ALTO
            x=float(a["HPOS"]);y=float(a["VPOS"]);w=float(a["WIDTH"]);h=float(a["HEIGHT"])
            bbox=[x,y,x+w,y+h]
            strs=L.findall(".//p:String",ns) if ns else L.findall(".//String")
            txt=" ".join(s.get("CONTENT","") for s in strs).strip()
        else:  # PAGE
            c=L.find("p:Coords",ns) if ns else L.find("Coords")
            if c is None or not c.get("points"): continue
            pts=[tuple(map(float,p.split(','))) for p in c.get("points").split()]
            xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
            bbox=[min(xs),min(ys),max(xs),max(ys)]
            u=L.find(".//p:Unicode",ns) if ns else L.find(".//Unicode")
            txt=(u.text or "").strip() if u is not None else ""
        out.append({"bbox":bbox,"order":i,"text":txt})
    return out

def wer(ref_words, hyp_words):
    n,mm=len(ref_words),len(hyp_words)
    if n==0: return 0.0
    dp=list(range(mm+1))
    for i in range(1,n+1):
        prev=dp[0]; dp[0]=i
        for j in range(1,mm+1):
            cur=dp[j]
            dp[j]=min(dp[j]+1, dp[j-1]+1, prev+(ref_words[i-1]!=hyp_words[j-1]))
            prev=cur
    return dp[mm]/n

MULTI=["eng","swe","frm"]; SINGLE=["spa","ita","fra","frp","cat"]
def boxes_of(tool,base): return [ln["bbox"] for ln in json.load(open(f"bench/pred/{tool}/{base}.json"))["lines"]]

def order_induced_wer(gt, pred_boxes, order_idx):
    pred=[{"bbox":pred_boxes[i],"order":rank} for rank,i in enumerate(order_idx)]
    pairs=match(gt,pred)                       # (gi,pj)
    if len(pairs)<5: return None
    prank={gi:pred[pj]["order"] for gi,pj in pairs}
    matched_gi=list(prank.keys())
    true_seq=[g for g in sorted(matched_gi)]                       # true reading order
    pred_seq=[g for g in sorted(matched_gi,key=lambda g:prank[g])] # predicted order
    ref=" ".join(gt[g]["text"] for g in true_seq).split()
    hyp=" ".join(gt[g]["text"] for g in pred_seq).split()
    return wer(ref,hyp)

SYS=[("yolo","topbottom"),("yolo","columns"),("surya","topbottom"),("surya","columns")]
agg={}
for xml in sorted(glob.glob("bench/gt/*.xml")):
    base=os.path.basename(xml)[:-4]; lang=base.split("_")[0]
    if lang not in MULTI+SINGLE: continue
    gt=load_gt_text(xml)
    for tool,mname in SYS:
        b=boxes_of(tool,base)
        w=order_induced_wer(gt,b,METHODS[mname](b))
        if w is not None: agg.setdefault((f"{tool}+{mname}",lang),[]).append(w)
    # kraken native
    kb=json.load(open(f"bench/pred/kraken/{base}.json"))["lines"]
    w=order_induced_wer(gt,[l["bbox"] for l in kb],[l["order"] for l in sorted(kb,key=lambda z:z["order"])])
    if w is not None: agg.setdefault(("kraken(native)",lang),[]).append(w)

def gm(system,langs):
    v=[x for l in langs for x in agg.get((system,l),[])]
    return sum(v)/len(v) if v else None
SYSTEMS=["yolo+topbottom","yolo+columns","surya+topbottom","surya+columns","kraken(native)"]
print("=== Order-induced WER (perfect line recognition assumed; lower=better) ===\n")
print(f"{'system':<20}{'MULTI-col':>12}{'SINGLE-col':>12}")
for s in SYSTEMS:
    m=gm(s,MULTI); si=gm(s,SINGLE)
    print(f"{s:<20}{(f'{m*100:.0f}%' if m is not None else '-'):>12}{(f'{si*100:.0f}%' if si is not None else '-'):>12}")
print("\n=== per multi-column language ===")
print(f"{'system':<20}"+"".join(f"{l:>8}" for l in MULTI))
for s in SYSTEMS:
    print(f"{s:<20}"+"".join(f"{(f'{gm(s,[l])*100:.0f}%' if gm(s,[l]) is not None else '-'):>8}" for l in MULTI))
