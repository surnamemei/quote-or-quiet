"""L3 design helper: a side index of local FineWiki titles by normalised core (title without a trailing "(...)" qualifier),
so entity ambiguity can be looked up fast. Read-only on the wiki DB; writes results/runs/l3/titles.db."""
import re, sqlite3, sys, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from vkg import localwiki as LW  # noqa: E402

def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().casefold()
    return " ".join(re.sub(r"[^a-z0-9]", " ", s).split())

def split(t):
    m = re.match(r"^(.*?)\s*\(([^()]*)\)$", t)
    return (m.group(1), m.group(2)) if m else (t, "")

if __name__ == "__main__":
    import psutil
    psutil.Process().nice(psutil.IDLE_PRIORITY_CLASS)
    src = sqlite3.connect(f"file:{LW.DB}?mode=ro", uri=True)
    out_p = ROOT / "results/runs/l3/titles.db"
    out_p.unlink(missing_ok=True)
    out = sqlite3.connect(out_p)
    out.execute("CREATE TABLE t(title TEXT, core TEXT, qual TEXT, ncore TEXT, len INTEGER)")
    batch = []
    for i, (title, n) in enumerate(src.execute("SELECT title, length(text) FROM articles")):
        c, q = split(title)
        batch.append((title, c, q, norm(c), n))
        if len(batch) >= 200000:
            out.executemany("INSERT INTO t VALUES (?,?,?,?,?)", batch); batch = []
            print(i, flush=True)
    out.executemany("INSERT INTO t VALUES (?,?,?,?,?)", batch)
    out.execute("CREATE INDEX i_ncore ON t(ncore)")
    out.execute("CREATE INDEX i_title ON t(title)")
    out.commit()
    print("rows", out.execute("SELECT count(*) FROM t").fetchone()[0])
