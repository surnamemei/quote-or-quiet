# L3 summary: what is guaranteed, what is assumed, what is not (2026-11-09)

Merges docs/L3_QUALIFIED_DESIGN.md (entity slot, Qualified state, judge, Goal B step 1, v5) and docs/L3_CERTIFICATES.md
(derived numbers, written by the S22 session). All numbers are on the frozen S19 H1 releases; DEV sets were used for design, the
FRESH-5 / S21 test sets are already unsealed, so everything on them is **post hoc**. Nothing here is a confirmatory result: S22 was
not run and no Qualified endpoint was pre-registered.

## 1. The claim, by layer
| layer | what holds | how |
|---|---|---|
| span | the answer A is a verbatim span of a hash-pinned page P that passes V1-V5 | checked by code (first half of L3) |
| entity slot | the question's subject mention has one reading in the sense inventory (Verified), or the output states the reading E and A occurs on E's page or P = E (Qualified) | checked by code against the local FineWiki title index (6.6 M titles) |
| derived number (formal extension, not in the system) | the number is the output of a whitelisted program (age_at, years_between, diff, sum) on verbatim quotes from pinned pages; values parsed by code, the LLM only supplies quotes and the op name | checked by code |
| **assumed, not proven** | the source is true; the span answers the asked relation; the time frame matches the snapshot (a present-tense question cannot be Derived without a stated reference date); every reading of the mention has a page in the snapshot | stated |
| **heuristic hole** | mention extraction: when no subject mention is found the output is Verified by default | reported as such |

## 2. Output states
- **Verified** "A": one sense of the mention, or the question names the qualifier, or P's title is a shortened form of a fuller name in
  the question.
- **Qualified** "A, assuming m = E": several senses; E is the release page if it is a sense, the sense of the type the relation implies,
  the primary topic if it holds A, the only sense holding A, or (v5) the sense whose qualifier word occurs in the question (R1) or the
  primary topic when the answer is the release page's own subject and that page names the mention (R2).
- **Unresolved**: the mention is ambiguous and no single sense can be named (strict).
- **Derived** (formal label only): the answer is the output of a whitelisted program on verbatim quotes. Not part of the evaluated
  system and not part of any claim: on Mintaka 12 certificates were issued, 8 wrong against gold (6 stale present-tense ages, 2
  relation misreads); 12 certificates came from 224 numerical-answer candidates and only 1 of the 4 correct ones was not already
  released. At most 1.4% of items (27 of 2000 Mintaka) could gain an answer from derivation.

## 3. Accounting (fixed rule)
Completion = graded-correct Verified + Qualified. Silent error = Verified wrong + Qualified wrong against gold (no conditional-truth
discount, because no judge was validated). A correct Qualified answer with a wrong stated sense is a qualifier error, reported
separately. If more than half of releases are Qualified, L2 is also reported on Verified alone.

## 4. Numbers
DEV, strict v4 (design data): Verified wrong 3 / 1 / 1 / 2 and Qualified wrong 3 / 1 / 0 / 0 on PopQA / Mintaka / SimpleQA / fresh; no entity
error remains in Verified. v5 recovers 4 of the 8 correct answers v4 left Unresolved (in-sample).
Used test sets, v5, post hoc (conservative silent errors = Verified wrong + Qualified wrong):
| set | Verified (wrong) | Qualified (wrong) | silent errors | correct answers lost to Unresolved |
|---|---|---|---|---|
| FRESH-5 | 507 (4) | 42 (0) | 4 | 19 |
| Mintaka test | 344 (17) | 221 (7) | 24 | 51 |
| PopQA test | 310 (8) | 83 (6) | 14 | 5 |
(Verified counts include graded-wrong ones; Mintaka errors include stale or ambiguous gold. S22's blind adjudication, on the frozen
S19 releases, removed 19 of the 28 frozen Mintaka errors under the strict two-adjudicator rule and kept 9 (3 answer wrong, 2 ambiguous,
4 cannot tell; corrected upper bound 0.92% at coverage 0.310; docs/S22_DEV_FINDINGS.md). Those 9 were not re-run through the entity
layer here. The 28 here and the 24 in the table are counted by different graders and error definitions and have not been reconciled.)
A dry run on the S22 *combination* system's Mintaka releases (S19 plus pinned-page releases, 1005 releases, not the frozen system) kept 29
of 63 errors under the same rule; 17 of those 29 stayed Verified, because they are time, rank or scope ambiguity rather than same-name
entity ambiguity. That figure is about the combination system and is not comparable to the table above.
It targets one mechanism (silent entity resolution), and all 8 PopQA
S21 entity errors leave Verified.

## 5. What did not work (DEV, recorded)
- Conditional-truth judge (qwen3.8-27b), v1 yes/no and v2 extraction: both fail the pre-set bar on hand-false items (v2 held-out 3 of 9
  supported). An excerpt judge cannot tell "the answer appears on E's page" from "the answer is true of E".
- The 4B stating its own entity (Goal B step 1): free text 18/59 right, often writing the answer as the entity; closed choice among
  candidate senses 12/20 vs rule 10/20, but it catches no error and would downgrade 4 correct answers. The rule-based slot stays.
- Derivation certificates: sound by construction, practically negligible.

## 6. Cost and the next design step
True multi-sense ambiguity costs about 9% of the correct answers on Mintaka (51 to 87 depending on version and set) and 3.6% on SimpleQA
DEV. More rules would only add guesses. Proposed instead: for a mention whose senses cannot be told apart from the question, release a
**candidate list** ("A under E1, B under E2") rather than withholding. This keeps the guarantee (each line is Qualified) and needs a
confirmatory test to count as a result; none exists yet.

## 7. What may be said
Within the scope of mention extraction and the sense inventory: every Verified or Qualified output is a verbatim span of a pinned,
checked page, and the entity it is about is either unique or explicitly stated. Residual errors are in the assumed row (source truth,
relation, time) and in mention extraction. Not claimed: that Qualified answers are true for their stated sense, that the layer
lowers the conservative silent-error rate, or any bound at the L2 level.
