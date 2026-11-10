"""One-off: make the tool and README say that rule R failed on the Mintaka set."""
from pathlib import Path
ROOT = Path(r"F:\Projects\AI hallucinations")
core = ROOT / "tool/qoq_core.py"; c = core.read_text(encoding="utf-8")
old = "    quote_checked = False\n    import qoq_extra as X\n"
new = "    quote_checked = False\n    quote_rule = None\n    import qoq_extra as X\n"
assert old in c; c = c.replace(old, new, 1)
old = "        doc, quote, sha, quote_checked = w[\"doc\"], w[\"quote\"], w[\"sha\"], True\n"
new = "        doc, quote, sha, quote_checked = w[\"doc\"], w[\"quote\"], w[\"sha\"], True\n        quote_rule = \"W1\" if X.relation_of(question) else \"R\"      # R held on SimpleQA-style questions (1.0% misleading) and failed on natural Mintaka questions (24%)\n"
assert old in c; c = c.replace(old, new, 1)
old = "\"quote_checked\": quote_checked, "
assert old in c; c = c.replace(old, "\"quote_checked\": quote_checked, \"quote_rule\": quote_rule, ", 1)
core.write_text(c, encoding="utf-8")

r = ROOT / "tool/README.md"; s = r.read_text(encoding="utf-8")
old = "measured on open questions as 1.0% misleading among kept, at the price of withholding 35% (section 5.14)"
assert old in s
s = s.replace(old, "measured as 1.0% misleading among kept on SimpleQA-style questions at the price of withholding 35%, and as 24% misleading on natural Mintaka questions, where it failed (section 5.14); the result carries `quote_rule: R` so that a caller can treat it as less reliable than `W1`", 1)
r.write_text(s, encoding="utf-8")

# the release README is kept in the release folder
rr = Path(r"F:\Projects\quote-or-quiet\README.md"); x = rr.read_text(encoding="utf-8")
x = x.replace("| biographies written by a 4B model | claims verified against the subject's own page (rule W4) |", "| biographies written by Phi-4 (14B) | claims verified against the subject's own page (rule W4) |", 1)
old = "| open questions, no relation frames (rule R) | sentence quote, question numbers present, quote-only judge with a swapped-answer control | 1.0% misleading (3.7%) against 11.3% for the displayed quote; withholds 35% of the releases |"
assert old in x
x = x.replace(old, "| open questions, no relation frames (rule R) | sentence quote, question numbers present, quote-only judge with a swapped-answer control | SimpleQA-style: 1.0% misleading (3.7%) against 11.3% for the displayed quote, withholds 35%. Natural Mintaka questions: failed, 24.0% misleading (30.6%) against 43.0% displayed; a small judge trained on reviewer labels gave 5.2% (10.0%) there |", 1)
old = "| a small judge | 0.6B model trained on 4,595 reviewer labels | AUROC 0.988 on held-out questions; 2.6% not 'states' among accepted against 8.8% for the prompted 4B judge |"
assert old in x
x = x.replace(old, "| a small judge | 0.6B model trained on 4,595 reviewer labels | AUROC 0.988 on held-out questions; 2.6% not 'states' among accepted against 8.8% for the prompted 4B judge; AUROC 0.897 on the Mintaka rows it never saw |", 1)
rr.write_text(x, encoding="utf-8")
print("ok")
