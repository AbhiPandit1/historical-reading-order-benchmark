# LayoutReader (learned reading-order) on Azure

`hantian/layoutreader` (ReadingBank-trained) run as an Azure Container Apps job
(`lr_azure_run.py`): fetch YOLO line boxes, normalise to 0-1000, run the model,
parse the reading-order logits, upload predictions to blob. It is included as a
*learned* reading-order baseline. On historical multi-column pages it does not
transfer (tau ~0.14, worse than a naive top-to-bottom sort), consistent with its
modern-business-document training domain.
