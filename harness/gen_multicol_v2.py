#!/usr/bin/env python3
"""Generator v2: realistic multi-column historical registers.
Adds ruled table grid (vertical column separators + horizontal rows), handwriting-ish
script fonts, per-line skew, header row, heavier degradation. YOLO labels: 0=line, 1=column."""
import os, argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

SCRIPT_FONTS = [f for f in [
 "/System/Library/Fonts/Supplemental/SnellRoundhand.ttc",
 "/System/Library/Fonts/Supplemental/Savoye LET.ttc",
 "/System/Library/Fonts/Supplemental/Apple Chancery.ttf",
 "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf",
 "/System/Library/Fonts/Supplemental/Noteworthy.ttc",
 "/System/Library/Fonts/Supplemental/Brush Script.ttf",
] if os.path.exists(f)]
WORDS=("Anders Pehr Karin Olof Nilsson dotter Larsson socken anno den blef född gift död "
       "Trin post soldat hustru barn gaard husman tjenare enka war som att och").split()

def paper(W,H,rng):
    b=np.zeros((H,W,3),np.float32); t=rng.uniform(196,228)
    b[:]=(t,t-rng.uniform(8,18),t-rng.uniform(24,46)); b+=rng.normal(0,7,(H,W,3))
    for _ in range(rng.integers(6,14)):
        x,y=rng.integers(0,W),rng.integers(0,H); r=rng.integers(50,190)
        yy,xx=np.ogrid[:H,:W]; b[((xx-x)**2+(yy-y)**2)<r*r]-=rng.uniform(4,16)
    return Image.fromarray(np.clip(b,0,255).astype(np.uint8))

def ink(rng): return (int(rng.integers(20,60)),int(rng.integers(18,50)),int(rng.integers(15,45)))

def render_line(txt,fnt,rng):
    tb=fnt.getbbox(txt); w=tb[2]-tb[0]+8; h=tb[3]-tb[1]+8
    lay=Image.new("RGBA",(max(w,10),max(h,10)),(0,0,0,0)); d=ImageDraw.Draw(lay)
    d.text((4-tb[0],4-tb[1]),txt,fill=ink(rng)+(255,),font=fnt)
    if rng.random()<0.7: lay=lay.rotate(rng.uniform(-2.2,2.2),expand=True,resample=Image.BICUBIC)
    return lay

def rule(d,x1,y1,x2,y2,rng,fill=(70,60,55)):        # slightly wavy ruled line
    n=6; pts=[]
    for i in range(n+1):
        t=i/n; x=x1+(x2-x1)*t; y=y1+(y2-y1)*t+rng.uniform(-1.2,1.2)
        pts.append((x,y))
    d.line(pts,fill=fill,width=1)

def gen(rng):
    W=int(rng.integers(1040,1440)); H=int(rng.integers(760,1040))
    img=paper(W,H,rng); d=ImageDraw.Draw(img); boxes=[]
    m=int(W*rng.uniform(0.03,0.055)); top=m
    ncol=int(rng.integers(2,6)); gap=0
    colw=(W-2*m)//ncol
    # header row
    hbot=top
    if rng.random()<0.7:
        fs=int(rng.integers(26,38)); f=ImageFont.truetype(rng.choice(SCRIPT_FONTS),fs)
        for c in range(ncol):
            cx1=m+c*colw; lay=render_line(rng.choice(WORDS).capitalize(),f,rng)
            img.paste(lay,(cx1+6,top+2),lay); tb=(cx1+6,top+2,cx1+6+lay.width,top+2+lay.height)
            boxes.append((0,tb[0],tb[1],tb[2],tb[3]))
        hbot=top+fs+10; rule(d,m,hbot,W-m,hbot,rng,(60,50,45)); top=hbot+6
    # vertical column rules
    for c in range(ncol+1):
        x=m+c*colw; rule(d,x,top,x,H-m,rng,(80,70,62))
    # fill each column with lines + row rules
    for c in range(ncol):
        cx1=m+c*colw; cx2=cx1+colw; y=top+int(rng.integers(2,14)); cell=[]
        while y<H-m-26:
            fs=int(rng.integers(20,32)); f=ImageFont.truetype(rng.choice(SCRIPT_FONTS),fs)
            if rng.random()<0.10: y+=int(fs*rng.uniform(0.7,1.5)); continue
            txt=" ".join(rng.choice(WORDS) for _ in range(rng.integers(1,4)))
            lay=render_line(txt,f,rng)
            if lay.width>colw-12:
                lay=lay.crop((0,0,colw-12,lay.height))
            xoff=cx1+6+int(rng.uniform(0,0.1)*colw)
            img.paste(lay,(xoff,y),lay); tb=(xoff,y,xoff+lay.width,y+lay.height)
            boxes.append((0,tb[0],tb[1],tb[2],tb[3])); cell.append(tb)
            y2=y+lay.height+int(fs*rng.uniform(0.25,0.6))
            if rng.random()<0.5: rule(d,cx1+2,y2-2,cx2-2,y2-2,rng,(120,110,100))  # row rule
            y=y2
        boxes.append((1,cx1+3,top+2,cx2-3,H-m-3))   # column region
    # degradation
    if rng.random()<0.7: img=img.filter(ImageFilter.GaussianBlur(rng.uniform(0.4,1.3)))
    a=np.asarray(img).astype(np.float32)+rng.normal(0,rng.uniform(3,9),(H,W,3))
    # ink blots
    img=Image.fromarray(np.clip(a,0,255).astype(np.uint8)); d2=ImageDraw.Draw(img)
    for _ in range(rng.integers(0,6)):
        x,y=rng.integers(0,W),rng.integers(0,H); r=rng.integers(2,7)
        d2.ellipse([x,y,x+r,y+r],fill=(60,50,45))
    if rng.random()<0.35:
        bt=paper(W,H,rng).transpose(Image.FLIP_LEFT_RIGHT); img=Image.blend(img,bt,0.07)
    return img,boxes,W,H

def yolo(b,W,H):
    c,x1,y1,x2,y2=b; return f"{c} {((x1+x2)/2)/W:.6f} {((y1+y2)/2)/H:.6f} {(x2-x1)/W:.6f} {(y2-y1)/H:.6f}"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("-n",type=int,default=8); ap.add_argument("--out",default="synth_v2"); ap.add_argument("--seed",type=int,default=0)
    a=ap.parse_args(); rng=np.random.default_rng(a.seed)
    os.makedirs(f"{a.out}/images",exist_ok=True); os.makedirs(f"{a.out}/labels",exist_ok=True)
    for i in range(a.n):
        img,boxes,W,H=gen(rng); img.save(f"{a.out}/images/v2_{i:05d}.jpg",quality=86)
        open(f"{a.out}/labels/v2_{i:05d}.txt","w").write("\n".join(yolo(b,W,H) for b in boxes))
    print(f"generated {a.n} -> {a.out}/")
if __name__=="__main__": main()
