# Quote or Quiet as an MCP tool

Give any local model (or Claude Code, or any MCP client) a fact-checking tool that answers a short factual question only when it can quote the answer, and otherwise says so.

Output format (illustration; real outputs from the end-to-end test will replace it):

```
quote_or_quiet("Who directed the film Rec 4: Apocalypse?")
-> Verified: Jaume Balagueró
   Quote: "[REC] 4: Apocalypse is a 2014 Spanish horror film directed by Jaume Balagueró ..."
   Source: [REC] 4: Apocalypse (https://en.wikipedia.org/wiki/...), FineWiki, English Wikipedia, August 2025, page sha256 ...
   Support: all 3 evidence sources and a second reader agree.

quote_or_quiet("<a question the sources disagree on>")
-> Unresolved: only 2 of 3 evidence sources support the candidate. (Unverified candidate, do not state as fact: ...)
```

It is the frozen system from the paper, one question at a time: web pages (free-search-mcp pool), local Wikipedia (FineWiki, Aug 2025) and a combined passage, read by Qwen3-4B-Instruct-2507 with two prompts each; an answer is released only if all three sources support it, it is a verbatim, type-checked span of a hash-pinned Wikipedia page, and Phi-4 confirms it. On the sealed SimpleQA-style test this answered 37% of questions with a silent-error rate whose 97.5% upper bound was 0.76%.

## What it is for and what it is not
- For: short factual questions with one answer (who, when, where, how many, which year).
- Not for: explanations, opinions, advice, multi-step reasoning, code, or anything not in Wikipedia. Those come back Unresolved.
- It answers about a third to a half of factual questions. Unresolved means "no verified answer", not "false".
- Each question takes tens of seconds (web search, page fetching, seven model readings).

## Parts
| file | runs in | role |
|---|---|---|
| `qoq_core.py` | project environment | the pipeline for one question |
| `qoq_service.py` | project environment | local HTTP service on 127.0.0.1:18100 |
| `qoq_mcp.py` | free-search-mcp environment (MCP SDK 2.x) | MCP server: web search, then asks the service |
| `start_service.sh` / `stop_service.sh` | Git Bash | start or stop the 4B server (port 18000), Ollama with Phi-4 (11535) and the service |

The two environments are kept apart because the MCP SDK lives in the free-search-mcp environment and the models in the project one; no extra installation is needed.

## Use
1. Start the service (needs free RAM >= 16 GB and free VRAM >= 22 GB; it refuses while another job holds the project GPU lock):
   `bash tool/start_service.sh`
2. Register the MCP server with your client. For Claude Code:
   `claude mcp add quote-or-quiet -- F:/Projects/tools/fsm_venv/Scripts/python.exe -I "F:/Projects/AI hallucinations/tool/qoq_mcp.py"`
   For clients with a JSON config (LM Studio, Cherry Studio, Claude Desktop and others):
   ```json
   {"mcpServers": {"quote-or-quiet": {"command": "F:/Projects/tools/fsm_venv/Scripts/python.exe",
     "args": ["-I", "F:/Projects/AI hallucinations/tool/qoq_mcp.py"]}}}
   ```
3. Stop it and free the GPU: `bash tool/stop_service.sh`

## Differences from the paper's runs
- The generation server's memory cap is 45% of the card here (68% in the batch runs); generation is greedy, so answers do not change, only batch size.
- Search results for a new question are fetched live; a question asked before reuses the cached URL list.
