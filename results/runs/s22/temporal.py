"""S22 design (DEV): question-only time-sensitivity rule. A question is time-sensitive when its answer can change after the
question was written and it carries no explicit time anchor. Such questions get no Verified answer from a fixed snapshot;
the system outputs Qualified ("as of <snapshot date>") or Unresolved instead.
Motivation disclosed: the idea came from reading S21 Mintaka TEST errors after unsealing (stale gold); the rule is written and
tuned on DEV only and must be tested on a new sealed set."""
import re

ANCHOR = re.compile(r"\b(as of|in|by|during|before|after|until|between|from)\s+(the\s+)?(\w+\s+)?(1[5-9]\d\d|20\d\d)s?\b|\b(1[5-9]\d\d|20\d\d)\b", re.I)
PATTERNS = [
    r"\b(current|currently|presently|nowadays|now|today|still|incumbent|reigning|defending)\b",
    r"\b(most recent|latest|newest)\b",
    r"^\s*(who|what)\s+(is|are)\s+(the\s+)?(\w+\s+){0,2}(president|prime minister|premier|chancellor|governor|mayor|king|queen|monarch|"
    r"pope|ceo|chief executive|chairman|chair|head coach|coach|manager|captain|leader|owner|secretary|speaker|senator|director general|"
    r"emperor|champion|holder|record holder)\b",
    r"\bhow many\b(?!.*\b(did|was|were|had)\b).*\b(has|have|does|do|are there|is there)\b",
    r"\bhow many\b(?!.*\b(did|was|were|had)\b).*\b(won|win|wins|titles|championships|grammys|oscars|awards|medals|goals|points|albums|"
    r"films|movies|games|books|seasons|episodes|times)\b",
    r"\b(record|all[- ]time|career|in history|ever)\b.*\b(most|highest|lowest|longest|fewest|largest|record)\b|\b(most|highest|longest|fewest)\b.*\b(all[- ]time|career|ever|in history|record)\b",
    r"\bholds? the record\b",
]
PAT = [re.compile(p, re.I) for p in PATTERNS]


PAT[0] = re.compile(PATTERNS[0])          # case-sensitive: "Today Show" or "Now" in a title is not a time word
QUOTED = re.compile(r"[\"“”][^\"“”]*[\"“”]")


def time_sensitive(q):
    q = QUOTED.sub(" ", q)                # quoted titles and patch notes are not part of the question's time frame
    if ANCHOR.search(q):
        return False
    return any(p.search(q) for p in PAT)
