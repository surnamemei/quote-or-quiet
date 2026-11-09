"""S20 draft (docs/S20_PLAN.md): relation frames for the D3 check. Development on DEV only. Not frozen; not part of S19.
M_Q  question -> relation (fail-closed: exactly one relation family must match, otherwise None)
M_S  released span in its sentence -> does the sentence state relation r for the span? (fail-closed)
D3   release only if M_Q gives r and M_S confirms r with no nearer competitor trigger."""
import re

# name: (question pattern, sentence pattern, competitors)
REL = {
    "born":       (r"\bborn\b|\bbirth\b", r"\bborn\b|\bbirth\b|\bb\.\s", ("died", "baptised")),
    "baptised":   (r"\bbapti[sz]ed\b", r"\bbapti[sz]", ("born",)),
    "died":       (r"\b(die|died|death|pass(ed)? away)\b", r"\b(died|dies|death|passed away|killed|d\.)\b", ("born", "buried")),
    "buried":     (r"\bburied\b|\bburial\b", r"\bburied\b|\bburial\b|\binterred\b", ("died",)),
    "married":    (r"\bmarr(y|ied|iage)\b|\bwedding\b|\bwed\b", r"\bmarr(y|ied|iage|ies)\b|\bwed(ding|s)?\b", ("divorced", "engaged")),
    "divorced":   (r"\bdivorc", r"\bdivorc", ("married",)),
    "engaged":    (r"\bengaged\b|\bengagement\b|\bbetrothed\b", r"\bengaged\b|\bengagement\b|\bbetroth", ("married",)),
    "founded":    (r"\b(found(ed|ing)?|establish(ed|ment)?|formed)\b", r"\b(found(ed|ing|er)|establish(ed|ment)|formed|set up|created)\b",
                   ("renamed", "relocated", "incorporated", "dissolved", "opened")),
    "renamed":    (r"\brenamed\b|\boriginal name\b|\bformerly\b", r"\brenamed\b|\boriginally (called|named|known)\b|\bformerly\b", ("founded",)),
    "relocated":  (r"\brelocat|\bmoved\b", r"\brelocat|\bmoved\b", ("founded",)),
    "incorporated": (r"\bincorporat", r"\bincorporat", ("founded",)),
    "dissolved":  (r"\bdissolv|\bdefunct\b|\bclosed\b", r"\bdissolv|\bdefunct\b|\bclosed\b|\bshut down\b", ("founded", "opened")),
    "opened":     (r"\binaugurat|\bopened\b|\bopening\b", r"\binaugurat|\bopened\b|\bopening\b", ("founded", "construction", "announced", "dissolved")),
    "construction": (r"\bconstruct|\bbuilt\b|\berected\b", r"\bconstruct|\bbuilt\b|\berected\b|\bcompleted\b", ("opened",)),
    "released":   (r"\b(released?|launch(ed)?|came out|come out|premiered?|published|debuted|aired)\b",
                   r"\b(release[ds]?|launch(ed|es)?|came out|premiered?|published|debuted|aired|issued)\b", ("announced", "certified", "recorded")),
    "announced":  (r"\b(announc|introduc|reveal|unveil|roll(ed)? out)\w*", r"\b(announc|introduc|reveal|unveil|roll(ed)? out)\w*", ("released",)),
    "recorded":   (r"\brecorded\b", r"\brecord(ed|ing)\b", ("released",)),
    "certified":  (r"\bcertif", r"\bcertif", ("released",)),
    "award":      (r"\b(receiv\w*|won|win|wins|awarded|conferred|honou?red|invested|medal\w*|prize|award\w*|recipient|laureate)\b",
                   r"\b(award\w*|prize|medal\w*|received|won|conferred|honou?r\w*|recipient|laureate|invested)\b", ("nominated", "shortlisted")),
    "nominated":  (r"\bnominat", r"\bnominat", ("award", "appointed", "elected")),
    "shortlisted": (r"\bshortlist|\bfinalist\b", r"\bshortlist|\bfinalist\b", ("award",)),
    "elected":    (r"\belect(ed|ion)?\b", r"\belect(ed|ion|s)?\b", ("nominated", "appointed", "defeated")),
    "defeated":   (r"\bdefeat|\blost\b|\blose\b", r"\bdefeat|\blost\b|\blosing\b", ("elected",)),
    "appointed":  (r"\b(appointed|sworn in|took office|served as|became)\b", r"\b(appointed|sworn in|took office|served as|became|named)\b",
                   ("nominated", "elected", "resigned")),
    "resigned":   (r"\bresign|\bstepped down\b|\bleft office\b", r"\bresign|\bstepped down\b|\bleft office\b", ("appointed",)),
    "educated":   (r"\b(graduat\w*|attend\w*|stud(y|ied)|degree|B\.?\s?A\.?|B\.?\s?S\.?|Ph\.?\s?D|master'?s|bachelor'?s|alma mater)\b",
                   r"\b(graduat\w*|attend\w*|stud(y|ied|ying)|degree|educated|enroll?ed|alumn\w*|B\.?\s?A\.?|B\.?\s?S\.?|Ph\.?\s?D|master'?s|bachelor'?s)\b",
                   ("taught", "worked")),
    "taught":     (r"\btaught\b|\bprofessor\b|\blectur", r"\btaught\b|\bprofessor\b|\blectur|\bfaculty\b", ("educated",)),
    "worked":     (r"\bworked\b|\bemployed\b", r"\bworked\b|\bemployed\b|\bjoined\b", ("educated", "invented")),
    "invented":   (r"\binvent|\bdiscover|\bdevelop", r"\binvent|\bdiscover|\bdevelop|\bpatent", ("worked",)),
    "joined":     (r"\bjoin(ed|s)?\b", r"\bjoin(ed|s)?\b|\bsigned\b", ("left",)),
    "left":       (r"\bleft\b|\bdeparted\b|\bquit\b", r"\bleft\b|\bdeparted\b|\bquit\b", ("joined",)),
    "debut":      (r"\bdebut", r"\bdebut", ()),
    "children":   (r"\bhow many (children|sons|daughters|kids)\b", r"\b(child(ren)?|sons?|daughters?|kids)\b", ()),
    "dissertation": (r"\bdissertation\b|\bthesis\b", r"\bdissertation\b|\bthesis\b", ()),
    "preceded":   (r"\bprecede|\bpredecessor\b", r"\bprecede|\bpredecessor\b|\bsucceeded\b", ("succeeded",)),
    "succeeded":  (r"\bsucceed|\bsuccessor\b", r"\bsucceed|\bsuccessor\b|\bpreceded\b", ("preceded",)),
    "height":     (r"\bheight\b|\btall\b|\bhigh\b(?! school)", r"\bheight\b|\btall\b|\bhigh\b(?! school)",("width", "length", "elevation")),
    "width":      (r"\bwidth\b|\bwide\b", r"\bwidth\b|\bwide\b", ("height", "length")),
    "length":     (r"\blength\b|\blong\b", r"\blength\b|\blong\b", ("height", "width")),
    "elevation":  (r"\belevation\b|\babove sea level\b|\baltitude\b", r"\belevation\b|\babove sea level\b|\baltitude\b", ("height",)),
    "population": (r"\bpopulation\b|\binhabitants\b", r"\bpopulation\b|\binhabitants\b|\bresidents\b", ()),
    "weight":     (r"\bweigh(t|s|ed)?\b", r"\bweigh(t|s|ed)?\b", ()),
}
CQ = {k: re.compile(v[0], re.I) for k, v in REL.items()}
CS = {k: re.compile(v[1], re.I) for k, v in REL.items()}
# A question pattern may legitimately mention a competitor as context ("first elected"), so precedence resolves known pairs.
PREFER = [("nominated", "award"), ("nominated", "appointed"), ("elected", "award"), ("children", "born"), ("dissertation", "educated"),
          ("certified", "award"), ("certified", "released"), ("debut", "released"), ("debut", "joined"), ("population", "award"),
          ("educated", "award"), ("educated", "taught"), ("award", "taught"), ("length", "renamed"), ("award", "renamed"),
          ("joined", "founded"), ("married", "taught")]


def question_relation(q):
    """M_Q: the single relation family the question asks about, or None (fail-closed)."""
    hits = {k for k, c in CQ.items() if c.search(q)}
    for a, b in PREFER:
        if a in hits:
            hits.discard(b)
    return next(iter(hits)) if len(hits) == 1 else None


def sentence_of(text, i, j):
    a = max(text.rfind(". ", 0, i), text.rfind("\n", 0, i))
    b = min([x for x in (text.find(". ", j), text.find("\n", j)) if x >= 0] or [len(text)])
    return a + 1 if a >= 0 else 0, b


def sentence_confirms(r, text, i, j):
    """M_S: True if the sentence holding text[i:j] has a trigger of r and no competitor trigger is nearer to the span."""
    a, b = sentence_of(text, i, j)
    s = text[a:b]
    mid = (i + j) / 2 - a

    def dist(rel):
        d = [min(abs(m.start() - mid), abs(m.end() - mid)) for m in CS[rel].finditer(s)]
        return min(d) if d else None
    dr = dist(r)
    if dr is None:
        return False
    for c in REL[r][2]:
        dc = dist(c)
        if dc is not None and dc < dr:
            return False
    return True


ORD = re.compile(r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|last|final|\d+(?:st|nd|rd|th)|inaugural|original)\b", re.I)
YEAR = re.compile(r"\b(1[5-9]\d\d|20\d\d)\b")


def qualifiers_ok(q, answer, text, i, j, window=400):
    """Qualifier part of D3: every ordinal and every year named in the question (other than the answer itself) must occur
    in the span's sentence (ordinals) or within +-window characters of the span (years)."""
    a, b = sentence_of(text, i, j)
    sent = text[a:b].lower()
    near = text[max(0, i - window):j + window]
    for m in ORD.finditer(q):
        w = m.group(0).lower()
        if w not in sent and not (w == "first" and re.search(r"\b(1st|inaugural|founding)\b", sent)):
            return False
    for y in set(YEAR.findall(q)):
        if y not in str(answer) and y not in near:
            return False
    return True
