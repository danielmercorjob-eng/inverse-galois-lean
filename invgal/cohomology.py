"""Finite-field Betti numbers with trivial coefficients, using GAP/HAP.

The resolution is built on a Sylow subgroup and fusion relations are imposed
in the full group. Both the prime and the inclusive degree bound can vary.
"""

import argparse
import math
import json
from dataclasses import dataclass

from .backends import InvariantError, checked_perms, gap_compute, positive_int
from .group import GROUPS_DIR, GroupSpec, load_groups


@dataclass(frozen=True)
class CohomologyResult:
    group: str
    order: int
    p: int
    betti_numbers: tuple

    @property
    def max_degree(self):
        return len(self.betti_numbers) - 1

    def to_dict(self):
        return dict(group=self.group, order=self.order, p=self.p,
                    max_degree=self.max_degree, betti_numbers=list(self.betti_numbers))


def _is_prime(p):
    if p < 2:
        return False
    if p % 2 == 0:
        return p == 2
    return all(p % d for d in range(3, math.isqrt(p) + 1, 2))


def compute_cohomology(group: GroupSpec, p: int, max_degree: int, *,
                       gap="gap", timeout=300) -> CohomologyResult:
    """Return dim H^n(G,F_p) for n=0,...,max_degree, with trivial action.

    GAP is unnecessary in coprime characteristic or for degree zero. Group
    generators are verified even for these shortcuts. Backend failure or a
    timeout raises InvariantError; uncomputed dimensions are never filled in.
    """
    if type(p) is not int or not _is_prime(p):
        raise ValueError("p must be a prime integer")
    positive_int(max_degree, "max_degree", 0)
    if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be positive and finite")
    checked_perms(group)
    if max_degree == 0 or group.order % p:
        values = [1] + [0] * max_degree
    else:
        values = gap_compute(group, "betti", p=p, max_degree=max_degree,
                             gap=gap, timeout=timeout)
        if (not isinstance(values, list) or len(values) != max_degree + 1
                or any(type(x) is not int or x < 0 for x in values) or values[0] != 1):
            raise InvariantError("GAP returned an incomplete or invalid Betti sequence")
    return CohomologyResult(group.name, group.order, p, tuple(values))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groups", nargs="+")
    parser.add_argument("--groups-dir", default=str(GROUPS_DIR))
    parser.add_argument("--p", required=True, type=int)
    parser.add_argument("--max-degree", required=True, type=int)
    parser.add_argument("--gap", default="gap")
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    try:
        for group in load_groups(args.groups, args.groups_dir):
            result = compute_cohomology(group, args.p, args.max_degree,
                                        gap=args.gap, timeout=args.timeout)
            print(json.dumps(result.to_dict()), flush=True)
    except (ValueError, InvariantError, OSError) as e:
        parser.exit(1, f"error: {e}\n")


if __name__ == "__main__":
    main()
