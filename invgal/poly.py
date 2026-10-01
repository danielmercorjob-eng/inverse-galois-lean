"""Known polynomials realising a group, and the properties that the generator needs from them.

A known polynomial is given in a group file either by its integer coefficients (lowest degree
first), from which every property is computed, or by declared properties only.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import Optional


def _trim(p):
    while p and p[-1] == 0:
        p = p[:-1]
    return p


def _rem(a, b):
    a = list(a)
    while len(a) >= len(b) and a:
        q = a[-1] / b[-1]
        shift = len(a) - len(b)
        for i, c in enumerate(b):
            a[shift + i] -= q * c
        a = _trim(a)
    return a


def count_real_roots(coeffs):
    """Number of distinct real roots of the polynomial (Sturm's theorem, exact arithmetic)."""
    p = _trim([Fraction(c) for c in coeffs])
    if len(p) < 2:
        raise ValueError("polynomial must be non-constant")
    seq = [p, _trim([i * c for i, c in enumerate(p)][1:])]
    while len(seq[-1]) > 1:
        r = _rem(seq[-2], seq[-1])
        if not r:
            break
        seq.append([-c for c in r])

    def sign_changes(signs):
        signs = [s for s in signs if s != 0]
        return sum(a != b for a, b in zip(signs, signs[1:]))

    def sign(x):
        return (x > 0) - (x < 0)

    at_pos_inf = [sign(q[-1]) for q in seq]
    at_neg_inf = [sign(q[-1]) * (-1) ** (len(q) - 1) for q in seq]
    return sign_changes(at_neg_inf) - sign_changes(at_pos_inf)


def digit_count(n: int) -> int:
    return len(str(abs(n))) if n != 0 else 0


@dataclass
class KnownPolynomial:
    """What is known about one polynomial with the group as Galois group.

    `digits` is the smallest `N` such that every coefficient has fewer than `N` decimal digits.
    `root_action` records that its Galois action on the roots is the group's permutation action
    up to relabelling. A property that is `None` is unknown.
    """
    degree: Optional[int] = None
    digits: Optional[int] = None
    monic: Optional[bool] = None
    real_roots: Optional[int] = None
    root_action: bool = False
    source: str = ""
    coefficients: Optional[list] = None

    @classmethod
    def from_json(cls, d):
        d = dict(d)
        coeffs = d.get("coefficients")
        if coeffs is not None:
            coeffs = [int(c) for c in coeffs]
            if not coeffs or coeffs[-1] == 0:
                raise ValueError("coefficients must be listed lowest degree first, "
                                 "with a nonzero leading coefficient")
            computed = {
                "degree": len(coeffs) - 1,
                "digits": max(map(digit_count, coeffs)) + 1,
                "monic": coeffs[-1] == 1,
                "real_roots": count_real_roots(coeffs),
            }
            for k, val in computed.items():
                if k in d and d[k] != val:
                    raise ValueError(f"declared {k}={d[k]} but the coefficients give {val}")
            d.update(computed, coefficients=coeffs)
        return cls(**d)

    def satisfies(self, variant) -> bool:
        """Whether this polynomial witnesses `variant` (a polynomial `Variant`)."""
        if self.degree is not None and self.degree != variant.group.degree:
            return False
        if variant.digits is not None and (self.digits is None or self.digits > variant.digits):
            return False
        # Over a transitive group the polynomial is irreducible, so `monic` suffices.
        if variant.normalization != "any" and not self.monic:
            return False
        if variant.real_roots is not None and self.real_roots != variant.real_roots:
            return False
        if variant.action == "roots" and not self.root_action:
            return False
        return True
