"""Tests for vkg/l3_verify.py. Run: python -B -m vkg.test_l3_verify
1. Unit tests of N, T, G and each verifier check (V1-V3), including adversarial inputs.
2. Property tests (randomised, seeded): for random documents, questions, answers and spans,
   (P1) every release returned by the gate F re-verifies as accepted, and its span normalises to the answer;
   (P2) the verifier rejects any tampered record (changed hash, shifted span, changed answer, unknown document);
   (P3) N is idempotent;
   (P4) V never accepts when the span text is absent from the document."""
import random
import string

from . import l3_verify as L

DOCS = {
    "Reita Faria": "Reita Faria Powell (born 23 August 1943) is an Indian physician and the winner of Miss World 1966. "
                   "Population was 1,234,567 in 2011. She married David Powell in 1971.",
    "Lemaitre": "Georges Lemaître published the paper in 1931. A French translation appeared on 5 March 1933.",
}
get = lambda t: DOCS.get(t, "")


def rec(doc, a, frag, occurrence=0):
    text = DOCS[doc]
    i = -1
    for _ in range(occurrence + 1):
        i = text.index(frag, i + 1)
    return {"answer": a, "doc": doc, "doc_sha256": L.doc_hash(text), "start": i, "end": i + len(frag)}


def unit():
    assert L.N("  1,234,567 ") == "1234567" and L.N("Doki–Doki") == "doki-doki" and L.N("“Hello.”") == "hello"
    assert L.T("In what year did X win?") == "YEAR"
    assert L.T("What day, month, and year was X born?") == "DATE_DMY"
    assert L.T("In what month and year did X happen?") == "MONTH_YEAR"
    assert L.T("How many people live in X?") == "NUMBER"
    assert L.T("Who won Miss World 1966?") == "NAME"
    assert L.T("What is the capital of X?") == "ANY"
    for s, t in (("23 August 1943", "DATE_DMY"), ("August 23, 1943", "DATE_DMY"), ("1943-08-23", "DATE_DMY"),
                 ("August 1943", "MONTH_YEAR"), ("1966", "YEAR"), ("1,234,567", "NUMBER"), ("12.5 km", "NUMBER"),
                 ("David Powell", "NAME"), ("Ludwig van Beethoven", "NAME")):
        assert L.type_ok(s, t), (s, t)
    for s, t in (("August 1943", "DATE_DMY"), ("1943", "DATE_DMY"), ("19433", "YEAR"), ("about 1966", "YEAR"),
                 ("twelve", "NUMBER"), ("david powell", "NAME"), ("1966", "NAME")):
        assert not L.type_ok(s, t), (s, t)
    q = "In what year did Reita Faria win Miss World?"
    ok, why = L.verify(q, rec("Reita Faria", "1966", "1966"), get)
    assert ok, why
    assert not L.verify(q, {**rec("Reita Faria", "1966", "1966"), "doc": "Nope"}, get)[0]                      # V1 unknown doc
    assert not L.verify(q, {**rec("Reita Faria", "1966", "1966"), "doc_sha256": "0" * 64}, get)[0]             # V1 hash
    assert not L.verify(q, rec("Reita Faria", "1965", "1966"), get)[0]                                         # V2 answer != span
    assert not L.verify(q, {**rec("Reita Faria", "1966", "1966"), "end": 10**9}, get)[0]                       # V2 range
    assert not L.verify(q, rec("Reita Faria", "1943", "1943"), get)[1].startswith("accepted (NAME")            # sanity
    assert not L.verify("Who married Reita Faria?", rec("Reita Faria", "1971", "1971"), get)[0]                # V3 type
    assert L.verify("How many people lived there in 2011?", rec("Reita Faria", "1234567", "1,234,567"), get)[0]  # N on numbers
    assert not L.verify(q, {"answer": "1966"}, get)[0]                                                         # malformed
    a, r = L.release("What day, month, and year was Reita Faria born?", "23 August 1943", ["Reita Faria"], get)
    assert a == "23 August 1943" and r["span"] == "23 August 1943"
    a, r = L.release("What day, month, and year was Reita Faria born?", "August 1943", ["Reita Faria"], get)
    assert a is None                                                                                           # incomplete date refused
    a, r = L.release("In what year was the French translation published?", "1932", ["Lemaitre"], get)
    assert a is None                                                                                           # not in source
    assert L.years("2018–19 UEFA Champions League") == {2018, 2019} and L.years("1999") == {1999} and L.years("no year") == set()
    assert L.years("2025–26 UEFA Youth League") == {2025, 2026} and L.years("Solar eclipse of September 8, 1801") == {1801}
    DOCS["2012 UEFA Champions League final"] = "Bayern had 4 shots on target in the final."
    y = rec("2012 UEFA Champions League final", "4", "4")
    assert not L.verify("How many shots on target did Inter have in the 2010 final?", y, get)[0]                # V4
    assert L.verify("How many shots on target did Bayern have in the 2012 final?", y, get)[0]
    DOCS["Castle"] = "The castle had 2.1 million visitors and exactly 2,111,578 in 2018."
    assert L.T("What is the exact number of visitors in 2018?") == "NUMBER_EXACT"
    assert not L.verify("What is the exact number of visitors in 2018?", rec("Castle", "2.1 million", "2.1 million"), get)[0]
    assert L.verify("What is the exact number of visitors in 2018?", rec("Castle", "2111578", "2,111,578"), get)[0]
    return "unit ok"


def props(n=3000, seed=0):
    rng = random.Random(seed)
    words = ["alpha", "Beta", "1999", "2,500", "March", "12", "Gamma", "of", "the", "Delta", "3.5", "km", "23", "August"]
    qs = ["In what year was it?", "How many were there?", "Who was it?", "What day, month, and year was it?", "What is it?"]
    released = 0
    for _ in range(n):
        doc = " ".join(rng.choice(words) for _ in range(rng.randint(5, 40)))
        DOCS["_r"] = doc
        q = rng.choice(qs)
        k = rng.randint(1, 4)
        st = rng.randint(0, max(0, len(doc.split()) - k))
        ans = " ".join(doc.split()[st:st + k]) if rng.random() < 0.7 else "".join(rng.choice(string.ascii_letters) for _ in range(5))
        a, r = L.release(q, ans, ["_r"], get)
        assert L.N(L.N(ans)) == L.N(ans)                                                                       # P3
        if a is not None:
            released += 1
            ok, _ = L.verify(q, r, get)
            assert ok and L.N(doc[r["start"]:r["end"]]) == L.N(a)                                              # P1
            for bad in ({**r, "doc_sha256": "f" * 64}, {**r, "start": r["start"] + 1}, {**r, "answer": a + "x"}, {**r, "doc": "_missing"}):
                assert not L.verify(q, bad, get)[0]                                                            # P2
        if L.N(ans) and L.N(ans) not in L.N(doc):
            assert a is None                                                                                   # P4
    DOCS.pop("_r", None)
    return f"properties ok over {n} random cases ({released} releases re-verified)"


if __name__ == "__main__":
    print(unit())
    print(props())
