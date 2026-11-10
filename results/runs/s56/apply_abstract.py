"""One-off: shorten the abstract of paper/manuscript.md and add the third sealed set and contested topics."""
from pathlib import Path
m = Path(__file__).resolve().parents[3] / "paper/manuscript.md"; L = m.read_text(encoding="utf-8").split("\n")
assert L[8].startswith("A language model that answers a factual question wrongly")
L[8] = ("A language model that answers a factual question wrongly and without qualification commits a silent error. We ask how far a small local system can remove two failures: the wrong answer, and the right answer shown with a quote that does not say it, which misleads the person who re-checks the release. "
"The system releases an answer only when three evidence sources agree, the answer is a verbatim, typed span of a hash-pinned page, and a second reader concurs. "
"On 1,526 sealed SimpleQA questions it answered 37.2% with a one-sided 97.5% upper bound on the silent-error rate of 0.76%; on a second sealed set of 3,359 Wikidata questions it answered 52.5% with an upper bound of 0.88%; on a third sealed set of 3,040 Wikidata questions, with a registered two-source cell added, it answered 55.1% with an upper bound of 0.65%. On Mintaka and PopQA it missed the 35% coverage floor. "
"A quote that exists need not state the answer: in blind review by language models the displayed quote did not state it in 12.5% of releases, 72 of 75 of them with right answers. "
"Choosing the first accepted span that passes a frame check, a subject link and a quote-only reader reduced this to 2 of 1,017 fresh releases (0.20%, upper bound 0.71%) at a cost of 7% of the releases, and on the third sealed set to 0.7% (upper bound 2.7%) against 11.3% for the displayed quote. "
"The same idea answered names that several films or people share reading by reading (no misleading quote in 250 readings) and, for biographies written from the subject's own page, kept 61% of the claims of fifty fresh subjects (1 false claim in a blind sample of 400), but failed on closed-book drafts (4.7% false). "
"On contested topics, 57% of generated statements of who holds which view had no supporting sentence, and the sentence a citing system would show failed to report the view for 17.7%. "
"It does not carry over without limits: a relation-free version held on one set of open questions and failed on a natural-question set (24% misleading); a small trained judge (5.2%) and a 27B prompted judge (1.9%) did better. "
"Most results other than the sealed sets are design data and the reviewers are language models. The guarantee is that the page says it, not that the page is right.")
m.write_text("\n".join(L), encoding="utf-8"); print(len(L[8].split()))
