# S22 adjudication by web verification (DRAFT, not frozen)

Why: on Mintaka about 4% of system releases carry stale, wrong or ambiguous gold (docs/S22_DEV_FINDINGS.md), more than the whole
L2 allowance. Gold-relative L2 is therefore out of reach on any benchmark older than the evidence snapshot. The protocols always
had blind adjudication as the primary endpoint; human adjudication was never carried out. The user proposed (2026-11-08) that
verification be done online by Claude instead, which is faster and leaves a cited source for each verdict.

## Blindness
- The sheet is built exactly as in S19/S21: every graded-wrong system release plus equal numbers of decoys of two kinds
  (graded-wrong baseline answers on unreleased items; graded-correct system releases), shuffled with a fixed seed. It shows only
  row, question, gold, answer. The key stays in a separate file.
- The adjudicator is a fresh Claude agent instance that receives only the sheet and this rubric: no project files, no key, no
  system outputs, no knowledge of which rows are the system's. The session that built the system does not adjudicate.

## Rubric (one verdict per row, each with a source URL and a one-line quote)
- **answer wrong**: a reliable source contradicts the answer, and the gold is right.
- **gold wrong**: a reliable source shows the answer is right and the gold is not. Includes **stale gold**: the question has no
  time anchor, the gold was true when the dataset was written, and the answer is true as of August 2025 (the evidence snapshot).
- **both acceptable**: the question admits both (two defensible readings, both answers sourced).
- **ambiguous question**: the question names something that can be read as different entities or events and the answer fits a
  different reading than the gold; kept as an error (as in S21).
- **cannot tell**: no reliable source found within the search budget. Kept as an error.
Only "gold wrong" and "both acceptable" remove an error.
Sources: Wikipedia, official league/organisation/government sites, major reference works and news outlets. Not allowed:
the benchmark's own pages or mirrors (Mintaka, PopQA, Hugging Face dataset viewers), Q&A sites, or the system's evidence logs.

## Validity check on the adjudicator (decided before unsealing)
- decoy_baseline_wrong rows are graded-wrong baseline answers. If the adjudicator removes the error ("gold wrong" or "both
  acceptable") on a clearly larger share of them than the design pilot suggests (threshold to be fixed from the pilot, e.g. more
  than 40%), adjudication counts as too lenient and the primary endpoint falls back to gold-relative k.
- decoy_system_correct rows: the share judged "answer wrong" estimates hidden grader false credit; reported, and if it exceeds
  the f_up correction (0.82%) by more than its CI, the correction is replaced by the observed rate.

## Pilot (descriptive, decides nothing about S21)
Run the same blind procedure on the existing S21 Mintaka sheet (84 rows: 28 system errors, 28 + 28 decoys). S21's verdict is
already final (the protocol named the user as adjudicator and the sheet stays blank); the pilot only calibrates the adjudicator:
decoy rates, verdict distribution, time per row, source quality. Its numbers fix the validity threshold above.

## Pilot result (2026-11-08, results/runs/s22/adj_pilot.md; descriptive)
Fresh general-purpose agent, sheet only, 84 rows in about 3.3 minutes.
| kind | n | removed (gold wrong + both acceptable) | answer wrong | ambiguous |
|---|---|---|---|---|
| system errors | 28 | 24 (17 + 7) | 3 | 1 |
| baseline-wrong decoys | 28 | 12 (6 + 6) | 15 | 1 |
| system-correct decoys | 28 | 28 "both acceptable" | 0 | 0 |
- Adjudicated k on S21 Mintaka would be 4 (k ≤ 10 needed), so precision would pass and coverage (0.310) alone fails. Agrees
  closely with this session's unblinded reading (14 stale + 3 wrong gold + 9 both acceptable).
- The 12 removed baseline decoys look genuine on reading (stale gold: Ecuador leader, Eagles coach, Michael Caine's age; ceremony
  vs film year: 1947 Best Actress, 2011 Best Actor, BCS 2008). So on Mintaka the baseline-wrong decoys measure gold quality as
  much as adjudicator leniency; they cannot serve as the validity check on their own.
- **Process defects:** only 17 searches and 1 fetch for 84 rows; most quotes are paraphrases from the agent's own knowledge, not
  text it read; it also used knowledge after the August 2025 reference date in places. That is knowledge-based adjudication, not
  web verification.

## Changes for the frozen version
1. **Injected-false decoys** (ground truth known): for a fixed number of rows, the answer is replaced by a plausible wrong answer
   of the same type taken from another item's gold (same answer type, different value), checked by the session not to be an alias.
   Validity: the adjudicator must call at least 95% of them "answer wrong"; otherwise adjudication is void and the endpoint falls
   back to gold-relative k.
2. **Mechanical source check:** every removed error must carry a URL and a quote of at most 25 words; a script fetches the URL
   and requires the quote to appear in the page text (normalised whitespace and case). A verdict whose quote is not found reverts
   to "cannot tell" (error kept).
3. At least one fetch per row that removes an error; the agent is told that unverifiable quotes revert.
4. Reference date stays August 2025 for unanchored questions; ceremony year vs award year counts as "both acceptable".
