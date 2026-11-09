"""Quote or Quiet MCP server (runs in the free-search-mcp environment, which has the MCP SDK 2.x).
Tool quote_or_quiet(question): searches the web with the free-search-mcp pool (the same pool as the S29 sealed run), stores the URL list
where the pipeline reads it, and asks the local Quote or Quiet service (tool/qoq_service.py) for a Verified answer with its quote, or
Unresolved with the reason. The answer is never produced here.
Run (stdio): F:/Projects/tools/fsm_venv/Scripts/python.exe -I "F:/Projects/AI hallucinations/tool/qoq_mcp.py" """
import hashlib
import json
import os
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from mcp.server.mcpserver import MCPServer
from search_mcp import server as fsm

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results" / "cache" / "web_fsm"
SERVICE = os.environ.get("QOQ_SERVICE", "http://127.0.0.1:18100")
BLOCK = ("huggingface.co", "github.com", "githubusercontent.com", "gitlab.com", "kaggle.com", "arxiv.org", "paperswithcode.com",
         "openai.com", "openreview.net", "aclanthology.org", "semanticscholar.org", "researchgate.net", "scale.com", "llm-stats.com")

mcp = MCPServer(name="quote-or-quiet", instructions=(
    "Use quote_or_quiet for short factual questions (who, when, where, how many). It returns either a Verified answer with a verbatim "
    "quote from a pinned Wikipedia page, or Unresolved. Report Verified answers with their quote and source; for Unresolved, say that "
    "no verified answer was found instead of guessing."))


def _blocked(u):
    h = urlparse(u).netloc.lower()
    return any(h == b or h.endswith("." + b) for b in BLOCK)


async def _search(question):
    f = CACHE / f"s_{hashlib.sha256(question.encode('utf-8')).hexdigest()}.json"
    if f.exists():
        return
    res = await fsm.search(question, max_results=10, use_cache=False, format="json")
    urls = []
    for r in res.get("results", []):
        u = r.get("url", "")
        if u.startswith("http") and not _blocked(u) and u not in urls:
            urls.append(u)
    if urls:
        CACHE.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(urls[:8]), encoding="utf-8")


def _format(r):
    if r.get("status") == "Verified":
        return (f"Verified: {r['answer']}\nQuote: \"{r['quote']}\"\nSource: {r['source_title']} ({r['source_url']}), {r['snapshot']}, "
                f"page sha256 {r['page_sha256'][:12]}...\nSupport: all 3 evidence sources and a second reader agree.")
    return f"Unresolved: {r.get('reason', 'no verified answer')}." + (f" (Unverified candidate, do not state as fact: {r['candidate']})" if r.get("candidate") else "")


@mcp.tool(description="Answer a short factual question only if the answer can be quoted verbatim from a pinned Wikipedia page and is "
                      "supported by web, local Wikipedia and combined evidence plus a second reader. Otherwise returns Unresolved. "
                      "Slow (tens of seconds); use for facts that matter.")
async def quote_or_quiet(question: str) -> str:
    question = question.strip()
    if not question:
        return "Unresolved: empty question."
    try:
        await _search(question)
    except Exception as ex:                      # search failure: the pipeline falls back to DuckDuckGo
        pass
    req = urllib.request.Request(f"{SERVICE}/answer", data=json.dumps({"question": question}).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            r = json.loads(resp.read().decode("utf-8"))
    except Exception as ex:
        return f"Unresolved: the local Quote or Quiet service is not reachable at {SERVICE} ({type(ex).__name__}). Start tool/start_service.sh."
    return _format(r) + "\n\n" + json.dumps({k: v for k, v in r.items() if k not in ("readers",)}, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
