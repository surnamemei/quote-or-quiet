"""S68 (gate G4, second test): seal 1,500 NQ-open validation questions (google-research-datasets/nq_open, CC BY-SA 3.0; downloaded 2026-11-12 under the user's download permission),
drawn with seed 6801. Writes results/runs/s68/sealed/items.jsonl (S29 item format) and seal_hashes.txt; prints counts and the hash only. python -B results/runs/s68/seal68.py"""
import hashlib, json, random
from pathlib import Path
import pyarrow.parquet as pq
ROOT = Path(__file__).resolve().parents[3]
t = pq.read_table(ROOT / "data/external/nq_open/nq_open/validation-00000-of-00001.parquet").to_pylist()
idx = list(range(len(t))); random.Random(6801).shuffle(idx)
out = [{"id": f"nq-{i}", "q": t[i]["question"], "gold": list(t[i]["answer"]), "relation": "nq", "stratum": "nq", "qid": ""} for i in idx[:1500]]
p = ROOT / "results/runs/s68/sealed/items.jsonl"
with open(p, "w", encoding="utf-8") as f:
    for e in out:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
h = hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT / "results/runs/s68/seal_hashes.txt").write_text(f"items.jsonl {h}\n", encoding="utf-8")
print("sealed", len(out), "of", len(t), "sha256", h)
