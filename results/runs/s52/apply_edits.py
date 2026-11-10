"""One-off: apply the audit corrections that touch the abstract, Discussion, Conclusion and header, add the Mintaka result to Sections 5.14 and 5.17 and to the S52 plan, and correct the population wording in S48/S49."""
import datetime
from pathlib import Path
ROOT = Path(r"F:\Projects\AI hallucinations")
tm = datetime.datetime.now().strftime("%H:%M")
m = ROOT / "paper/manuscript.md"; t = m.read_text(encoding="utf-8")


def rep(old, new):
    global t
    assert t.count(old) == 1, (t.count(old), old[:70])
    t = t.replace(old, new, 1)


rep("For biographies written by a 4B model the same check kept 20% of the claims of closed-book drafts with 4.7% false, and, when the draft was written from the subject's own page, 61% of the claims of fifty fresh subjects with 1 false and 1 misleading quote in a blind sample of 400. ",
    "For biographies, a sentence-level rule (W4) kept 20% of the claims of closed-book drafts written by a 14B model with 4.7% false and 4.7% misleading, and, when the draft was written from the subject's own page, 61% of the claims of fifty fresh subjects with 1 false and 1 misleading quote in a blind sample of 400. A relation-free version of the check cut the share of misleading quotes from 11.3% to 1.0% on one set of open questions but failed on a second, natural-question set (24% misleading), where a small judge trained on the reviewers' labels did better (5.2%). Witnesses on later spans were less safe than on the first span, and the check withholds 7 to 35% of the releases. ")
rep("The cost is larger than for templated questions:",
    "Rule R did not hold on the second set of open questions we gave it. On the Mintaka test set (natural crowd-worker questions; 685 releases with a candidate span, taken from the same part of the combination rule), with the rule, code and protocol unchanged and the predictions written beforehand, the displayed quote was misleading for both reviewers in 129 of 300 reviewed releases (43.0%, 97.5% upper bound 48.8%); R kept 192 (64.0%) and its quote was misleading for 46 of them (24.0%, upper bound 30.6%), with 'states' for both in 61.5%. The prediction of at most 2% failed. The misleading quotes are sentences that mention the answer entity or the topic of the page without answering the question (a sentence on a sports group for 'Fenway Park is home to what MLB team?'), accepted by the 4B judge. Rule R is therefore not a general relation-free guarantee: it worked on SimpleQA-style questions, where the fact is stated about a named subject, and not on natural questions whose releases often rest on list, index or loosely related pages.\n\nThe cost on FRESH-5 is larger than for templated questions:")
rep("The small judge is not used in any earlier result.",
    "The small judge transfers to the Mintaka set of Section 5.14, which contributed no row to its training: on the 361 non-decoy review rows its AUROC for 'states' was 0.897; of the displayed quotes it accepted at 0.5 (126 of 300), 7 were misleading for both reviewers (5.6%, upper bound 11.1%), against 43.0% for all displayed quotes and 24.0% for the quotes that rule R accepted; over all 361 rows it accepted 154 and 8 were misleading (5.2%, upper bound 10.0%). The learned decision carried over where the prompted rule did not, at a cost of about 57% of the rows. The small judge is not used in any earlier result.")
rep("An output state between Verified and Unresolved would turn the failures we measured into checkable statements.",
    "An output state between Verified and Unresolved turns the failures we measured into checkable statements; we implemented the Qualified state (Section 5.10), and it holds the gold answer in 81% of the quotes on templated questions but not on head-of-government questions or on long-form drafts.")
rep("made the shown quote misleading in 0.2% of fresh releases.",
    "made the shown quote misleading in 0.2% of 1,017 fresh releases (upper bound 0.71%), at a cost of 7% of the releases; witnesses on later spans were less safe than on the first span (2 of 134). The requirement stated without relation frames held on one set of open questions and failed on a second; a small judge trained on the reviewers' labels transferred better. For biographies the check works when the draft is written from the subject's page and not when it is written from memory.")
rep("<!-- DRAFT v0.3, 2026-11-10: adds Sections 5.10 and 5.11 (S42; numbers trace to docs/S42_CLAIM_AUDIT_AND_PLAN.md section 6 and docs/S41_RESULT.md) and the quote-sufficiency related work;",
    "<!-- DRAFT v0.4, 2026-11-10: adds Sections 5.10 to 5.17 (S42 to S52; numbers trace to docs/S42_CLAIM_AUDIT_AND_PLAN.md section 6, docs/S41_RESULT.md and docs/S43 to S52; an independent audit of these sections is in docs/PAPER_AUDIT_2026-11-10.md and its findings were corrected afterwards) and the quote-sufficiency related work;")
m.write_text(t, encoding="utf-8")

p = ROOT / "docs/S52_RULE_R_MINTAKA_PLAN.md"; s = p.read_text(encoding="utf-8").rstrip("\n")
s += f"""

## Result ({tm}; results/runs/s52/M_result.md and M_small_judge.md; the set was opened before)

Population: the 697 'source s19' releases are the part of the later combination rule (with its format gate) that comes from the frozen system, as on FRESH-5 (601 of 727); 685 of the 697 had a candidate span. R kept 453 of 685
(66.1%); the judge accepted a swapped answer for 3 of 2,166 candidates (0.14%). Blind quote-only review of 391 rows (300 releases, 61 R witnesses that differ from the displayed quote, 30 decoys; 28 distinct decoys, all caught):

| Quotes | n | misleading for both | 'states' for both |
|---|---|---|---|
| Displayed quote (first accepted span), 300 releases | 300 | 129 (43.0%, 97.5% upper 48.8%) | 123 (41.0%) |
| Displayed quote, the 192 releases R keeps | 192 | 63 (32.8%, upper 39.9%) | 99 (51.6%) |
| Rule R witness, the same 192 releases | 192 | 46 (24.0%, upper 30.6%) | 118 (61.5%) |

Against the predictions: displayed quote misleading in 8 to 20%: far off (43.0%). R keeps 65 to 90%: met at the edge (64.0% of the sample, 66.1% of all). Misleading among kept at most 2%: FAILED (24.0%). 'States' at least 90%: FAILED (61.5%).
Judge accepting a swapped answer at most 10%: met (0.14%).
Rule R, which left 1.0% misleading on FRESH-5, leaves 24% on natural Mintaka questions: the 4B judge accepts sentences that mention the answer entity or the page topic without answering the question (twelve examples read, among them a sentence on a
sports group for the home team of Fenway Park and a sentence on an award shortlist for the largest city in Scotland). Many Mintaka releases rest on list, index or loosely related pages, where no sentence states the answer.
The small judge of S51, trained without any Mintaka row, scores the review rows with AUROC 0.897 (361 non-decoy rows); accepting at 0.5 it passes 154 rows and 8 are misleading (5.2%, upper 10.0%); among the displayed quotes it passes 126 of 300 with 7 misleading (5.6%).
Reading: the relation-free requirement is not established by FRESH-5 alone; it fails on natural questions with the 4B prompt judge and a learned judge transfers better. The S40 analysis registered on 2026-11-10 20:12 is therefore a test of a rule with one success and one failure.
"""
p.write_text(s + "\n", encoding="utf-8")
for f, old, new in (("docs/S48_RELATION_FREE_PLAN.md", "Input: the 601 releases of the frozen system on FRESH-5", "Input: 601 releases on FRESH-5 (the part of the later combination rule, with its format gate, that comes from the frozen system; the frozen system itself released 568)"),
                    ("docs/S48_RELATION_FREE_PLAN.md", "601 releases of the frozen system on FRESH-5. Rule R kept", "601 releases on FRESH-5 (the S19 part of the combination rule with the format gate, not the 568 frozen releases). Rule R kept"),
                    ("docs/S49_OTHER_CORPORA_PLAN.md", "Data: the 601 FRESH-5 releases of the frozen system.", "Data: the 601 FRESH-5 releases of the S19 part of the combination rule with the format gate (the frozen system released 568).")):
    q = ROOT / f; x = q.read_text(encoding="utf-8")
    if old in x:
        q.write_text(x.replace(old, new, 1), encoding="utf-8")
    else:
        print("not found:", old[:50])
print("done")
