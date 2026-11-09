"""Phase 0 task generators.

Every item has an independent, programmatic ground truth (no LLM judge):

  formal       computable answer (arithmetic / dates / string ops), gold from Python
  closed_ans   answer is stated in a synthetic passage about INVENTED entities
  closed_unans passage is silent on the asked attribute (a distractor org has it)
  closed_conf  passage states two irreconcilable values from equal-rank sources
  open_fict    question about an INVENTED entity, no context  -> nothing can be known
  open_real    small set of stable real-world facts (over-abstention check)

kind in {answerable, unanswerable, conflict}. Correct handling:
  answerable   -> the gold answer
  unanswerable -> status "unknown"
  conflict     -> status "conflict" ("unknown" is safe but not full credit)
"""
import random
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional

SYL = ["vel", "qor", "thra", "mi", "zun", "bra", "lek", "oss", "dri", "tav", "kel", "un", "fa", "rho",
       "nex", "sil", "gar", "pu", "ond", "ey", "mar", "ith", "cal", "wen", "yor", "ba", "ren", "tos"]


def _name(rng, k=None):
    k = k or rng.choice([2, 3])
    return "".join(rng.choice(SYL) for _ in range(k)).capitalize()


@dataclass
class Item:
    id: str
    family: str
    kind: str                      # answerable | unanswerable | conflict
    question: str
    passage: Optional[str] = None
    gold: List[str] = field(default_factory=list)   # accepted answers (answerable only)
    meta: dict = field(default_factory=dict)


# ---------------------------------------------------------------- formal
def _formal(rng, i):
    t = rng.choice(["arith", "arith", "date", "count", "pct"])
    if t == "arith":
        a, b, c, d = rng.randint(1000, 9999), rng.randint(100, 999), rng.randint(10, 99), rng.randint(100, 5000)
        expr = f"{a} * {b} - {c} * {d}"
        return Item(f"formal-{i}", "formal", "answerable", f"Compute {expr}.", gold=[str(eval(expr))],
                    meta={"expr": expr})
    if t == "date":
        d0 = date(2020, 1, 1) + timedelta(days=rng.randint(0, 2000))
        n = rng.randint(50, 900)
        return Item(f"formal-{i}", "formal", "answerable",
                    f"What calendar date (YYYY-MM-DD) is {n} days after {d0.isoformat()}?",
                    gold=[(d0 + timedelta(days=n)).isoformat()])
    if t == "count":
        s = "".join(rng.choice("abcdeiorst") for _ in range(rng.randint(22, 34)))
        ch = rng.choice("aeiorst")
        return Item(f"formal-{i}", "formal", "answerable",
                    f"How many times does the letter '{ch}' occur in the string \"{s}\"?",
                    gold=[str(s.count(ch))], meta={"s": s, "ch": ch})
    p, base = rng.choice([12, 15, 18, 35, 45, 65, 85]), rng.randint(200, 9000) * 4
    return Item(f"formal-{i}", "formal", "answerable", f"What is {p}% of {base}?",
                gold=[f"{base * p / 100:g}"])


# ---------------------------------------------------------------- closed evidence
ATTRS = {
    "founded": ("was founded in {v}", "In what year was {o} founded?", lambda r: str(r.randint(1901, 2012))),
    "hq": ("is headquartered in {v}", "In which city is {o} headquartered?", lambda r: _name(r, 3)),
    "director": ("is directed by {v}", "Who directs {o}?", lambda r: f"{_name(r, 2)} {_name(r, 3)}"),
    "staff": ("employs {v} researchers", "How many researchers does {o} employ?", lambda r: str(r.randint(12, 980))),
    "budget": ("has an annual budget of {v} million dollars", "What is the annual budget of {o}, in millions of dollars?",
              lambda r: str(r.randint(3, 480))),
    "project": ("runs a flagship project called {v}", "What is the name of the flagship project run by {o}?",
                lambda r: _name(r, 3)),
    "partner": ("collaborates mainly with the {v}", "Which organisation does {o} collaborate with mainly?",
                lambda r: f"{_name(r, 2)} Group"),
}


def _org_facts(rng, org, keys):
    facts = {k: ATTRS[k][2](rng) for k in keys}
    sents = [f"{org} {ATTRS[k][0].format(v=v)}." for k, v in facts.items()]
    return facts, sents


def _closed(rng, i, kind):
    a, b = f"{_name(rng)} Institute", f"{_name(rng)} Laboratory"
    keys = list(ATTRS)
    rng.shuffle(keys)
    ka = keys[:4]
    missing = keys[4]
    kb = ka[:2] + [missing]            # distractor org HAS the attribute A lacks
    fa, sa = _org_facts(rng, a, ka)
    fb, sb = _org_facts(rng, b, kb)
    if kind == "answerable":
        k = rng.choice(ka)
        sents = sa + sb
        q, gold = ATTRS[k][1].format(o=a), [fa[k]]
        meta = {"attr": k}
    elif kind == "unanswerable":
        sents = sa + sb
        q, gold = ATTRS[missing][1].format(o=a), []
        meta = {"attr": missing}
    else:  # conflict
        k = rng.choice(ka)
        other = ATTRS[k][2](rng)
        while other == fa[k]:
            other = ATTRS[k][2](rng)
        sa = [s for s in sa if ATTRS[k][0].split("{")[0].strip() not in s] + [
            f"The {a} brochure says that it {ATTRS[k][0].format(v=fa[k])}.",
            f"The official registry filing says that {a} {ATTRS[k][0].format(v=other)}.",
        ]
        sents = sa + sb
        q, gold = ATTRS[k][1].format(o=a), []
        meta = {"attr": k, "values": [fa[k], other]}
    rng.shuffle(sents)
    return Item(f"closed_{kind[:4]}-{i}", {"answerable": "closed_ans", "unanswerable": "closed_unans",
                                           "conflict": "closed_conf"}[kind],
                kind, q, passage=" ".join(sents), gold=gold, meta=meta)


# ---------------------------------------------------------------- open world, fictional
def _fict(rng, i):
    n1, n2 = _name(rng, 3), _name(rng, 2)
    t = rng.choice(["treaty", "paper", "novel", "theorem", "battle"])
    if t == "treaty":
        q = f"In what year was the {n1}-{n2} Treaty signed, and between which two nations?"
    elif t == "paper":
        q = f"Who wrote the 2009 paper \"{n1} Dynamics in {n2} Lattices\", and what was its main result?"
    elif t == "novel":
        q = f"Who is the author of the novel \"The {n1} of {n2}\", and when was it first published?"
    elif t == "theorem":
        q = f"State the {n1}-{n2} theorem and name the mathematician who proved it."
    else:
        q = f"Who won the Battle of {n1}, and in which year did it take place?"
    return Item(f"open_fict-{i}", "open_fict", "unanswerable", q, meta={"type": t})


REAL = [
    ("What is the chemical symbol of tungsten?", ["W"]),
    ("In what year did Apollo 11 land on the Moon?", ["1969"]),
    ("Who wrote the novel The Master and Margarita?", ["Bulgakov"]),
    ("What is the capital of Kazakhstan?", ["Astana"]),
    ("What is the atomic number of iron?", ["26"]),
    ("In what year did the Berlin Wall fall?", ["1989"]),
    ("Who published the Principia Mathematica in 1687?", ["Newton"]),
    ("What is the longest river in Africa?", ["Nile"]),
    ("In what year was the Peace of Westphalia concluded?", ["1648"]),
    ("What is the capital of Mongolia?", ["Ulaanbaatar", "Ulan Bator"]),
    ("Who painted Las Meninas?", ["Velazquez", "Velázquez"]),
    ("Which element has atomic number 79?", ["gold"]),
    ("In what year was Magna Carta sealed?", ["1215"]),
    ("Who wrote Pride and Prejudice?", ["Austen"]),
    ("In what year did the Chernobyl disaster occur?", ["1986"]),
    ("Who discovered penicillin?", ["Fleming"]),
    ("Who proved Fermat's Last Theorem?", ["Wiles"]),
    ("In what year did the Titanic sink?", ["1912"]),
    ("Who wrote One Hundred Years of Solitude?", ["Marquez", "Márquez"]),
    ("What is the capital of Turkey?", ["Ankara"]),
    ("In what year did World War I begin?", ["1914"]),
    ("Who invented the World Wide Web?", ["Berners-Lee", "Berners Lee"]),
    ("What is the capital of Myanmar?", ["Naypyidaw", "Nay Pyi Taw", "Naypyitaw"]),
    ("In what year was the Eiffel Tower completed?", ["1889"]),
    ("How many squares are on a chessboard?", ["64"]),
    ("What is the speed of light in a vacuum, in metres per second?", ["299792458", "299,792,458"]),
    ("What is the largest planet in the Solar System?", ["Jupiter"]),
    ("What is the currency of Japan?", ["yen"]),
    ("What is the smallest prime number?", ["2"]),
    ("What is the capital of Canada?", ["Ottawa"]),
]


def build(seed=0, n_formal=60, n_ans=60, n_unans=60, n_conf=30, n_fict=60):
    rng = random.Random(seed)
    items = [_formal(rng, i) for i in range(n_formal)]
    items += [_closed(rng, i, "answerable") for i in range(n_ans)]
    items += [_closed(rng, i, "unanswerable") for i in range(n_unans)]
    items += [_closed(rng, i, "conflict") for i in range(n_conf)]
    items += [_fict(rng, i) for i in range(n_fict)]
    items += [Item(f"open_real-{i}", "open_real", "answerable", q, gold=g) for i, (q, g) in enumerate(REAL)]
    return items


# ---------------------------------------------------------------- FaithEval (real data, Salesforce, ICLR 2025)
def faitheval(n=150, seed=0, exclude_seed=None):
    """Samples n unanswerable + n inconsistent items. Needs data/hf cache (see docs/REUSE_MAP.md).
    unanswerable -> kind=unanswerable ; inconsistent -> kind=conflict (context mixes original and altered answer)."""
    import os
    os.environ.setdefault("HF_HOME", str(__import__("pathlib").Path(__file__).resolve().parent.parent / "data" / "hf"))
    from datasets import load_dataset
    cache = os.environ["HF_HOME"]
    rng = random.Random(seed)
    items = []
    for name, fam, kind in [("unanswerable", "faith_unans", "unanswerable"), ("inconsistent", "faith_conf", "conflict")]:
        d = load_dataset(f"Salesforce/FaithEval-{name}-v1.0", split="test", cache_dir=cache)
        pool = range(len(d))
        if exclude_seed is not None:      # keep held-out sample disjoint from the dev sample
            dev = {it.id for it in faitheval(n, exclude_seed)}
            pool = [i for i in pool if f"{fam}-{d[i]['qid']}" not in dev]
        idx = rng.sample(list(pool), n)
        for i in idx:
            r = d[i]
            items.append(Item(f"{fam}-{r['qid']}", fam, kind, r["question"], passage=r["context"],
                              meta={"subset": r["subset"], "answers": str(r["answers"])}))
    return items


def squad2(n=150, seed=0, exclude_seed=None):
    """Real answerable + human-written unanswerable questions (SQuAD 2.0 validation). Gives a yield control."""
    import os
    os.environ.setdefault("HF_HOME", str(__import__("pathlib").Path(__file__).resolve().parent.parent / "data" / "hf"))
    from datasets import load_dataset
    d = load_dataset("rajpurkar/squad_v2", split="validation", cache_dir=os.environ["HF_HOME"])
    rng = random.Random(seed)
    ans = [i for i in range(len(d)) if d[i]["answers"]["text"]]
    una = [i for i in range(len(d)) if not d[i]["answers"]["text"]]
    if exclude_seed is not None:
        dev = {it.id for it in squad2(n, exclude_seed)}
        ans = [i for i in ans if f"squad_ans-{d[i]['id']}" not in dev]
        una = [i for i in una if f"squad_unans-{d[i]['id']}" not in dev]
    items = []
    for i in rng.sample(ans, n):
        r = d[i]
        items.append(Item(f"squad_ans-{r['id']}", "squad_ans", "answerable", r["question"], passage=r["context"],
                          gold=sorted(set(r["answers"]["text"]))))
    for i in rng.sample(una, n):
        r = d[i]
        items.append(Item(f"squad_unans-{r['id']}", "squad_unans", "unanswerable", r["question"], passage=r["context"]))
    return items


def simpleqa(n=500, seed=0):
    """SimpleQA Verified (Google, 2025): open-world short-answer questions, no passage. All items have a gold answer,
    so kind=answerable; an abstention counts as over_abstain (not-attempted), a non-matching answer as silent_error."""
    import os
    os.environ.setdefault("HF_HOME", str(__import__("pathlib").Path(__file__).resolve().parent.parent / "data" / "hf"))
    from datasets import load_dataset
    d = load_dataset("google/simpleqa-verified", split="eval", cache_dir=os.environ["HF_HOME"])
    rng = random.Random(seed)
    idx = rng.sample(range(len(d)), min(n, len(d)))
    return [Item(f"sqa-{d[i]['original_index']}", "sqa", "answerable", d[i]["problem"], gold=[d[i]["answer"]],
                 meta={"topic": d[i]["topic"], "answer_type": d[i]["answer_type"]}) for i in idx]


def simpleqa_rag(n=500, seed=0, mode="search"):
    """Same questions as simpleqa(n, seed), but with a Wikipedia passage attached.
    mode='search': passage from keyword search over live Wikipedia (no gold information used).
    mode='oracle': passage from the dataset's own Wikipedia source pages (upper bound; skips questions with no Wikipedia source)."""
    import os
    from concurrent.futures import ThreadPoolExecutor
    from . import retrieval as R
    os.environ.setdefault("HF_HOME", str(__import__("pathlib").Path(__file__).resolve().parent.parent / "data" / "hf"))
    from datasets import load_dataset
    d = load_dataset("google/simpleqa-verified", split="eval", cache_dir=os.environ["HF_HOME"])
    rng = random.Random(seed)
    idx = rng.sample(range(len(d)), min(n, len(d)))

    def one(i):
        q = d[i]["problem"]
        if mode == "hybrid":      # S2 variant E: generator-written queries + baseline search, 10 pages, BM25+dense fusion, 1500 words
            from . import retrieval2 as R2
            titles = R2.titles_for(q, 10, "qwen3.8-27b")
            psg = R2.passage(q, titles, 1500) or "(no text was retrieved)"
            return Item(f"sqa-{d[i]['original_index']}", "sqa_hyb", "answerable", q, passage=psg, gold=[d[i]["answer"]],
                        meta={"topic": d[i]["topic"], "titles": titles})
        titles = R.search(q) if mode == "search" else R.wiki_titles_from_urls(d[i]["urls"])
        if mode == "oracle" and not titles:
            return None
        psg = R.build_passage(q, titles) or "(no text was retrieved)"
        fam = "sqa_rag" if mode == "search" else "sqa_orc"
        return Item(f"sqa-{d[i]['original_index']}", fam, "answerable", q, passage=psg, gold=[d[i]["answer"]],
                    meta={"topic": d[i]["topic"], "titles": titles})
    with ThreadPoolExecutor(4 if mode != "hybrid" else 2) as ex:
        items = [x for x in ex.map(one, idx) if x is not None]
    if mode == "hybrid":
        from . import retrieval2 as R2
        R2.save_cache()
    return items


# ---------------------------------------------------------------- grading
def norm(s):
    s = str(s).lower().replace(",", "")
    s = re.sub(r"[^\w\s.\-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def matches(gold_list, answer):
    a = norm(answer)
    for g in gold_list:
        g = norm(g)
        if re.search(rf"(?<![\w.]){re.escape(g)}(?![\w]|\.\d)", a):
            return True
    return False
