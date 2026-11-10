"""S42 E7 helpers: subject link S (docs/S42_CLAIM_AUDIT_AND_PLAN.md section 8)."""
import re, unicodedata
QSTOP = set("""a an the of in on at to for from by with and or as is was were are be been being did does do has have had what which who
whom whose when where why how many much that this these those it its his her their there than then into over under about after before
during between up out not no year years month day date name full number first last according give tell
born die died death wrote written write directed direct director film movie book novel capital city country head government""".split())


def fold(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).casefold()


def toks(s):
    return re.findall(r"[a-z0-9]+", fold(s))


def subject_tokens(question):
    """Content tokens of the question: what is left after question words, relation words and 4-digit years."""
    return [w for w in toks(question) if w not in QSTOP and not re.fullmatch(r"1[0-9]{3}|20[0-9]{2}", w)]


def subject_link(question, title, quote):
    """S: every content token of the question occurs in the page title or in the quote (accents folded)."""
    have = set(toks(title)) | set(toks(quote))
    st = subject_tokens(question)
    return bool(st) and all(w in have for w in st)

TEMPLATE = {"death_year": r"In what year did (.+) die\?", "birth_year": r"In what year was (.+) born\?", "birth_place": r"Where was (.+) born\?",
            "director": r"Who directed the film (.+)\?", "author": r"Who wrote (.+)\?", "capital": r"What is the capital of (.+)\?",
            "office": r"Who was the head of government of (.+) in (\d{4})\?"}
INV = {"death_year": "Who died in {a}?", "birth_year": "Who was born in {a}?", "birth_place": "Who was born in {a}?",
       "director": "Which film did {a} direct?", "author": "What did {a} write?", "capital": "{a} is the capital of which country?",
       "office": "Of which country was {a} the head of government in {y}?"}
CON = {"death_year": "In what year was {s} born?", "birth_year": "In what year did {s} die?", "birth_place": "Where did {s} die?",
       "director": "Who composed the music for the film {s}?", "author": "Who illustrated {s}?",
       "capital": "What is the second-largest city of {s}?", "office": "Who was the head of government of {s} in {y2}?"}
GP = ('Page title: {t}\nSentence from that page: "{s}"\n\nQuestion: {q}\n'
      "Answer in a few words with only what this sentence states. If the sentence does not state the answer to this exact question, reply NONE.")   # as in e6_build.py


def subject(rel, question):
    m = re.fullmatch(TEMPLATE[rel], question.strip())
    return (m.group(1), m.group(2) if rel == "office" else None) if m else (None, None)


def prompts(x, c):
    """Four reader prompts for candidate quote c of item x: the question; the question on the quote with the span swapped;
    the inverse question (answer given, subject asked); a contrasting question that the quote should not answer with the span."""
    s, y = subject(x["relation"], x["question"])
    sw = c["quote"][:c["o1"]] + x["swap"] + c["quote"][c["o2"]:]
    return [GP.format(t=c["doc"], s=c["quote"], q=x["question"]), GP.format(t=c["doc"], s=sw, q=x["question"]),
            GP.format(t=c["doc"], s=c["quote"], q=INV[x["relation"]].format(a=x["answer"], y=y)),
            GP.format(t=c["doc"], s=c["quote"], q=CON[x["relation"]].format(s=s, y2=(int(y) - 40) if y else None))]
