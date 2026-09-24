import os, glob, json, traceback, urllib.request
from azure.storage.blob import BlobServiceClient
from PIL import Image

CS = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
cont = BlobServiceClient.from_connection_string(CS).get_container_client("ppout")
RAW = "https://raw.githubusercontent.com/AbhiPandit1/historical-reading-order-benchmark/main/bench"

def up(local, name):
    with open(local, "rb") as f:
        cont.upload_blob(name=name, data=f, overwrite=True)
    print("UPLOADED", name, os.path.getsize(local), flush=True)

from paddleocr import PPStructureV3
p = PPStructureV3(use_table_recognition=False, use_formula_recognition=False,
                  use_chart_recognition=False, use_seal_recognition=False,
                  use_doc_orientation_classify=False, use_doc_unwarping=False)
print("PPStructureV3 ready (lite)", flush=True)

TARGET_W = 1500
factors = {}
for base in ["eng_00", "swe_02", "frm_00"]:
    src = f"{base}_src.jpg"; small = f"{base}.jpg"
    try:
        urllib.request.urlretrieve(f"{RAW}/{base}.jpg", src)
        im = Image.open(src).convert("RGB"); ow, oh = im.size
        f = ow / TARGET_W
        im.resize((TARGET_W, int(oh / f))).save(small, quality=85)
        factors[base] = {"orig_w": ow, "orig_h": oh, "factor": f}
        print("prepared", base, "orig", ow, "x", oh, "factor", round(f, 3), flush=True)
        res = p.predict(small)
        for r in res:
            r.save_to_json(f"{base}_res.json")
            for cand in [f"{base}_res.json"] + glob.glob(f"{base}_res.json/*") + glob.glob(f"{base}_res*"):
                if os.path.isfile(cand): up(cand, os.path.basename(cand).replace("_res", ""))
            break
        print("DONE", base, flush=True)
    except Exception as e:
        print("ERR", base, repr(e), flush=True); traceback.print_exc()
json.dump(factors, open("factors.json", "w")); up("factors.json", "factors.json")
print("ALL DONE", flush=True)
