# New sealed real-question set: design (2026-11-09; nothing generated yet)

Purpose. A second real benchmark for L2, power for L1, a test of the error-budget predictions (docs/GENERALITY_STEP1.md P1 to P3), and a time-anchored test bed for questions whose old gold is stale
(Mintaka). It must have current, checked gold, a unique answer per question, and no namesake ambiguity by construction.

## Construction (Wikidata SPARQL route; feasibility checked: the public endpoint returns JSON through the fetch tool)
- Subjects: Wikidata items with an English Wikipedia sitelink whose English title core is unique in our title index (results/runs/l3/titles.db, ncore count 1), so the question names exactly one page.
- Relations (single-valued, stable or closed in time; multi-valued relations such as occupation are excluded, the PopQA lesson): birth place and birth year, death year, founding year, headquarters or capital,
  author or director of a work, award year, holder of an office in a stated year (closed interval), population in a stated census year. Every question carries its time anchor where the value depends on time.
- Questions are written from per-relation templates plus a small set of paraphrases; present-tense volatile questions ("current president") are excluded.
- Gold: the Wikidata statement as of the query date (date recorded), with its qualifiers; for time-bound items the interval must be closed and cover the anchor.
- Popularity: sitelink count in three strata, 1/3 each (the system's coverage fell for popular entities on PopQA, so the strata are balanced).
- Size: 4,000 sealed items (L2 needs about 1,500 for k <= 6; L1 at a 50% reduction needs about 50 baseline plus system errors together, which at the observed error levels takes roughly 4,000 to 6,000 questions).
  A separate pilot of 150 items from a different seed is adjudicated first and is not part of the sealed set (it tests P3).
- Sealing: item identifiers, question and gold files hashed before any run; files not opened; each run once.

## Evaluation (written before any run)
- Systems: the frozen S19 system (system of record); the Learn-then-Test agreement baseline calibrated on the SimpleQA design pool; the agreement-ranked baseline at matched coverage.
- Primary endpoint: SER over all questions with errors after the blind adjudication rule fixed in docs/S22_DEV_FINDINGS.md (two adjudicators, decoy validity >= 95%, removal only when both agree with a verbatim quote),
  corrected for grader false credit as before; L2 met if the corrected 97.5% upper bound is below 1% at coverage >= 35%. Secondary: gold-relative SER; the same quantities per released answer; L1 at matched coverage with an exact binomial test.
- Predictions with prior probabilities written before the run: coverage between 0.25 and 0.45; system-judged-wrong at most 0.91% of releases; gold-class errors below 2% of releases given unique subjects and current gold.
- This is a transfer test: the system is not recalibrated.

## Costs and blockers
- Web evidence for 4,000 new questions: the keyless DuckDuckGo route allows one search per ten seconds (about 11 hours); the Serper route needs account credits (balance not checked here).
- Adjudication: about 150 pilot rows plus all system and baseline errors plus decoys, with the existing agent protocol.
- Downloading the Wikidata query results is read-only; no bulk dump is needed.
Open decision for the authors: the credit budget for web search, and whether the pilot adjudication should include a human subset.

## Build record (2026-11-09; counts only, items not opened)
Built by results/runs/s29/wd_build.py from the public QLever Wikidata endpoint (randomised queries, English labels, sitelink counts); subject names must have exactly one page in the local Wikipedia title index. Hashes in results/runs/s29/seal_hashes.txt.
- Sealed: 3,959 questions: birth place 800, birth year 600, death year 400, founded 600, author 500 (literary works, "Who wrote X?"), director 600, head of government in a stated year 400, capital 59 (the pool after the uniqueness filter was small).
  Popularity strata (sitelinks): low 1,820, mid 1,238, high 901, not the planned thirds because the high stratum pools are smaller.
- Pilot: 144 questions, disjoint, different seed; to be adjudicated before the sealed run.
- First build had no author items (the class "novel" has no item with 10 or more sitelinks and an author statement); the author relation was switched to literary works and the set rebuilt before any run. No sealed item was read.

## Web source for the sealed run (decided 2026-11-09)
The web evidence comes from the free-search-mcp keyless pool (DuckDuckGo, Bing, Yahoo! Japan, AnySearch merged by reciprocal rank fusion; results cached as URL lists in a separate cache directory), not from DuckDuckGo alone. Reason given by the user: Wikipedia need not be correct or current. Consequences written down now:
- the system under test is the frozen S19 pipeline with one declared change (the search pool); the earlier SimpleQA certificate was obtained with DuckDuckGo and is not claimed for this configuration;
- the verification gate still accepts spans only from the pinned Wikipedia snapshot (August 2025); the web pages enter the support vote, not the certificate; a gate that also accepts hash-pinned web pages is a separate variant to be designed on the pilot and DEV data first;
- the pilot (144 questions) is run once with each search pool.

## Pilot, first pass (free-search-mcp pool, frozen pipeline; 144 questions; 2026-11-09; pilot items may be read, sealed items may not)
Released 79 (coverage 0.549), gold-relative wrong 4 (SER 2.8% of 144, selective 5.1%). By relation (n / released / wrong): death year 15/6/0, founded 22/16/3, author 18/11/0, director 22/14/0, birth place 30/14/1, birth year 22/16/0, head of government 15/2/0.
The four wrong releases (not blind): Jordan Bos birth place (gold "Point Cook", answer "Melbourne, Victoria, Australia": a coarser place), and three founding years of companies (4F 2007 against 2003, Sigma-Aldrich 1976 against 1975, Herrenknecht 1977 against 1975), where the Wikipedia article and the Wikidata inception differ
(merger year, registration year). The "founded" relation for businesses has a gold problem of the kind found in Mintaka and PopQA. This is a design finding from the pilot; the sealed set is unopened and unrun, so the relation can still be changed before the run; the decision waits for the adjudicated pilot.
Coverage on this set is higher than on SimpleQA (0.55 against 0.37), which the earlier prediction (0.25 to 0.45) did not allow. Revised before the sealed run, because of the pilot: coverage between 0.40 and 0.65 (prior 0.7); other predictions unchanged.

## Pilot, second pass (DuckDuckGo pool, same frozen pipeline; 2026-11-09)
Released 76 of 144 (coverage 0.528), 2 wrong against gold (4F, Sigma-Aldrich). The 76 releases are a subset of the 79 from the free-search-mcp pass and carry identical answer text in all 76 cases; the three that the DuckDuckGo pool did not release are Jordan Bos (birth place), Herrenknecht (founded) and one correct release. The two pools therefore differ in coverage by 3 questions and not in what is said when something is released: the release decision is dominated by the Wikipedia-gated step, not by which search engine supplied the web pages.
Blind adjudication of the 79 releases' errors, with 24 gold-matching releases and 12 injected-false decoys (40 rows, two independent agents, key withheld) is running; the sheet builder is results/runs/s29/adj_build.py.

## Pilot adjudication and the decision on "founded" (2026-11-09; before any sealed run)
Two independent agents, key withheld, 40 rows: 4 gold-relative wrong releases (union of both pools), 24 gold-matching releases, 12 injected-false decoys (results/runs/s29/adj/S29_pilot_adjudication.md).
- Decoys: 12 of 12 flagged as wrong by at least one agent, 11 of 12 by both. Gold-matching releases: 24 of 24 accepted by both agents. The agents separate correct from false answers on this set.
- The 4 wrong releases: both agents judged all 4 acceptable (Sigma-Aldrich: gold wrong, the 1975 merger year is right; Herrenknecht 1975 vs 1977 and 4F 2003 vs 2007: founding versus incorporation or renaming; Jordan Bos: the answer names the containing city of the gold suburb). So the pilot has 0 adjudicated system errors in 79 releases, and the whole gold-relative error rate comes from gold ambiguity, three of four in one relation.
- Caveats: the agents saw gold, several quotes came from page summaries and were not checked as verbatim; the removal rule of the earlier protocol (both agents plus a verbatim quote) was not applied here; a strict reading would keep Jordan Bos as an error (coarser than the gold). n = 4 errors is too few to estimate an error rate.
- Decision: the "founded" relation (600 sealed items) is dropped from the sealed run. Reason: 3 of 15 to 16 pilot releases in this relation had an ambiguous gold, a rate that would put hundreds of adjudication rows on the budget and weaken the gold-relative metric. Not a post-hoc exclusion of errors: the sealed items of this relation were never opened or run. Sealed set now 3,359 items (hash of the sorted ids in seal_hashes.txt); the original hash of the full file stays. The relation is reported as dropped, with this reason, in the paper.

### Pre-registration of the sealed run (fixed before running; frozen pipeline S19 with the free-search-mcp pool)
1. Primary endpoint: adjudicated system errors k_adj among releases, with the earlier protocol (two blind agents with decoys, removal needs both agents plus a verbatim quote that is checked against the page text). Report the corrected Clopper-Pearson upper bound for k_adj over all 3,359 questions; L2 on this set holds if it is below 1% at coverage of at least 35%.
2. Secondary: gold-relative errors by relation; coverage by relation and by popularity stratum.
3. Predictions: coverage 0.40 to 0.65; gold-relative wrong at most 1.5% of releases; system-judged-wrong at most 0.91% of releases (pooled earlier estimate). If any prediction fails it is reported as failed.
4. Baseline: the LTT agreement-score rule (threshold calibrated on the 2,500 SimpleQA design items, unchanged) at matched coverage, to repeat the L1 comparison.

### Pilot observation on the baseline (pilot only; written before the sealed run)
Dry run of results/runs/s29/s29_final.py on the free-search-mcp pilot (144 questions, includes "founded"): the agreement-score baseline at t = 6 releases 80 with 4 gold-relative wrong, against 79 and 4 for the frozen system. On this question set the two rules are nearly the same, so an L1 gain over the baseline is not expected; the sealed run is mainly a test of L2 (error bound at coverage). Prediction added before the run: the system and the baseline at matched coverage differ by fewer than 3 wrong releases on the sealed set.
The sealed run is chained to start after the prefetch (results/runs/s29/chain_sealed.sh); it waits for free RAM and VRAM and for the lock.

### Execution detail (2026-11-09, before the sealed run)
To use the GPU while the search prefetch is still running, the 3,359 sealed items are processed as four consecutive slices of 840 (file order; chain_chunks.sh), each started when its search results are cached, and the outputs are concatenated (s29_combine.py) before scoring. Items are processed independently with fixed seeds and the same code, so slicing does not change any item's result; the per-slice runs use identical settings. Nothing about the pre-registered rules changes.

### L1 on the sealed set (added 2026-11-09, before any sealed result; see docs/CRITERIA_REVISION_L1.md)
5. Revised L1: L1-a (system SER lower than the raw model closed book, the raw model with an abstention prompt, standard RAG and RAG with an abstention prompt; McNemar, Holm) and L1-b (non-inferiority to the agreement-score ablation at matched coverage: SER difference upper bound below +0.25 points, yield difference lower bound above -1 point, truth-relative errors from a blind review). Closed-book generations for B0/B1 are made once after the main run with the prompts fixed in the revision document.
6. The original L1 test (50% lower than the ablation, discordant binomial) is run as well; prediction: not met.

### Secondary confirmatory test: the two-source cell (added 2026-11-09, after S38 and before any sealed result is seen)
7. Rule V2 = frozen release rule, plus release of a candidate with support 2 of 3 when Phi-4 agrees, the deductive gate passes, and both Wikipedia readers abstained (S31 cell; S38: 0 truth-relative errors in 55 on design data). Computed from the sealed outputs, no new generation.
8. Measures: coverage gain over the frozen system; truth-relative errors among the added releases by the S36-style blind review (two reviewers, decoys, gold hidden). Pass: added error rate at most 3% and one-sided 90% upper bound at most 6% with at least 40 added; and V2's overall truth-relative SER upper bound below 1%.
9. L1 at the higher coverage: V2 against the agreement-score baseline at exactly V2's coverage (edge interpolation), truth-relative errors from the same review; original criterion (at least 50% fewer, discordant binomial p < 0.05) and the revised L1-b, both reported. Prediction: coverage gain 2 to 6 points; the original L1 is still not met at this coverage.
