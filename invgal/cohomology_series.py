"""Full cohomology series for cyclic Sylow subgroups and abelian groups."""

from .backends import InvariantError, checked_perms, gap_compute
from .cohomology import _is_prime
from .series import RationalSeries, mul


def check_prime(p):
    if type(p) is not int or not _is_prime(p):
        raise ValueError("p must be a prime integer")


def hilbert_poincare_series(group, p, *, gap="gap", timeout=300):
    """The full series sum dim H^n(G,Fp) t^n, with trivial coefficients.

    The function uses full formulas. It does not infer a rational function
    from a coefficient list with a degree limit.
    """
    check_prime(p)
    checked_perms(group)
    if group.order % p:
        return RationalSeries((1,), (1,))
    data = gap_compute(group, "cyclic_sylow", p=p, gap=gap, timeout=timeout)
    if data["cyclic"]:
        if p == 2 and data["order"] == 2:
            return RationalSeries((1,), (1, -1))
        e = data["automizer"]
        return RationalSeries(tuple([1] + [0]*(2*e-2) + [1]),
                              tuple([1] + [0]*(2*e-1) + [-1]))
    data = gap_compute(group, "abelian_structure", p=p, gap=gap, timeout=timeout)
    if not data["abelian"]:
        raise InvariantError("no full-series formula for this group and prime")
    numerator, denominator = [1], [1]
    for order in data["orders"]:
        if p == 2 and order == 2:
            denominator = mul(denominator, [1, -1])
        else:
            numerator = mul(numerator, [1, 1])
            denominator = mul(denominator, [1, 0, -1])
    return RationalSeries(tuple(numerator), tuple(denominator))
