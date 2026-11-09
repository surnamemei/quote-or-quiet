"""L3 design (DEV only): entity slot made explicit. For a released answer, find the question's subject mention, the local-wiki
senses that share it, and decide the output state:
  Verified  : subject unambiguous (one sense), or the question names the sense's qualifier, or the release page is the only
              sense whose text contains the answer and no other sense could be meant (see below)
  Qualified : subject ambiguous; the answer is stated together with the sense it holds for ("A, assuming <sense title>")
  Unresolved: subject ambiguous and no single sense can be named (the answer occurs on several senses' pages, or on none)
Subject mention: the longest question n-gram (1-8 tokens, containing a capitalised word or a digit) that equals the normalised core
of at least one local-wiki title. Titles of disambiguation pages, lists and indexes are not senses."""
import re, sqlite3, sys, unicodedata
from functools import lru_cache
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from vkg import localwiki as LW  # noqa: E402

TDB = sqlite3.connect(f"file:{ROOT / 'results/runs/l3/titles.db'}?mode=ro", uri=True, check_same_thread=False)
NOT_SENSE = re.compile(r"\b(disambiguation|surname|given name|name)\b|^(list|lists|index|outline|glossary|timeline) of ", re.I)
STOPQ = set("who what which when where why how is was are were the a an of in on at to for by did does do whose whom".split())


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().casefold()
    return " ".join(re.sub(r"[^a-z0-9]", " ", s).split())


@lru_cache(maxsize=None)
def senses(ncore, mention=None):
    """Sense pages for a subject: titles whose core (before a trailing "(...)") normalises to ncore, plus place-style titles
    "<mention>, <qualifier>" (Lima, Ohio). Duplicates removed; disambiguation/name/list pages excluded."""
    rows = TDB.execute("SELECT title, qual, len FROM t WHERE ncore = ?", (ncore,)).fetchall()
    if mention:
        rows += [(t, t[len(mention) + 2:], n) for t, n in
                 TDB.execute("SELECT title, len FROM t WHERE title >= ? AND title < ?", (mention + ", ", mention + ",￿")).fetchall()
                 if PLACEQ.match(t[len(mention) + 2:])]          # v4: only place-style qualifiers ("Ohio", "New York")
    out, seen = [], set()
    for t, q, n in rows:
        if t in seen or NOT_SENSE.search(t) or NOT_SENSE.search(q or ""):
            continue
        seen.add(t)
        out.append((t, q, n))
    return tuple(out)


GENERIC = re.compile(r"^(American|British|English|Scottish|Welsh|Irish|French|German|Italian|Spanish|Portuguese|Dutch|Belgian|Swiss|"
                     r"Austrian|Swedish|Norwegian|Danish|Finnish|Icelandic|Polish|Czech|Slovak|Hungarian|Romanian|Bulgarian|Greek|"
                     r"Turkish|Russian|Ukrainian|Serbian|Croatian|Chinese|Japanese|Korean|Indian|Pakistani|Bangladeshi|Iranian|"
                     r"Iraqi|Israeli|Egyptian|Nigerian|Kenyan|South African|Australian|Canadian|Mexican|Brazilian|Argentine|"
                     r"Argentinian|Chilean|Colombian|Peruvian|Cuban|Filipino|Indonesian|Vietnamese|Thai|Malaysian|Soviet|European|"
                     r"African|Asian|Latin|Arab|Persian|Jewish|Catholic|Christian|Muslim|Islamic|"
                     r"USA|US|UK|EU|UN|USSR|UAE|U\.S\.|U\.K\.|"
                     r"Ph\.D\.?|PhD|B\.A\.?|M\.A\.?|B\.S\.?|M\.S\.?|BA|MA|BS|MS|MBA|CEO|TV|DJ|MP|MLB|NBA|NFL|NHL)$")   # v4: degrees, titles, leagues
PLACEQ = re.compile(r"^[A-Z][\w.'’-]*(?:\s+[A-Z][\w.'’-]*){0,2}$")
YEARLIKE = re.compile(r"^\d+(s)?$")


def mentions(question):
    """Named n-grams of the question (possessive 's stripped) that equal a local-wiki title core, longest first; a bare
    capitalised first word, pure numbers and years are skipped."""
    q = re.sub(r"['’]s\b", "", question)
    toks = re.findall(r"[^\W_]+(?:['’.-][^\W_]+)*", q)
    out, used = [], set()
    for n in range(min(8, len(toks)), 0, -1):
        for i in range(len(toks) - n + 1):
            if any(k in used for k in range(i, i + n)):
                continue
            g = toks[i:i + n]
            if all(w.casefold() in STOPQ for w in g) or all(YEARLIKE.match(w) for w in g):
                continue
            caps = [k for k, w in enumerate(g) if w[:1].isupper() or w[:1].isdigit()]
            if not caps or (n == 1 and i == 0):
                continue
            if g[0].casefold() in STOPQ or (g[-1].casefold() in STOPQ and not g[-1][:1].isupper()):   # v3: "Carry On"
                continue
            if n == 1 and (GENERIC.match(g[0]) or len(g[0]) <= 2):      # v3: demonyms, country codes, "3D" are not subjects
                continue
            nc = norm(" ".join(g))
            if nc and senses(nc, " ".join(g)):
                out.append((nc, " ".join(g)))
                used.update(range(i, i + n))
    return out


def core_of(title):
    m = re.match(r"^(.*?)\s*\(([^()]*)\)$", title)
    t = m.group(1) if m else title
    return t.split(", ")[0] if ", " in t else t


def contains(text, a):
    return bool(text) and (" " + norm(a) + " ") in (" " + norm(text) + " ")


CONNECT = {"de", "da", "do", "dos", "das", "del", "della", "di", "van", "von", "der", "den", "le", "la", "y", "bin", "ibn", "al", "of"}


def qtokens(question):
    return re.findall(r"[^\W_]+", unicodedata.normalize("NFKD", question).encode("ascii", "ignore").decode())


def token_match(core, question):
    """Every token of the page title core (at least 2 tokens) occurs in the question; a one-letter token (initial) matches any
    question token with that first letter."""
    ct = [w.casefold() for w in re.findall(r"[^\W_]+", unicodedata.normalize("NFKD", core).encode("ascii", "ignore").decode())]
    if len(ct) < 2:
        return False
    qt = [w.casefold() for w in qtokens(question)]
    return all((w in qt) if len(w) > 1 else any(x.startswith(w) for x in qt) for w in ct)


def cap_runs(question):
    """Maximal runs of capitalised tokens (connectors like 'de', 'van' allowed inside), as strings."""
    toks = qtokens(re.sub(r"['’]s\b", "", question))
    runs, cur = [], []
    for k, w in enumerate(toks):
        if (w[:1].isupper() and k > 0) or (cur and w.casefold() in CONNECT):
            cur.append(w)
        else:
            if cur:
                runs.append(cur)
            cur = [w] if (w[:1].isupper() and k > 0) else []
    if cur:
        runs.append(cur)
    return [" ".join(r).strip() for r in runs if r and r[-1].casefold() not in CONNECT]


def is_fragment(mention, question):
    """The mention is a strict part of a longer capitalised name in the question that has no local-wiki title of its own."""
    nm = norm(mention)
    for run in cap_runs(question):
        nr = norm(run)
        if nr != nm and (" " + nm + " ") in (" " + nr + " ") and len(nr.split()) > len(nm.split()) and not senses(nr, run):
            return True
    return False


TYPE_HINTS = [
    (r"\b(direct|director|directed|screenwriter|screenplay|producer|produced|cinematograph|starr|cast|composer of the score)\w*",
     r"film|movie|tv series|television|miniseries|serial|show"),
    (r"\b(author|wrote|written|writer|novel|book|publish)\w*", r"novel|book|play|short story|novella|poem|comic|manga|series"),
    (r"\b(composer|composed|song|album|singer|band|recorded|genre)\w*", r"album|song|single|band|opera|musical|composition|novel|film"),
    (r"\b(capital|country|located|city|province|state|region|river|mountain|born in)\w*", r"[A-Z]|river|city|town|village|province|county|state|region|mountain|lake|island|district"),
    (r"\b(occupation|profession|father|mother|spouse|wife|husband|son|daughter|born|died|played for|position)\w*",
     r"\w+(er|ist|or|ian|ant|ent|man|woman|player|footballer|politician|actor|actress|singer|musician|born|died)\b"),
]


AUTHOR_Q = re.compile(r"\b(author|wrote|written|writer|novel)\w*", re.I)
ADAPTATION = re.compile(r"film|movie|tv|television|miniseries|series|musical|soundtrack|album|opera|play|video game|game", re.I)


def incompatible(question, qual):
    """v4: for authorship questions, adaptation senses (film, TV, musical ...) are not what the question means."""
    return bool(AUTHOR_Q.search(question)) and bool(ADAPTATION.search(qual)) and not re.search(r"novel|book|novella", qual, re.I)


def type_hint(question):
    for qrx, srx in TYPE_HINTS:
        if re.search(qrx, question, re.I):
            return srx
    return None


def decide(question, answer, release_doc, strict=True):
    """Returns (state, assumed_sense, info). strict: an ambiguous anchor whose senses do not hold the answer -> Unresolved
    (else Verified)."""
    nq = " " + norm(question) + " "
    dcore = core_of(release_doc)
    aggregator = bool(NOT_SENSE.search(release_doc))            # "Outline of X", "List of ...", "Index of X-related articles"
    longer = [m for m in mentions(question) if (" " + norm(dcore) + " ") in (" " + m[0] + " ") and m[0] != norm(dcore)]
    if longer and (" " + norm(dcore) + " ") in nq:              # the question names something longer than the page core
        nc, mention = longer[0]
        anchor = "longest mention"
    elif (" " + norm(dcore) + " ") in nq and not aggregator:    # anchor = the release page's own subject
        nc, mention, anchor = norm(dcore), dcore, "release page"
    elif token_match(dcore, question):                          # page title is a shortened form of the name in the question
        return "Verified", release_doc, {"why": "question names the release page's subject more fully", "mention": dcore}
    else:
        lead = (LW.page_text(release_doc) or "")[:400]
        for run in cap_runs(question):                         # v3: a full name in the question that the release page's lead
            if len(run.split()) >= 2 and contains(lead, run) and len(senses(norm(run), run)) <= 1:   # states is the subject
                return "Verified", release_doc, {"why": "release page lead states the question's full name", "mention": run}
        M = [m for m in mentions(question) if not is_fragment(m[1], question)]
        if not M:
            return "Verified", None, {"why": "no subject mention found (or only fragments of a more specific name)"}
        nc, mention = M[0]
        anchor = "longest mention"
    S = senses(nc, mention)
    rcore = norm(dcore)
    if anchor == "longest mention" and len(S) <= 1 and not aggregator and release_doc not in [t for t, _, _ in S] \
            and rcore.startswith(nc + " "):               # release page is a longer namesake (Salaryman -> Salaryman Kintaro)
        return "Qualified", release_doc, {"mention": mention, "n": len(S), "anchor": anchor, "why": "release page is a longer namesake"}
    named = [t for t, q, _ in S if q and all((" " + norm(w) + " ") in nq for w in re.findall(r"[^\W_]+", q) if len(w) > 2)]
    info = {"mention": mention, "n": len(S), "anchor": anchor}
    if len(S) <= 1:
        return "Verified", (S[0][0] if S else release_doc), {**info, "why": "one sense"}
    if len(named) == 1:
        return "Verified", named[0], {**info, "why": "question names the qualifier"}
    titles = [t for t, _, _ in S]
    hint = type_hint(question)
    if hint:                                              # relation implies an entity type: prefer senses of that type
        typed = [t for t, q, _ in S if q and re.search(hint, q, re.I) and not incompatible(question, q)]
        held = [t for t in typed if t == release_doc or contains(LW.page_text(t), answer)]
        if len(held) == 1:
            return "Qualified", held[0], {**info, "why": "typed sense holds the answer"}
    rq = dict((t, q) for t, q, _ in S).get(release_doc, "")
    if release_doc in titles and not (hint and rq and incompatible(question, rq)):   # v4: a sense of the wrong type is not named
        return "Qualified", release_doc, {**info, "why": "release page is a sense"}
    primary = [t for t in titles if norm(t) == nc]
    if primary and contains(LW.page_text(primary[0]), answer):
        return "Qualified", primary[0], {**info, "why": "primary topic holds the answer"}
    hold = [t for t in titles if contains(LW.page_text(t), answer)]
    if len(hold) == 1:
        return "Qualified", hold[0], {**info, "why": "answer on one sense page"}
    # v5 (DEV-designed 2026-11-09), two additions, both only for what v4 left Unresolved:
    QSTOP = {"the", "and", "for", "of", "in", "film", "series"}
    if len(hold) >= 2:                                     # R1: a word of exactly one holding sense's qualifier is in the question
        qw = [t for t, q, _ in S if t in hold and q and any(w in set(nq.split()) for w in norm(q).split() if len(w) > 3 and w not in QSTOP)]
        if len(qw) == 1:
            return "Qualified", qw[0], {**info, "why": "v5 R1: question word matches the sense's qualifier"}
    if not hold and primary and norm(dcore) == norm(answer) and contains(LW.page_text(release_doc), mention):
        # R2: the answer is the release page's own subject, and that page names the question's entity; E = its primary topic
        return "Qualified", primary[0], {**info, "why": "v5 R2: answer is the page subject and the page names the mention"}
    if strict == "mid" and not hold and contains(LW.page_text(release_doc), mention):
        return "Verified", release_doc, {**info, "why": "mid: answer on no sense page; release page names the mention"}
    if strict:
        return "Unresolved", None, {**info, "why": f"answer on {len(hold)} sense pages"}
    return "Verified", release_doc, {**info, "why": f"lenient: answer on {len(hold)} sense pages"}
