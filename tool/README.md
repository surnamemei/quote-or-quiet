# Quote or Quiet as an MCP tool

Give any local model (or Claude Code, or any MCP client) a fact-checking tool that answers a short factual question only when it can quote the answer, and otherwise says so.

Real output from the end-to-end test (2026-11-10: an MCP client over stdio, the service on this machine, public PopQA and Mintaka questions):

```
quote_or_quiet("What is the distance between bases on a baseball diamond?")
-> Verified: 90 feet
   Quote: "Thus, although the "points" of the bases are 90 feet apart, the physical distance between each successive pair of base markers is closer to 88 feet (26.8 m)."
   Source: Baseball field (https://en.wikipedia.org/wiki/Baseball_field), FineWiki, English Wikipedia, August 2025, page sha256 c12bd4d473af...
   Support: all 3 evidence sources and a second reader agree.

quote_or_quiet("Who won the most Popular TV Program Award in the first Emmy Award Show in 1949?")
-> Verified: Pantomime Quiz
   Quote: "Most Popular Television Program: Pantomime Quiz Time"
   Source: 1st Primetime Emmy Awards (https://en.wikipedia.org/wiki/1st_Primetime_Emmy_Awards), FineWiki, English Wikipedia, August 2025, page sha256 3c4b3bbf6479...
   Support: all 3 evidence sources and a second reader agree.

quote_or_quiet("Who was the composer of Happy New Year?")
-> Unresolved: only 2 of 3 evidence sources support the candidate. (Unverified candidate, do not state as fact: Vishal–Shekhar)
```

The last question is ambiguous (several works share the title), and the tool declines rather than guessing. The quote shown is a verbatim sentence from a pinned page that contains the answer and the most words of the question; the release decision itself is the deductive gate's span (returned as `span`, `gate_page` and `gate_context` in the JSON part of the reply).

It is the frozen system from the paper, one question at a time: web pages (free-search-mcp pool), local Wikipedia (FineWiki, Aug 2025) and a combined passage, read by Qwen3-4B-Instruct-2507 with two prompts each; an answer is released only if all three sources support it, it is a verbatim, type-checked span of a hash-pinned Wikipedia page, and Phi-4 confirms it. On the sealed SimpleQA-style test this answered 37% of questions with a silent-error rate whose 97.5% upper bound was 0.76%.

## What it is for and what it is not
- For: short factual questions with one answer (who, when, where, how many, which year).
- Not for: explanations, opinions, advice, multi-step reasoning, code, or anything not in Wikipedia. Those come back Unresolved.
- It answers about a third to a half of factual questions. Unresolved means "no verified answer", not "false".
- Speed: in the test the first question took 17 s with the models loaded and its pages not yet fetched; questions whose pages were already fetched took 2 to 5 s. A live web search adds several seconds (the test questions' URL lists were already cached).

## Parts
| file | runs in | role |
|---|---|---|
| `qoq_core.py` | project environment | the pipeline for one question |
| `qoq_service.py` | project environment | local HTTP service on 127.0.0.1:18100 |
| `qoq_mcp.py` | free-search-mcp environment (MCP SDK 2.x) | MCP server: web search, then asks the service |
| `start_service.sh` / `stop_service.sh` | Git Bash | start or stop the 4B server (port 18000), Ollama with Phi-4 (11540) and the service |

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


## Additions after the S42 to S47 experiments (paper sections 5.10 to 5.13)
Three changes, all in `qoq_extra.py` and wired into the service and the MCP server. They were self-tested end to end on 2026-11-10 (`tool/selftest.sh`, log in `tool/selftest.log`); that test shows the code runs, not accuracy. The accuracy figures are those of the paper's experiments, which used the same code and thresholds except where stated.

| tool | input | output | measured in the paper |
|---|---|---|---|
| `quote_or_quiet` (changed) | a short question | Verified with a quote that states the answer, or Unresolved. For the seven templated relations (birth year and place, death year, director, author, capital, head of government in a year) the quote is chosen by rule W1: the first sentence of a pinned page that passes a frame check, a subject link and a quote-only reader; if no sentence does, Unresolved. For other questions the old best-sentence quote is shown with `quote_checked: false` | 0.20% of 1,017 quotes misleading (upper bound 0.71%), coverage about 3.5 points lower (section 5.11) |
| `quote_or_quiet_bio` (new) | a person's exact page title | a list of claims, each with a sentence of the person's own page that states it; claims without one are left out | with drafts written from the page: 61% of claims kept, 1 of 400 false and 1 of 400 quotes not stating the claim (section 5.12) |
| `quote_or_quiet_readings` (new) | a name and a relation (director, birth_year, birth_place, death_year, author) | one answer per page that bears the name, each with its quote | 250 readings, none false or misleading (section 5.13) |

Differences from the tested rules, so that the paper's numbers are not claimed for them: (1) W1 here also requires the quote to be a sentence, not a table row, heading or list line (the test did not; this is stricter and its coverage cost was not measured; with it the tool returns Unresolved for 'who was the head of government of Saudi Arabia in 1933', whose only quote was a row of a list of Italian ambassadors); (2) in `bio` the swapped value of the control comes from another claim of the same biography, or a fixed value of the same type, instead of another subject's claim; (3) the Ollama port is 11540 (Windows now reserves 11437 to 11536).
Known gap: the local Wikipedia top five for a question does not always contain the person's own page (for 'In what year was Tina Fey born?' it held a list page, so the answer is Unresolved); the tool then says nothing instead of quoting a list line.
