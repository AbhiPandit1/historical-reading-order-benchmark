import xml.etree.ElementTree as ET, re
def load_gt(xmlf):
    r=ET.parse(xmlf).getroot(); m=re.match(r'\{(.*)\}',r.tag); ns={'p':m.group(1)} if m else {}
    def F(tag): return r.findall(f".//p:{tag}",ns) if ns else r.findall(f".//{tag}")
    out=[]
    for i,L in enumerate(F("TextLine")):      # document order = reading order
        a=L.attrib
        if all(k in a for k in ("HPOS","VPOS","WIDTH","HEIGHT")):   # ALTO
            x=float(a["HPOS"]);y=float(a["VPOS"]);w=float(a["WIDTH"]);h=float(a["HEIGHT"])
            out.append({"bbox":[x,y,x+w,y+h],"order":i})
        else:                                   # PAGE (Coords points)
            c=L.find("p:Coords",ns) if ns else L.find("Coords")
            if c is not None and c.get("points"):
                pts=[tuple(map(float,p.split(','))) for p in c.get("points").split()]
                xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
                out.append({"bbox":[min(xs),min(ys),max(xs),max(ys)],"order":i})
    return out
def iou(a,b):
    x1=max(a[0],b[0]);y1=max(a[1],b[1]);x2=min(a[2],b[2]);y2=min(a[3],b[3])
    inter=max(0,x2-x1)*max(0,y2-y1); ua=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter
    return inter/ua if ua>0 else 0
def match(gt,pred,thr=0.5):
    pairs=[];used=set()
    for gi,g in enumerate(gt):
        best=(-1,None)
        for pj,p in enumerate(pred):
            if pj in used: continue
            v=iou(g["bbox"],p["bbox"])
            if v>best[0]: best=(v,pj)
        if best[0]>=thr: pairs.append((gi,best[1]));used.add(best[1])
    return pairs
def kt(seq):
    n=len(seq)
    if n<2: return 1.0
    c=d=0
    for i in range(n):
        for j in range(i+1,n):
            if seq[i]<seq[j]:c+=1
            elif seq[i]>seq[j]:d+=1
    return (c-d)/(c+d) if (c+d)>0 else 1.0
def evaluate(gt,pred):
    pairs=match(gt,pred); tp=len(pairs)
    P=tp/len(pred) if pred else 0; R=tp/len(gt) if gt else 0; F=2*P*R/(P+R) if P+R>0 else 0
    pr={gi:pred[pj]["order"] for gi,pj in pairs}
    seq=[pr[gi] for gi in sorted(pr)]
    return dict(P=P,R=R,F=F,tau=kt(seq),matched=tp,n_gt=len(gt),n_pred=len(pred))
