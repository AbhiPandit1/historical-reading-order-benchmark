import glob,os,json,time,warnings
warnings.filterwarnings("ignore")
from PIL import Image
from kraken.blla import segment
for img in sorted(glob.glob("bench/*.jp*g")+glob.glob("bench/*.png")):
    base=os.path.splitext(os.path.basename(img))[0]
    if not os.path.exists(f"bench/gt/{base}.xml"): continue
    if os.path.exists(f"bench/pred/kraken/{base}.json"): continue
    try:
        im=Image.open(img).convert("RGB")
        t=time.time(); seg=segment(im); dt=time.time()-t
        pred=[]
        for i,l in enumerate(seg.lines):      # kraken native reading order
            xs=[p[0] for p in l.boundary]; ys=[p[1] for p in l.boundary]
            pred.append({"bbox":[float(min(xs)),float(min(ys)),float(max(xs)),float(max(ys))],"order":i})
        json.dump({"lines":pred,"time":dt}, open(f"bench/pred/kraken/{base}.json","w"))
        print(base,"->",len(pred),"lines",f"{dt:.1f}s",flush=True)
    except Exception as e:
        print(base,"ERR",str(e)[:80],flush=True)
print("kraken done")
