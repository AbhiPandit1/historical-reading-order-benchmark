import glob,os,json,time
from PIL import Image
from surya.detection import DetectionPredictor
det=DetectionPredictor()
for img in sorted(glob.glob("bench/*.jp*g")+glob.glob("bench/*.png")):
    base=os.path.splitext(os.path.basename(img))[0]
    if not os.path.exists(f"bench/gt/{base}.xml"): continue
    if os.path.exists(f"bench/pred/surya/{base}.json"): continue  # SKIP-GUARD
    im=Image.open(img).convert("RGB")
    _=det([im])
    t=time.time(); res=det([im])[0]; dt=time.time()-t
    boxes=[b.bbox for b in res.bboxes]           # [x1,y1,x2,y2]
    boxes=sorted(boxes,key=lambda z:z[1])         # top-to-bottom (pure detector)
    pred=[{"bbox":[float(v) for v in z],"order":i} for i,z in enumerate(boxes)]
    json.dump({"lines":pred,"time":dt}, open(f"bench/pred/surya/{base}.json","w"))
    print(base,"->",len(pred),f"{dt:.1f}s",flush=True)
print("surya done")
