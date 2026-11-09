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
