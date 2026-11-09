"""Unit tests for the grader-6 vetoes (no model). python -B -m vkg.test_grade6"""
from .grade6 import veto

FIRE = [
    ("What is the full name of the Colombian soccer player Juan Guzmán born in 1988?", "Juan Pablo Guzmán Perdomo", "Juan Pablo Guzmán", "R4"),
    ("What was the full name of the composer of the theme?", 'Walter Gustave "Gus" Haenschen', "Walter Gustave", "R4"),
    ("Specify the day, month, and year Canon introduced two new lenses.", "April 2, 2019", "4 April 2019", "R1"),
    ("In what city and country did Gus Touchard Jr. pass away?", "Toronto, Canada", "Toronto", "R3"),
    ("What were the day, month, and year when Twitter tested a new homepage?", "5 April 2011", "April 5, April 20", "R2"),
    ("What relation is David W. Duclon to Cherie Johnson?", "Maternal uncle.", "uncle", "R5"),
    ("On what month, day, and year was the cave discovered?", "August 19, 2006", "August 2006", "R2"),
    ("In which month and year did X happen?", "July 1944", "1944", "R2"),
    ("When was she born?", "October 3, 1947", "October 3, 1948", "R1"),
]
PASS = [
    ("What is the name of the town in which Bartlett was born in 1880?", "Concord, Massachusetts", "Concord"),
    ("What was the church's membership in 1968?", "8000 (acceptable range: anything between 7920 and 8080)", "eight thousand"),
    ("Name the largest doab in India.", "Ganges-Yamuna Doab", "Ganga-Yamuna Doab"),
    ("Which country hosted it?", "The Republic of Colombia", "Colombia"),
    ("Who invented the glass?", "Katharine B. Blodgett", "Katharine Blodgett"),
    ("What were the day, month, and year when Twitter tested a new homepage?", "5 April 2011", "April 5, 2011"),
    ("In what city and country did he die?", "Toronto, Canada", "Toronto, Canada"),
    ("What is the full name of the singer?", "Joshna Chinappa", "Joshana Chinappa"),
    ("In which month and year did X happen?", "July 1944", "July 1944"),
    ("Who was the vice president in 1990?", "Vice President Dan Quayle", "Dan Quayle"),
    ("How many visitors in 2018?", "2,111,578 (acceptable range: anything between 2,006,000 and 2,217,157)", "2.1 million"),
]


def main():
    for q, g, a, rule in FIRE:
        assert veto(q, g, a) == rule, (q, a, veto(q, g, a), rule)
    for q, g, a in PASS:
        assert veto(q, g, a) is None, (q, a, veto(q, g, a))
    print(f"all {len(FIRE) + len(PASS)} grade6 veto tests pass")


if __name__ == "__main__":
    main()
