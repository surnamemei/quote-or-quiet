"""Torch-free access to the frozen prompt templates and the answer parser, for code that drives the pod from this machine.
The templates are read from the frozen source files (vkg/s6b_run.py, vkg/s11_run.py) with ast, so they cannot drift;
parse() is a copy of vkg.probe_gen.parse, checked equal to the original's source text at import."""
import ast
import inspect
import re
from pathlib import Path

_V = Path(__file__).resolve().parent


def _const(fname, name):
    for node in ast.parse((_V / fname).read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)


PLAIN = _const("s6b_run.py", "PLAIN")
CAUTIOUS = _const("s6b_run.py", "CAUTIOUS")
QPROMPT = _const("s11_run.py", "QPROMPT")


def parse(raw):
    m = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', raw)
    return (m.group(1) if m else raw.strip().split("\n")[0])[:200]


assert inspect.getsource(parse) in (_V / "probe_gen.py").read_text(encoding="utf-8"), "parse() drifted from vkg/probe_gen.py"
