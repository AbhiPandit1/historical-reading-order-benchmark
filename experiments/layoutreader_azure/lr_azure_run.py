import os, json, urllib.request, io, traceback
import torch
from transformers import LayoutLMv3ForTokenClassification
from azure.storage.blob import BlobServiceClient
from PIL import Image

CS = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
cont = BlobServiceClient.from_connection_string(CS).get_container_client("ppout")
BR = "https://raw.githubusercontent.com/AbhiPandit1/historical-reading-order-benchmark/paper-v2-ordering-control/bench"
MAIN = "https://raw.githubusercontent.com/AbhiPandit1/historical-reading-order-benchmark/main/bench"

def fetch_json(url):
    return json.loads(urllib.request.urlopen(url).read())

def img_size(base):
    for root in (MAIN, BR):
        try:
            data = urllib.request.urlopen(f"{root}/{base}.jpg").read()
            return Image.open(io.BytesIO(data)).size
        except Exception:
            continue
    raise RuntimeError("no image "+base)

def boxes2inputs(boxes):
    bbox = [[0,0,0,0]] + boxes + [[0,0,0,0]]
    input_ids = [0] + [6]*len(boxes) + [2]
    attn = [1]*len(input_ids)
    return {"bbox": torch.tensor([bbox]), "attention_mask": torch.tensor([attn]),
            "input_ids": torch.tensor([input_ids])}

def parse_logits(logits, length):
    logits = logits[1:length+1, :length]
    orders = logits.argsort(descending=False).tolist()
    ret = [o.pop() for o in orders]
    while True:
        conflict = {}
        for idx, order in enumerate(ret):
            conflict.setdefault(order, []).append(idx)
        conflict = {k:v for k,v in conflict.items() if len(v)>1}
        if not conflict: break
        for order, idxes in conflict.items():
            keep = sorted(idxes, key=lambda i: logits[i, order], reverse=True)
            for i in keep[1:]:
                ret[i] = orders[i].pop()
    return ret

model = LayoutLMv3ForTokenClassification.from_pretrained("hantian/layoutreader")
model.eval()
print("LayoutReader loaded", flush=True)

for base in ["eng_00","swe_02","frm_00"]:
    try:
        yolo = fetch_json(f"{BR}/pred/yolo/{base}.json")["lines"]
        W,H = img_size(base)
        raw = [l["bbox"] for l in yolo]
        norm = [[min(1000,max(0,int(b[0]*1000/W))), min(1000,max(0,int(b[1]*1000/H))),
                 min(1000,max(0,int(b[2]*1000/W))), min(1000,max(0,int(b[3]*1000/H)))] for b in raw]
        with torch.no_grad():
            logits = model(**boxes2inputs(norm)).logits.cpu().squeeze(0)
        order = parse_logits(logits, len(norm))   # order[i] = reading position of box i
        pred = [{"bbox": raw[i], "order": int(order[i])} for i in range(len(raw))]
        out = f"{base}_lr.json"
        json.dump({"lines": pred, "source":"LayoutReader hantian/layoutreader on YOLO boxes (Azure)"}, open(out,"w"))
        with open(out,"rb") as f: cont.upload_blob(name=f"{base}_lr.json", data=f, overwrite=True)
        print("DONE", base, len(pred), flush=True)
    except Exception as e:
        print("ERR", base, repr(e), flush=True); traceback.print_exc()
print("ALL DONE", flush=True)
