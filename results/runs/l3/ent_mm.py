import sys
sys.path.insert(0, "results/runs/l3")
src = open("results/runs/l3/ent_eval.py", encoding="utf-8").read().split("lines = [")[0].replace("parents[3]", "parents[3]").replace("Path(__file__)", "Path('F:/Projects/AI hallucinations/results/runs/l3/ent_eval.py')")
exec(src)
n = 0
for r, rel, doc, m in releases("popqa_dev"):
    it = m.get("s_wiki_title"); e, a = parse(raw[("popqa_dev", r["id"])]["raw"])
    if not matches_intended(e, it):
        n += 1
        if n <= 24: print(r["question"][:50], "|", e, "| intended:", it, "| doc:", doc)
print(n)
