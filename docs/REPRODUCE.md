# Reproducing the results (2026-11-09)
Commands below are the ones the project's own launchers and scripts use; they have not been run again from a clean checkout. The repository has no requirements file and no licence file yet (see docs/AVAILABILITY_DRAFT.md).

## Environment used
Windows 11, one RTX 5090 (32 GB), 62 GB RAM. Ollama on 127.0.0.1:11535 serving phi4 and qwen3.8-27b (project model store under models/ollama_store). The 4B reader runs in vkg/podgen_server.py
(Qwen3-4B-Instruct-2507 and Qwen3-Embedding-0.6B from models/) on 127.0.0.1:18000. Python 3.13 with torch, scipy, psutil, requests. GPU jobs follow the lock protocol in results/gpu_lock.txt (write, wait, re-check).

## Check the frozen files
`sha256sum -c results/runs/s24/hashes_freeze.txt` (harness, generators, gate code, launchers, sealed closed-evidence sets).

## Closed-evidence benchmark (Tables 4 and 5)
1. Generate a set: `python -B results/runs/s24/gen_closed.py closed_test 202 1500` (seed 202; closed_test2 uses seed 303; closed_dev uses 101 and 200 items). Writes items.jsonl, docs.jsonl and hashes.json.
2. Run configuration A once: `bash results/runs/s24/run_closed_test.sh` (waits for the GPU lock, starts the 4B server, runs `closed_run.py gen closed_test`).
3. Score: `OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s24/closed_run.py score closed_test` (writes results/runs/s24/closed_test_score.md).
4. Configuration B: `bash results/runs/s24/run_closed_alt.sh closed_test2`, then `OLLAMA_HOST_URL=http://127.0.0.1:9 python -B results/runs/s24/closed_run_alt.py score closed_test2`.
Results: docs/S24_CLOSED_TEST_RESULT.md and docs/S24_CONFIG_B_RESULT.md.

## SimpleQA, Mintaka, PopQA (Tables 1 to 3, Figures 2 and 3)
The frozen S19 system and its sealed runs are specified in docs/S19_PROTOCOL.md, docs/S21_PROTOCOL.md and docs/FREEZE.md; outputs and scores are in results/runs/s19, s21 and the S19 and S21 result files. Strict adjudication:
results/runs/s22 (adj_unblind.py, adj_combine.py, quote_check.py; sheets, verdicts and keys). Pinned-page and format-gate variants: results/runs/s22 (s22_run.py, combo_s21test.py, combo_fresh5.md). Independent retrieval: results/runs/s23.
Stronger veto: results/runs/s25. Learn-then-Test baseline: results/runs/s23/conformal_base.py. Error budget: docs/GENERALITY_STEP1.md. Derivation certificates: results/runs/l3cert and docs/L3_CERTIFICATES.md.
Re-running the web-evidence stages needs live DuckDuckGo results, which change over time; the stored evidence files in results/runs/s19 and s21 are what the reported numbers were computed from.

## Figures
`python -I -B paper/figures/make_figures.py` (values are typed into the script from Tables 1 to 3).

## Not included
Third-party web page text beyond what the run records hold; model weights (download from the model cards); the full FineWiki dump (download from Hugging Face HuggingFaceFW/finewiki).
