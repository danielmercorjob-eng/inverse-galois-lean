"""Five finite-group invariants computed with Python and GAP/HAP, without Sage.

All calculations use the same verified permutation generators as the original
inverse-Galois generator. Run with --list for the five available invariants.
"""

import argparse
import json
from pathlib import Path

from .backends import InvariantError, abelian_group, gap_compute, positive_int
from .cohomology import compute_cohomology
from .group import GROUPS_DIR, load_groups
from .series import molien_series


def schur_multiplier(group, *, gap="gap", timeout=300):
    """Invariant factors of H_2(G,Z), which is not H^2(G,Z)."""
    return abelian_group(gap_compute(group, "schur_multiplier", gap=gap, timeout=timeout))


def bogomolov_multiplier(group, *, gap="gap", timeout=300):
    """Abstract invariant factors of B0(G), not chosen cohomology classes.

    HAP computes the homological dual version, with the same abstract invariant
    factors. Abelian and simple groups use their vanishing theorems.
    """
    return abelian_group(gap_compute(group, "bogomolov_multiplier", gap=gap, timeout=timeout))


def mckay_quiver(group, *, representation="natural", gap="gap", timeout=300):
    """Rows i, columns j give dim Hom_G(rho_j,V tensor rho_i).

    V is the group's natural permutation representation or its regular
    representation. Character values are exact GAP cyclotomic strings.
    unit_index identifies the trivial vertex; it need not be vertex zero.
    """
    if representation not in ("natural", "regular"):
        raise ValueError("representation must be natural or regular")
    data = gap_compute(group, "mckay", representation=representation,
                       gap=gap, timeout=timeout)
    data["character_value_format"] = "exact GAP cyclotomics, E(n)=exp(2*pi*i/n)"
    return data


INVARIANTS = {
    "betti": "Finite-field Betti numbers through an inclusive degree bound",
    "schur_multiplier": "Second integral homology, as abelian invariant factors",
    "bogomolov_multiplier": "Bogomolov multiplier, as abelian invariant factors",
    "molien": "Full compressed Molien series and an exact coefficient prefix",
    "mckay": "McKay arrow multiplicities and irreducible character data",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--groups", nargs="+")
    parser.add_argument("--groups-dir", type=Path, default=GROUPS_DIR)
    parser.add_argument("--invariants", nargs="+", choices=INVARIANTS)
    parser.add_argument("--p", type=int, help="prime for Betti numbers")
    parser.add_argument("--max-degree", type=int, default=4)
    parser.add_argument("--representation", choices=("natural", "regular"), default="natural")
    parser.add_argument("--gap", default="gap")
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    if args.list:
        for name, description in INVARIANTS.items():
            print(f"{name:24} {description}")
        return
    if not args.invariants:
        parser.error("select one or more --invariants (or use --list)")
    if "betti" in args.invariants and args.p is None:
        parser.error("--p is required for Betti numbers")
    try:
        positive_int(args.max_degree, "max_degree", 0)
        for group in load_groups(args.groups, args.groups_dir):
            backend = dict(gap=args.gap, timeout=args.timeout)
            for name in args.invariants:
                if name == "betti":
                    result = compute_cohomology(group, args.p, args.max_degree, **backend).to_dict()
                elif name == "molien":
                    result = molien_series(group, representation=args.representation,
                                           max_degree=args.max_degree, **backend)
                elif name == "mckay":
                    result = mckay_quiver(group, representation=args.representation, **backend)
                else:
                    function = {"schur_multiplier": schur_multiplier,
                                "bogomolov_multiplier": bogomolov_multiplier}[name]
                    result = function(group, **backend)
                print(json.dumps(dict(group=group.name, invariant=name, result=result)), flush=True)
    except (InvariantError, ValueError, OSError) as e:
        parser.exit(1, f"error: {e}\n")


if __name__ == "__main__":
    main()
