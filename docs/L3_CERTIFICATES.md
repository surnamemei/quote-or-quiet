# Derivation certificates for computed answers (prototype, design data only; 2026-11-09)
Code: results/runs/l3cert/ (cert.py, run_cert.py, run_cert.sh; outputs cert_mintaka_{dev,test}.json, census_mintaka_test.json; v1/ = first
run with web-snippet evidence). Data: closed S21 Mintaka dev (21 candidates) and test (224 candidates): numerical-answer questions of
type compute ("how old / how long") or count ("how many").

## Mechanism
A certificate is (facts, op): each fact is a quote that must occur verbatim in a pinned local FineWiki page (l3_verify.locate); the
value is parsed from the quote by deterministic code (exactly one date/year/number per quote; the LLM supplies quotes and an
operation name, never values); the answer is the output of a whitelisted operation (age_at, years_between, diff, sum). Statement:
a certified number is the output of a fixed program on verbatim pinned spans. Not covered, as for spans: the quotes answer the
relation, the source is true, time. Phi-4 proposes the specification (cached, greedy); the checker rejects fabricated quotes.

## Census (mintaka_test, 269 numerical-answer questions)
Gold is not on the pinned page for 63 (compute 15, count 16, lookup 32). Stable compute/count items whose gold is absent: 27 (1.4% of
2000 items): the upper bound on what derivation could add on this benchmark.

## Result
| evidence given to Phi-4 | candidates | certified | correct | wrong | new (not already released) |
|---|---|---|---|---|---|
| web + wiki passage (v1) | 224 | 1 | 0 | 1 | 1 |
| local wiki passage only | 224 | 12 | 4 | 8 | 8 (1 correct) |
| local wiki passage only, dev | 21 | 1 | 0 | 1 | 1 |
- v1: 61 specifications cited web-snippet text that is not in the pinned page: the verbatim check rejected them all.
- v2 failure reasons: no op (answer stated or not computable) 141, unparsable quote 42, quote not verbatim 22, other 7.
- The 8 wrong certificates in test: 6 are present-tense "how old is X" (gold written in 2021; the certificate computes against a
  later date: stale gold, and a present-tense age question depends on today's date, which a page cannot supply); 2 are semantic
  misreads with correct quotes and arithmetic (NFL roster 69 vs 53; Lincoln Memorial 8 vs 50, where the already released answer 50
  was right). Dev: NFL preseason games, 0 (wrong).
- Correct: Grant 63, Godfather II 2, Civil War 4 (all three already released), Einstein 76 (new).

## Reading
- The soundness part works as designed: no certificate rests on a fabricated or paraphrased quote, and the computation is exact.
- The gap is the one L3 already names: a correct derivation from a verbatim span can still answer a different question
  (NFL roster, Paris "30"). Certificates do not close it.
- Coverage value is negligible here: at most 1.4% of items are derivable at all; with a question-only time rule for present-tense
  "how old is" and a disagreement rule (withhold when the certificate differs from an already released answer) the net is 1 new
  correct release in 224 candidates and 1-2 wrong. Not worth adding to the system. Value: the formal extension of L3 to derived numbers,
  and an honest negative on its practical size.
