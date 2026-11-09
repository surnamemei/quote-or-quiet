"""Import before any vkg module in analysis scripts that only need agree / g6 / cand: stands in for vkg.retrieval2, whose import
unpickles results/cache/emb.pkl (~38 GB in RAM). Any attribute access raises, so nothing can silently depend on it.
(Cause found by the Kimi session, 2026-11-07.) Never used by frozen S19 code paths."""
import sys
import types


class _Stub(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        raise RuntimeError(f"vkg.retrieval2.{name} used, but retrieval2 is stubbed out in this analysis")


sys.modules.setdefault("vkg.retrieval2", _Stub("vkg.retrieval2"))
