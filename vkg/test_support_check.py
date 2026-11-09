"""Unit tests for vkg/support_check.py (synthetic strings written by hand; none taken from the S8 fresh set).
python -B -m vkg.test_support_check"""
from .support_check import check, tokens, date_parts

P = ("Marie Louise Dubois (born 3 March 1921 in Lyon) was a French chemist. In 1950 she moved to Geneva. "
     "She received the Prix Lavoisier on June 14, 1962, and retired in September 1981 after 31 years. "
     "The company sold 1,500 units. She had two sons. The treaty of Paris was signed in May 1814.")
Q_FULL = "On what day, month, and year did she receive the Prix Lavoisier?"
Q_MY = "In what month and year did she retire?"
Q = "Who was the chemist?"

CASES = [
    (Q, "Marie Dubois", True),                    # dropped middle name, still inside one window
    (Q, "Marie Curie", False),                     # token not in passage
    (Q_FULL, "June 14, 1962", True),
    (Q_FULL, "14 June 1962", True),                # other format
    (Q_FULL, "14th of June, 1962", True),          # ordinal
    (Q_FULL, "June 1962", False),                  # incomplete for a full-date question
    (Q_FULL, "4 June 1962", False),                # wrong day
    (Q_FULL, "June 14, 1963", False),              # wrong year
    (Q_MY, "September 1981", True),
    (Q_MY, "1981", False),                         # month missing
    (Q_MY, "Sept. 1981", True),                    # abbreviation
    (Q, "1500 units", True),                       # digit grouping
    (Q, "2 sons", True),                           # number word in passage
    (Q, "three sons", False),
    (Q, "Lyon", True),
    (Q, "Lyon, France", False),                    # 'france' absent (passage says 'French')
    ("When was the treaty signed?", "May 1814", True),
    ("How long did she work?", "31 years", True),
    ("How long did she work?", "30 years", False),
    (Q, "The chemist Marie Louise Dubois", True),  # stop words ignored, 'chemist' present
]


def main():
    bad = 0
    for q, a, exp in CASES:
        r = check(q, a, P)
        if r["ok"] != exp:
            bad += 1
            print("FAIL", q, "|", a, "->", r, "expected", exp)
    assert tokens("May 1814") == ["@m5", "1814"] and tokens("you may go") == ["you", "may", "go"]
    assert date_parts(tokens("14 June 1962")) == ("14", "@m6", "1962")
    print(f"{len(CASES) - bad}/{len(CASES)} cases pass")
    assert bad == 0


if __name__ == "__main__":
    main()
