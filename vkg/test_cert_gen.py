"""Unit tests for the constraint logic of vkg/cert_gen.py (no model). python -B -m vkg.test_cert_gen"""
from .cert_gen import norm, step_valid, verify

P = "Marie Dubois was born in Lyon in 1921 and died in 1999. She won the Prix Lavoisier on June 14, 1962."
PN = norm(P)


def main():
    assert step_valid("", " Lyon", PN) == ("cont", "Lyon")
    assert step_valid("Lyon", '"', PN) == ("close", "Lyon")
    assert step_valid("Lyon", '",', PN) == ("close", "Lyon")
    assert step_valid("", " Paris", PN) is None
    assert step_valid("June", " 14", PN) == ("cont", "June 14")
    assert step_valid("June 14", ",", PN) == ("cont", "June 14,")
    assert step_valid("June 14", " 1963", PN) is None
    assert step_valid("", '"', PN) is None                      # empty answer cannot close
    assert step_valid("", "19", PN, numeric=True) == ("cont", "19")
    assert step_valid("19", "21", PN, numeric=True) == ("cont", "1921")
    assert step_valid("", "Lyon", PN, numeric=True) is None      # numbers only in compute mode
    assert step_valid("marie", " dubois", PN) == ("cont", "marie dubois")   # case-insensitive copy
    assert verify({"mode": "span", "answer": "June 14, 1962"}, P)
    assert not verify({"mode": "span", "answer": "June 15, 1962"}, P)
    assert verify({"mode": "compute", "a": "1999", "b": "1921", "op": "subtract", "answer": "78"}, P)
    assert not verify({"mode": "compute", "a": "1999", "b": "1921", "op": "subtract", "answer": "77"}, P)
    assert not verify({"mode": "compute", "a": "2000", "b": "1921", "op": "subtract", "answer": "79"}, P)
    assert verify({"mode": "unknown", "answer": ""}, P)
    print("all cert_gen constraint tests pass")


if __name__ == "__main__":
    main()
