"""One-off: correct the related-work text and references of the manuscript after the systematic check (docs/S42_RELATED_WORK_v2.md)."""
from pathlib import Path
ROOT = Path(r"F:\Projects\AI hallucinations")
m = ROOT / "paper/manuscript.md"; t = m.read_text(encoding="utf-8")


def rep(old, new):
    global t
    assert t.count(old) == 1, (t.count(old), old[:80])
    t = t.replace(old, new, 1)


# numbers of BalanceRAG and Badshah that could not be confirmed
i = t.index("Both certify a calibrated confidence score at risk targets of"); j = t.index(";", i)
t = t[:i] + "Both certify a calibrated confidence score at stated risk levels, validated on random splits of the same benchmark with gold matched by semantic similarity or reference labels" + t[j:]
rep("GopherCite answers with a verbatim quote and abstains when unsure [@menick2022verified], and claim-anchored provenance drops claims for which no quote can be located, while leaving support to the model [@guan2026cams].",
    "GopherCite answers with a verbatim quote, samples several candidate answer and quote pairs, scores them with a reward model trained on human ratings of whether the quote supports the answer, and declines below a threshold [@menick2022verified]; it is the nearest precedent for choosing among quotes and abstaining. Claim-anchored provenance drops claims for which no quote can be located and checks support with an NLI-based verifier and a three-annotator study, while stating that its provenance guarantee is not a support guarantee [@guan2026cams].")
rep("Sufficiency of the evidence has been used as a release signal at passage level, with a trained or large rater [@joren2025sufficient; @qiu2026sure].",
    "Sufficiency of the evidence has been used as a release signal at the level of the evidence set or passage, with a trained or large rater [@joren2025sufficient; @qiu2026sure]. Small trained consistency checkers exist (AlignScore, MiniCheck, HHEM [@zha2023alignscore; @tang2024minicheck]) and we did not compare them with our reviewer labels, and FActScore evaluates the atomic claims of biographies against Wikipedia [@min2023factscore].")
rep("Evidence chosen to convince a reader model also sways it towards wrong answers [@perez2019convince], which is why our witness rule (Section 5.11) pairs the reader with lexical checks.",
    "Learned evidence selectors also find evidence that looks strong for wrong answers (humans rated it strong for 31.1% of wrong answers against 74.6% of right ones on RACE [@perez2019convince]), which is one reason our witness rule (Section 5.11) pairs the reader with lexical checks.")
rep("We did not find a training-free rule that chooses among all the spans a deductive gate accepts, withholds the answer when none passes, and is tested by blind review of fresh items against a bound near 1% (searched 10 November 2026; the search cannot show that none exists).",
    "Showing a verified quote with an abstention option, auditing whether the quote supports the answer, and choosing among candidate quotes are all established, most completely by GopherCite. We did not find a training-free rule that chooses among all the spans a mechanical gate accepts by a fixed checklist with a swapped-answer control, withholds the answer when none passes, and is tested by blind review of fresh items against a bound near 1%, nor a report of the share of right answers whose displayed quote does not state them (searched in two passes on 10 November 2026; the search cannot show that none exists).")
# venues and references
rep("When should LLMs be less specific? Selective abstraction for reliable long-form text generation. arXiv:2602.11908 (2026).", "When should LLMs be less specific? Selective abstraction for reliable long-form text generation. NeurIPS 2026; arXiv:2602.11908.")
rep("ACL-Verbatim: hallucination-free question answering for research. arXiv:2605.21102 (2026).", "ACL-Verbatim: hallucination-free question answering for research. Workshop on AI for Scientific Publications (WASP) 2026, 23-33; arXiv:2605.21102.")
t = t.rstrip("\n") + "\n" + "\n".join([
    "- [@min2023factscore] Min S, Krishna K, Lyu X, Lewis M, Yih W, Koh PW, Iyyer M, Zettlemoyer L, Hajishirzi H. FActScore: fine-grained atomic evaluation of factual precision in long form text generation. Proceedings of EMNLP 2023. arXiv:2305.14251.",
    "- [@zha2023alignscore] Zha Y, Yang Y, Li R, Hu Z. AlignScore: evaluating factual consistency with a unified alignment function. Proceedings of ACL 2023. arXiv:2305.16739.",
    "- [@tang2024minicheck] Tang L, Laban P, Durrett G. MiniCheck: efficient fact-checking of LLMs on grounding documents. Proceedings of EMNLP 2024. arXiv:2404.10774."]) + "\n"
m.write_text(t, encoding="utf-8")
# the limitations paragraph in 5.17: say that no checker baseline was run
t = m.read_text(encoding="utf-8")
rep("None of these judges is used in an earlier result.", "None of these judges is used in an earlier result. We did not run an off-the-shelf small checker (AlignScore, MiniCheck, HHEM) on the labels, which a reader will want as a baseline.")
m.write_text(t, encoding="utf-8")
print("ok")
