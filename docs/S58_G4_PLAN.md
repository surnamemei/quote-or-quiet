# S58: gate G4, natural questions at usable coverage (plan, 2026-11-11, before any S58 run output)

Gate G4 (docs/PROGRESS_TRACKER.md): released answer wrong; threshold: 97.5% upper bound below 1% of all questions at coverage at least 35%; at least 1,000 sealed questions; registered, unseen, valid decoys.

## Why a new rule
The frozen system answered 31.0% of Mintaka questions (Section 5.2); the three-source agreement it requires is the main loss. Design work in S57 (results/runs/s57/g4; design data only: the 2,200 Mintaka questions of S21, whose sealed test is spent, and the 600 Mintaka design questions of S39) replaced agreement by the quote requirement that passed gate G3: an answer is released when a sentence of a Wikipedia page states it, as judged by the 27B with a swapped-answer control.
Design results (gold-relative, before adjudication): Q1c+T 37.7% coverage, 1.85% of questions wrong against the gold (S21 test) and 38.5%, 3.67% (S39); adding reader support of at least 2 (Q2): 35.8%, 1.35% and 36.3%, 2.83%. Reading the gold-wrong releases of Q2 by hand, most are stale or wrong gold or equally acceptable answers; about 3 to 5 of 27 (S21) and 2 of 17 (S39) looked like real errors. Two other rules were tried and rejected: a title-qualifier rule E (cost 8% of coverage for 8 errors) and a 27B page-subject check P (dropped 72 releases with 5 wrong).

## Rule Q2 (frozen now)
1. The frozen S19 pipeline runs unchanged up to the six reader answers (web, wiki and combined passages, plain and cautious prompts; free-search-mcp pool as in S39 and S40, 10 to 12 s between queries).
2. Candidates: the distinct reader answers (agreement as in the frozen system), with their support (number of readers that agree), most supported first.
3. Pages: the five pages of the local retriever plus the English Wikipedia pages named in the web results that are in the snapshot.
4. Spans: gate-accepted typed verbatim spans of the candidate (l3_verify.verify and l3_checks2.extra), quote = the sentence window, kept when it is a sentence of at least 40 characters and holds the question's numbers and ordinals; up to 6 per candidate.
5. Witness: the first span for which Qwen3.8-27B (chat, thinking off, temperature 0) answers YES to the rule R prompt for the candidate and NO for a swapped answer of the same shape (seed 5801).
6. Release when exactly one candidate has a witness (conflict: two different candidates with witnesses, withhold), its support is at least 2, and the question is not time-sensitive: the S22 rule (results/runs/s22/temporal.py) or, added from the S39 design check, the pattern 'this|last|next year|season|month|week', 'recent', 'recently', 'upcoming'.
Code: results/runs/s57/g4/g4_design.py (cands, judge) and results/runs/s58/s58_q2.py (decision), with the set pointed at the S58 outputs.

## Test
1,200 Mintaka 'generic' questions never used: positions 2800 to 4000 of the S21 seeded shuffle (S21 used 0 to 2200, S39 2200 to 2800), sealed on 2026-11-11 (results/runs/s58/seal58.py; sha256 455cebcf...; counts only printed). Run once.
Grading: alias-aware 27B judge with the grader 6.1 veto (as S21). Adjudication of every gold-wrong release as in S40 L2: two blind reviewers with the gold shown, the system's answer and its quote; a removing verdict (gold wrong or stale, or answer equally acceptable) needs a quote from a page that the reviewer gives and that is found mechanically in that page; 12 decoys (a wrong answer from another question) and 24 gold-matching releases mixed in; valid when at least 11 of 12 decoys are kept as wrong and at most 2 of 24 correct releases are called wrong by both. An error remains unless both reviewers remove it.
Primary: adjudicated errors e among the 1,200 questions; G4 T met when coverage >= 35% and the 97.5% upper bound of e/1200 is below 1% (e at most 5). N met (1,200). V met when the adjudication is valid.
Predictions: coverage 33 to 40% (so a real chance of missing 35%); gold-wrong releases 1.2 to 3.5% of questions; adjudicated errors 2 to 6; probability of passing about one half. Secondary, reported: the frozen rule's coverage on the same questions (expected 28 to 34%), and the share of Q2 releases whose quote states the answer is not reviewed here (G3 covers it).
A failure is reported as failed; the rule is not changed on these data.

Note (2026-11-11 16:5x): the first run stopped with a CUDA out-of-memory error at the reader stage (other processes held about 21 GB at that moment); the evidence stages (web, wiki, combo) had finished and are kept. The run is resumed with the 4B server capped at 45% of the card instead of 68% (generation is greedy, so only batch size changes, as in the tool). No other change.

Note (2026-11-11 18:1x): the resumed run also stopped (out of memory inside the 45% cap: one batch of long web passages needs more). The cap goes back to 68% as registered and in S40; the reader stage now waits for at least 24 GB of free memory before each of up to five attempts (cached stages are kept). No change to any rule.
