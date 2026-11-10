"""One-off: replace the 600-word abstract by a short one; the full list of numbers stays in Sections 5.1 to 5.17."""
from pathlib import Path
m = Path(r"F:\Projects\AI hallucinations\paper\manuscript.md")
lines = m.read_text(encoding="utf-8").split("\n")
i = next(n for n, l in enumerate(lines) if l.startswith("A language model that answers a factual question wrongly"))
old = lines[i]
new = ("A language model that answers a factual question wrongly and without qualification commits a silent error. We ask how far a small local system can remove two failures: the wrong answer, "
       "and the right answer shown with a quote that does not say it, which misleads the person who re-checks the release. The system releases an answer only when three evidence sources agree, the answer is a verbatim, typed span of a hash-pinned page, and a second reader concurs. "
       "On 1,526 sealed SimpleQA questions it answered 37.2% with a one-sided 97.5% upper bound on the silent-error rate of 0.76%; on a second sealed set of 3,359 Wikidata questions it answered 52.5% with an upper bound of 0.88%; on Mintaka and PopQA it missed the 35% coverage floor. "
       "Raising coverage by pinning pages or relaxing answer formats added answers at 5 to 6% error. "
       "A quote that exists need not state the answer: in blind review by language models the displayed quote did not state it in 12.5% of Verified releases, 72 of 75 of them with right answers. "
       "Choosing, among the accepted spans, the first that passes a frame check, a subject link and a quote-only reader reduced this to 2 of 1,017 fresh releases (0.20%, upper bound 0.71%) at a cost of 7% of the releases. "
       "The same idea answered names that several films or people share reading by reading (no misleading quote in 250 readings) and, for biographies written from the subject's own page, kept 61% of the claims of fifty fresh subjects (1 false claim and 1 misleading quote in a blind sample of 400), but failed on closed-book drafts (4.7% false). "
       "It does not carry over without limits: a relation-free version held on one set of open questions (1.0% misleading) and failed on a natural-question set (24%), witnesses on later spans were less safe than on the first span, and web pages gave 3.8% misleading; a small judge trained on the reviewers' labels transferred better (5.2% on the natural-question set). "
       "Most results are design data and the reviewers are language models. The guarantee is that the page says it, not that the page is right.")
lines[i] = new
m.write_text("\n".join(lines), encoding="utf-8")
print(len(old.split()), "->", len(new.split()), "words")
