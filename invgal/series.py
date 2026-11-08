"""Exact compressed Molien sums for natural and regular permutation representations."""

from math import comb

from .backends import InvariantError, gap_compute, positive_int


def molien_series(group, *, representation="natural", max_degree=6, gap="gap", timeout=300):
    """Exact Molien sum for the natural permutation or regular representation.

    A compressed sum of rational functions remains practical for the regular
    representation of M23; its polynomial denominator is not expanded.
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
