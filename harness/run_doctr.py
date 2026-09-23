import glob,os,json,time
from PIL import Image
import numpy as np
from doctr.models import ocr_predictor
model=ocr_predictor(pretrained=True, assume_straight_pages=True)
for img in sorted(glob.glob("bench/*.jp*g")+glob.glob("bench/*.png")):
    base=os.path.splitext(os.path.basename(img))[0]
    if not os.path.exists(f"bench/gt/{base}.xml"): continue
    if os.path.exists(f"bench/pred/doctr/{base}.json"): continue  # SKIP-GUARD
    im=np.array(Image.open(img).convert("RGB")); H,W=im.shape[:2]
    t=time.time(); doc=model([im]); dt=time.time()-t
    pred=[]; i=0
    for page in doc.pages:
        for block in page.blocks:
            for line in block.lines:      # docTR document order = reading order
                (x1,y1),(x2,y2)=line.geometry
                pred.append({"bbox":[x1*W,y1*H,x2*W,y2*H],"order":i}); i+=1
    json.dump({"lines":pred,"time":dt}, open(f"bench/pred/doctr/{base}.json","w"))
    print(base,"->",len(pred),f"{dt:.1f}s",flush=True)
print("doctr done")
