"""W4 value-coverage helper, copied from f5_sheet.py (unchanged)."""
import re, unicodedata
STOP = set("a an the of in on at to for from by with and or but is are was were be been being he she it they his her their its this that these those as has have had not no also which who whom whose when where what how into than then there here after before during over under about between".split())
def _fold(x): return "".join(ch for ch in unicodedata.normalize("NFKD", x) if not unicodedata.combining(ch)).casefold()
def cw(x): return {w for w in re.findall(r"[a-z0-9]+", _fold(x)) if w not in STOP and len(w) > 2}
def cov(val, q):
    vw = cw(val); return len(vw & cw(q)) / max(1, len(vw))
