# Replicating a gate (for gate G16)

Gate G16 is met when someone other than the authors reruns a registered test and gets results inside our intervals. Per-item review files (sheets, keys, verdicts) are not released, because they quote benchmark items; a replication therefore runs the test again on questions we never used, with the released code. The lightest test to rerun is gate G14 (the quote check placed after any model); this guide describes it. Expected effort: one evening on a 24 GB GPU plus a few hours of reviewing.

## What you need
- A GPU with at least 24 GB, Python 3.11 or newer with torch, scipy, requests, pyarrow, and Ollama.
- The Wikipedia snapshot: HuggingFaceFW/finewiki, data/enwiki (August 2025 dumps). vkg/localwiki.py reads the parquet files from data/wiki/finewiki_en/ and builds data/wiki/enwiki_fw2025.sqlite on first use; results/runs/l3/titles.db is the title index (built by results/runs/l3 scripts).
- The judge: we used a 27B Qwen model (Qwen3.8-27B, Q5_K_M GGUF) in Ollama under the name qwen3.8-27b, called with temperature 0 and thinking off. Use the same model if you can; if you use another, say so, because the result then tests the rule with a different judge.
- One drafting model of your choice through Ollama (we used llama3.1:8b, gemma3:12b, mistral-nemo:12b).
- PopQA (akariasai/PopQA, test.tsv) and Mintaka (only if you also rerun other gates) under data/external/.
- Paths: the scripts in tool/ find the repository root themselves. The run scripts under results/runs/ are the records of what we ran and are released unchanged (some are covered by registered hashes), so several still name our folders (F:/Projects/AI hallucinations, a separate free-search-mcp environment): replace the `cd` line or the ROOT constant with your clone's path before running one.

## Steps
1. Draw fresh questions. Copy results/runs/s65/seal65.py and change the slice to part[1767:2100] (positions no test used; S65 used 1000 to 1667, the stress-test inputs 1667 to 1767). Run it; it prints only a count and a hash. Do not open the items file.
2. Write down, before running anything, your predictions in the form of docs/S65_G14_OTHER_MODELS_PLAN.md (coverage, misleading share, errors).
3. Run results/runs/s65/g14.py with MODELS set to your model: draft, cands, judge, decide, sheet (the order in results/runs/s65/run_g14.sh).
4. Review blind. Give the quote sheets to two reviewers who see only question, answer, page title and quote, with the instructions used here: states / incomplete / not (the instructions are at the end of this guide). Give the truth sheet to two other reviewers who must look up every row and give a source.
5. Run `g14.py unblind` and compare with docs/S65_G14_OTHER_MODELS_PLAN.md: misleading quotes among releases (ours 0.3 to 1.0%, upper bounds 1.8 to 2.9%), errors after the truth check (ours 0 per model, upper bound 0.18% of questions), coverage (ours 15 to 16.5%).

## What counts
The replication agrees when your misleading share and your error share are inside our 97.5% upper bounds and your decoys are caught (at least 9 of 10 quote decoys, all truth decoys). Send back your plan file with its date, the counts table and your reviewers' agreement; we add it to the tracker with your name if you wish. A replication that does not agree is reported the same way.

## Other gates
Every gate has its plan and result in docs/ (S57 to S66) and its scripts in results/runs/. Gates on sealed sets need new sealed questions; the sealing scripts (results/runs/s58/seal58.py, s65/seal65.py) show how to draw them without reading them.

## Reviewer instructions (as used)
Quote reviewers (see only question, answer, page title, quote; no web, no own knowledge): for each row one verdict. states: the quote itself says that this answer is the answer to this exact question (right subject, relation, time or qualifier). incomplete: right subject and relation and agrees with the answer, but some part of the question is not in the quote. not: another subject, relation or time, does not say it, or says something different. Misleading = both reviewers 'not'.
Truth reviewers (see question, answer, subject page): look up every row (Wikipedia or another reliable source), give the source URL, verdict right / wrong / cannot tell; accept correct answers phrased differently and one of several correct answers. A release counts as an error unless both say right.
