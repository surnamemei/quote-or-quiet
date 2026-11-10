"""One-off: record the reviewer-agreement table in the paper, add the public labelled subset and its licence note to the release builder."""
from pathlib import Path
ROOT = Path(r"F:\Projects\AI hallucinations")
m = ROOT / "paper/manuscript.md"; t = m.read_text(encoding="utf-8")
old = "The quote-sufficiency figures of Section 5.11 come from language-model reviewers who saw the quote alone;"
assert t.count(old) == 1
t = t.replace(old, "Over all 4,714 reviewed rows the two reviewers agree with a Cohen kappa of 0.93 (0.85 to 1.00 by source), and counting a quote as misleading when either reviewer, not both, says 'not' changes the shares by at most 2 points; but the two reviewers are two runs of the same model with the same instructions, so this measures consistency and not validity, and no human has labelled a row yet. " + old, 1)
m.write_text(t, encoding="utf-8")

(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data/README_quote_sufficiency.md").write_text("""# Quote-sufficiency labels (public subset)

`quote_sufficiency_public.jsonl`: 2,018 rows from the biography and ambiguous-name experiments of the paper (Sections 5.12 and 5.13). Each row has a question written by the pipeline, a proposed answer or value, the title of an English Wikipedia
page, a sentence of that page (the quote) and two labels from two blind language-model reviewers who saw only the quote: `states` (the quote says that this is the answer to this question), `incomplete`, or `not`. About 12% of the rows are decoys
(an answer or a question swapped on purpose; their label is `not`). The rows are not a random sample of anything: they are the rows that the experiments selected for review.

Licence: the quotes are sentences from English Wikipedia (August 2025 snapshot, FineWiki) and are available under CC BY-SA 4.0 with attribution to Wikipedia and its authors (page titles are given); the labels and questions are CC BY 4.0.
Rows from benchmark questions (SimpleQA, Mintaka), from the Wikidata-generated question sets and from web pages are not included.
Limits: the labels are from language models, not people; the two reviewers are two runs of one model, so their agreement (kappa 0.87 to 1.00 on these sets) shows consistency, not validity.
""", encoding="utf-8")
b = ROOT / "results/build_release.py"; s = b.read_text(encoding="utf-8")
if "quote_sufficiency_public" not in s:
    s = s.replace("for p in (ROOT / \"tool\").glob(\"*\"):", "for f in (\"data/quote_sufficiency_public.jsonl\", \"data/README_quote_sufficiency.md\"):\n    if (ROOT / f).exists():\n        copy(ROOT / f, T / f); n += 1\nfor p in (ROOT / \"tool\").glob(\"*\"):", 1)
    b.write_text(s, encoding="utf-8")
print("ok", "quote_sufficiency_public" in b.read_text(encoding="utf-8"))
