# S21 protocol: transfer test of the frozen S19 system on new sealed sets (H1-M single primary; tiered answering descriptive)

**Status: FROZEN 2026-11-08 07:08 (AEST).** Hash list: results/runs/s21/hashes_freeze.txt. Nothing has been run on the test sets. DEV findings that motivate this design: docs/S21_DEV_FINDINGS.md.

## Why this test
S19 passed L2 on FRESH-5 (SimpleQA originals). SimpleQA questions were written to be unambiguous and Wikipedia-grounded. S21 asks
whether the frozen system transfers to question sets built differently: Mintaka (human-written, natural wording; "generic"
single-hop questions only) and PopQA (templated from Wikidata, long-tail subjects). DEV says it largely does not (PopQA coverage
0.197; Mintaka coverage 0.355 with a raw error rate of about 1%). S21 is therefore a pre-registered **transfer test**: the
predictions below expect H1-M to fail, and the result defines the scope of the S19 claim either way.

## Common part
- **Test sets** (results/runs/s21/seal.py, sealed 2026-11-07, not inspected; raw downloads data/external, SHA256SUMS.txt):
  - mintaka_test: 2,000 Mintaka "generic" items (train+dev+test pools, seed 21, after the 200 DEV items);
    results/runs/s21/mintaka_test.json, SHA-256 in seal_hashes.txt (b4d9fa7f...).
  - popqa_test: 2,100 PopQA items, 700 per subject-popularity tercile (seed 21, after DEV); popqa_test.json (93805990...).
  One run only.
- **Evidence:** exactly as S19 (vkg/s17_run.py with VKG_WEB=ddg): DuckDuckGo web (question-only query, up to 8 results/pages,
  contamination guard), local FineWiki Aug 2025 top-5 titles, combo passage. DuckDuckGo spacing 5 s (amendment of 2026-11-07,
  results/runs/s21/NOTES.md). Raw search results were prefetched without any model or gold (prefetch_s21.py; 0 errors on both
  test sets; mean pages per item 7.9 Mintaka, 6.9 PopQA). The S19 rule for failing searches applies unchanged.
- **Models:** as S19 (Qwen3-4B, embedder, Phi-4 ac896e5b8b34, judge qwen3.8-27b e0a7cdbef002), on the user's RTX 5090.
- **Grading (amendment, applies to every system and baseline):** alias-aware grader 6.1, vkg/s21_judge.g6a: an answer is correct
  if grader 6.1 (prompt, model and veto unchanged) labels it CORRECT against at least one usable gold alias (gold[0] first, then
  up to 8 more; aliases with fewer than 2 letters or digits dropped). For single-gold items this equals S19's g6. Labels are made
  by run_test.sh before any scoring; scorers run with the judge disabled.
- **One primary hypothesis, H1-M, at one-sided 2.5%.** A tiered L1-A co-primary (Kimi session) was proposed and withdrawn
  before the freeze after its DEV dry run failed criterion (a) (section pasted below); it is reported descriptively only.
  Everything on PopQA, and everything else on Mintaka, is secondary or descriptive.
- **Order of work:** (1) freeze. (2) results/runs/s21/run_test.sh: checks hashes, takes the GPU lock, generates (mintaka_test then
  popqa_test), judges, Phi-4, alias labels, unloads, releases the lock, re-checks hashes. (3) `python -B -m vkg.s21_eval score`
  (H1-M raw + blind sheet, PopQA descriptive), then Kimi's `tiered_s21.py --test` (descriptive). (4) Blind adjudication (below). (5)
  `python -B -m vkg.s21_eval final`. (6) results/runs/s21/S21_RESULT.md, failures included.

## H1-M: L2 on Mintaka (this session)
- **System:** the frozen S19 H1 system, unchanged (docs/S19_PROTOCOL.md, H1): max-support 4B candidate, L3 gate V1-V5
  (vkg.l3_checks2.release2), support 3, Phi-4 cautious veto.
- **Rule:** k = graded-wrong releases (alias-aware); E = ceil(k / (1 - 0.0082)); pass iff the Clopper-Pearson one-sided **97.5%**
  upper bound of E / 2000 is below 1% **and** coverage is at least 35%. At n = 2000: **k ≤ 10**.
- **Primary endpoint: k after blind adjudication,** sheet as S19 (every graded-wrong release + equal numbers of two decoy kinds,
  seed 21, key kept apart). Rubric: gold wrong / answer wrong / both acceptable / **ambiguous question** / cannot tell. Only
  "gold wrong" and "both acceptable" remove an error; "ambiguous question" (new, reported as its own class) keeps it.
  Adjudicator: the user, without the key. If the sheet is not adjudicated, every row counts as "cannot tell" (primary = secondary),
  as in S19.
- **Secondary:** the same rule on gold-relative k.
- **Design evidence** (DEV, same code: `python -B -m vkg.s21_eval score --dev`): see the table in "Dry run" below.
- **Predictions (priors before unsealing):**
  | | prediction | prior |
  |---|---|---|
  | P1 | H1-M met (adjudicated k ≤ 10 and coverage ≥ 35%) | about 12% |
  | P2 | coverage ≥ 35% | about 50% |
  | P3 | gold-relative SER of the system ≤ 1.5% (k ≤ 30) | about 75% |
  | P4 | system SER at most half of combo_plain's SER, gold-relative (an L1-style descriptive check) | about 90% |
  | P5 | at least a third of adjudicated system errors are "ambiguous question" or "both acceptable" | about 60% |
  Reasoning: DEV coverage 0.355 is on the floor (binomial SD at n = 2000 about 1 point, DEV sampling SD about 3.4 points); DEV
  raw error 2/200 suggests k around 20 at n = 2000, roughly half removable by adjudication; k ≤ 10 needs about 0.5% after
  adjudication.

## PopQA (descriptive, this session)
- Same system and grading on popqa_test. Reported: coverage and SER overall and per popularity tercile; error classes (the same
  rubric, filled by this session after unsealing, labelled post hoc); combo_plain baseline.
- Predictions: coverage < 0.35 overall (prior about 95%); coverage in the low-popularity tercile below that of the high tercile
  (about 60%); among released errors, ambiguous-subject cases are the largest class (about 60%).
- A_S check (descriptive): for released correct and wrong answers, the share whose release page states the gold (Wikipedia page
  versus Wikidata gold).

## Tiered answering (the Kimi session; descriptive only, pasted verbatim below)
Source: E:\Models\halluc_runs\PREREG_S21_TIERED.md, SHA-256 02601c5e94ab81c175576b331560d11c555b15c700e664cf159d5455fb756e31;
scorer E:\Models\halluc_runs\tiered_s21.py (6acdcdb7f3eece29a21a91a9abbd02d8750369caa495081883a3ed4a3201bd93), importing the frozen
tiered.py (9cfb2d74...) and nor2.py (e84c2932...). The text between the two rules is the file, unchanged.

---

# S21 section: tiered answering on Mintaka / PopQA (descriptive only, no primary)

**Status: FINAL (2026-11-08).** The tiered L1-A co-primary proposed for S21 is **withdrawn before the freeze**. The DEV
dry run below shows that the rule does not transfer to Mintaka: criterion (a) fails clearly on design data. A primary
expected to fail would only take alpha from H1-M. H1-M therefore keeps the full one-sided 2.5%.

## What is reported on the test sets (descriptive, no hypothesis test)

- **Script:** `E:\Models\halluc_runs\tiered_s21.py --test`. It reuses the frozen `tiered.py` functions unchanged
  (`system`, `outcome`, `l1`). Only three things change:
  - the items are the S21 sets;
  - the Phi-4 reader files are the `s21*` ones;
  - grading uses `vkg.s21_judge.g6a`, for the system and all baselines alike.
- The 1.25% bounds in the script are kept as a fixed convention. They carry no hypothesis.
- **Output:** `TIERED_S21_TEST.md` with coverage, correct, SER, CP upper bound and tier counts for:
  - tiered;
  - tier 1 only (the L2 system);
  - `wiki_plain`;
  - `combo_plain`;
  - the 4B cautious combo answer.
- It also gives the L1-A criteria, labelled descriptive, on mintaka_test (n = 2000) and popqa_test (n = 2100).
- Run after the H1-M scoring. Nothing is tuned on test data.

## DEV dry run (`tiered_s21.py`, judge off, cached g6a labels)

| set | tiered cov / correct / SER | tier 1 alone | wiki_plain | tier counts (1 / 2 / abstain) |
|---|---|---|---|---|
| mintaka_dev (n=200) | 80.5 / 71.0 / 9.50 | 35.5 / 34.5 / 1.00 | 67.5 / 52.5 / 15.00 | 71 / 90 / 39 |
| popqa_dev (n=300) | 61.0 / 39.3 / 21.67 | 19.7 / 17.7 / 2.00 | 43.3 / 27.0 / 16.33 | 59 / 124 / 117 |

**L1-A against `wiki_plain`:**
- Mintaka: (a) +0.0200, upper +0.0675, **fail**; (b) +0.185, lower +0.105, pass; (c) +0.130, pass.
- PopQA: (a) +0.135, fail; (b) and (c) pass.

**Why it fails.** Tier 2 is the problem: the 4B and Phi-4 agreeing on a cautious combo answer.
- Mintaka: tier 2 released 90 answers, of which 17 were wrong (19%). On S19 FRESH it was about 4%.
- PopQA (long-tail entities): 59 of 124 tier-2 answers were wrong.
- Tier 1 stays at 1–2% SER on both sets.

Agreement between two readers is not enough evidence on comparative, count and long-tail questions. Redesigning this
belongs to later work on the answer ladder, on DEV only.

## Expected on test (stated before unsealing)

- **Mintaka:**
  - tiered: coverage about 0.78, SER about 0.08–0.12;
  - L1-A (descriptive) NOT MET on (a);
  - tier 1 alone: SER about 0.01–0.02 at coverage about 0.35.
- **PopQA:** tiered SER above `wiki_plain`'s, coverage about 0.6.

---

## Dry run on DEV (same code, results/runs/s21/S21_raw_dev.md)
`python -B -m vkg.s21_eval score --dev` and `final --dev` (blank sheet = all "cannot tell") ran end to end on 2026-11-08:
| set | n | released | coverage | wrong (alias-aware) | combo_plain answered / wrong |
|---|---|---|---|---|---|
| mintaka_dev | 200 | 71 | 0.355 | 2 | 184 / 31 |
| popqa_dev | 300 | 59 | 0.197 | 6 (7 with gold[0] only) | 240 / 96 |
Alias-aware grading turned 1 of 7 PopQA errors into correct (491 extra labels on DEV) and changed nothing on Mintaka DEV.

## Frozen files
results/runs/s21/hashes_freeze.txt: every vkg module, seal.py and the four item files, prefetch_s21.py, phi4_dev.py, run_test.sh,
this protocol, the embedder weights, Kimi's tiered.py, tiered_s21.py, nor2.py and section file.
