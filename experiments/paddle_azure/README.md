# PaddleOCR PP-StructureV3 on Azure

PP-StructureV3's full pipeline is too heavy for local CPU, so it was run as an
Azure Container Apps job (paddle image; layout+text+reading-order only, table/
formula/chart/seal disabled; input downscaled to 1500px). `pp_azure_run.py` is the
job script: it fetches the benchmark pages, runs PP-StructureV3, and uploads the
raw result JSON to blob. Reading order is reconstructed from `parsing_res_list`
(region `block_order`) with lines ordered top-to-bottom within each region, then
coords rescaled to original resolution. Raw outputs: `bench/pred/ppstructure/raw/`.
