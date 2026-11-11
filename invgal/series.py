"""Exact rational series and Molien class sums."""

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from math import comb, gcd

from .backends import InvariantError, checked_perms, gap_compute, positive_int


def trim(a):
    a = list(map(Fraction, a))
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a or [Fraction(0)]


def mul(a, b):
    out = [Fraction(0)] * (len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] += x*y
    return trim(out)


def divmod_poly(a, b):
    a, b = trim(a), trim(b)
    if b == [0]:
        raise ZeroDivisionError("zero polynomial")
    q = [Fraction(0)]*max(1, len(a)-len(b)+1)
    while a != [0] and len(a) >= len(b):
        k, c = len(a)-len(b), a[-1]/b[-1]
        q[k] = c
        for j, v in enumerate(b):
            a[k+j] -= c*v
        a = trim(a)
    return trim(q), a


@dataclass(frozen=True)
class RationalSeries:
    """A reduced rational function with P(0)=1, using ascending rational coefficients."""

    numerator: tuple
    denominator: tuple

    def __post_init__(self):
        a, b = trim(self.numerator), trim(self.denominator)
        if not b[0] or a[0] != b[0]:
            raise ValueError("series must have denominator nonzero at zero and P(0)=1")
        x, y = a, b
        while y != [0]:
            x, y = y, divmod_poly(x, y)[1]
        common = [v/x[-1] for v in x]
        a, b = divmod_poly(a, common)[0], divmod_poly(b, common)[0]
        scale = b[0]
        object.__setattr__(self, "numerator", tuple(v/scale for v in a))
        object.__setattr__(self, "denominator", tuple(v/scale for v in b))

    def coefficients(self, max_degree):
        positive_int(max_degree, "max_degree", 0)
        out = []
        for n in range(max_degree+1):
            a = self.numerator[n] if n < len(self.numerator) else 0
            out.append(a - sum(self.denominator[j]*out[n-j]
                               for j in range(1, min(n+1, len(self.denominator)))))
        return tuple(out)

    def to_dict(self):
        return {"numerator": [str(x) for x in self.numerator],
                "denominator": [str(x) for x in self.denominator],
                "coefficient_order": "increasing degree", "full_series": True}


@lru_cache(None)
def cyclotomic(n):
    """The monic cyclotomic polynomial, calculated by exact division of t^n-1."""
    out = [-1] + [0]*(n-1) + [1]
    for d in range(1, n):
        if n % d == 0:
            out, rem = divmod_poly(out, cyclotomic(d))
            if rem != [0]:
                raise ArithmeticError("cyclotomic division was not exact")
    return tuple(out)


def zeros_and_poles(group, series, *, gap="gap", timeout=300):
    """Exact zero/pole data as irreducible Q-polynomials with multiplicities.

    The factor multiplicities give all algebraic conjugates.
    The input must be a full rational function.
    """
    if not isinstance(series, RationalSeries):
        raise TypeError("supply a full RationalSeries, not a Betti prefix")
    checked_perms(group)
    data = {}
    period = 1
    for name, coefficients in (("zeros", series.numerator), ("poles", series.denominator)):
        factors = gap_compute(group, "factor_polynomial", gap=gap, timeout=timeout,
                              coefficients=coefficients) if len(coefficients) > 1 else []
        factors = [factor for factor in factors if len(factor["coefficients"]) > 1]
        for factor in factors:
            values = list(map(Fraction, factor["coefficients"]))
            normalized = tuple(x/values[0] for x in values)
            degree = len(normalized)-1
            order = None
            # phi(n) >= sqrt(n/2). This bound includes all possible orders.
            for n in range(1, max(3, 2*degree*degree+1)):
                c = cyclotomic(n)
                if normalized == tuple(x/c[0] for x in c):
                    order = n
                    break
            factor["coefficients"] = [str(x) for x in normalized]
            factor["root_of_unity_order"] = order
            if name == "poles":
                if order is None:
                    raise ValueError("a pole is not a root of unity; not a finite-group Poincare series")
                period = period*order//gcd(period, order)
        data[name] = factors
    data["least_eventual_quasipolynomial_period"] = period
    data["pole_order_at_one"] = next((f["multiplicity"] for f in data["poles"]
                                       if f["root_of_unity_order"] == 1), 0)
    data["series"] = series.to_dict()
    return data


def molien_series(group, *, representation="natural", max_degree=6, gap="gap", timeout=300):
    """Molien sum for the natural permutation or regular representation.

    The sum keeps one term for each conjugacy class.
    With this form, the program can calculate the Molien series for the regular
    representation of M23 without a large polynomial denominator.
    """
    positive_int(max_degree, "max_degree", 0)
    if representation not in ("natural", "regular"):
        raise ValueError("representation must be natural or regular")
    data = gap_compute(group, "molien", gap=gap, timeout=timeout, representation=representation)
    out = [0]*(max_degree+1)
    for term in data["terms"]:
        coeff = [1]+[0]*max_degree
        for length, count in term["cycles"]:
            new = [0]*(max_degree+1)
            for n, c in enumerate(coeff):
                for k in range((max_degree-n)//length+1):
                    new[n+k*length] += c*comb(count+k-1, k)
            coeff = new
        for n, c in enumerate(coeff):
            out[n] += term["class_size"]*c
    if any(c % data["order"] for c in out):
        raise InvariantError("Molien average did not give integral coefficients")
    return dict(data, representation=representation, full_series=True,
                formula="(1/order) * sum class_size / product (1-t^length)^count",
                dimension=group.degree if representation == "natural" else group.order,
                max_degree=max_degree, coefficients=[c//data["order"] for c in out])
