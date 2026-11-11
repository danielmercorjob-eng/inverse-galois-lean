"""Calculate ten finite-group invariants with Python and GAP/HAP.

The program uses the permutation generators in the group files.
Use --list to see the ten invariants. Sage is not necessary.
"""

import argparse
import json
from pathlib import Path

from .backends import InvariantError, abelian_group, gap_compute, positive_int
from .cohomology import compute_cohomology
from .group import GROUPS_DIR, load_groups
from .series import molien_series, zeros_and_poles
from .cohomology_series import hilbert_poincare_series
from .detection import detection_kernel


def schur_multiplier(group, *, gap="gap", timeout=300):
    """Invariant factors of H_2(G,Z), which is not H^2(G,Z)."""
    return abelian_group(gap_compute(group, "schur_multiplier", gap=gap, timeout=timeout))


def bogomolov_multiplier(group, *, gap="gap", timeout=300):
    """Abstract invariant factors of B0(G), not chosen cohomology classes.

    HAP calculates a homological dual with the same abstract invariant factors.
    For abelian groups and finite simple groups, the function uses vanishing theorems.
    """
    return abelian_group(gap_compute(group, "bogomolov_multiplier", gap=gap, timeout=timeout))


def mckay_quiver(group, *, representation="natural", gap="gap", timeout=300):
    """Rows i, columns j give dim Hom_G(rho_j,V tensor rho_i).

    V is the group's natural permutation representation or its regular
    representation. Character values are GAP cyclotomic strings.
    unit_index identifies the trivial vertex. Its value can differ from zero.
    """
    if representation not in ("natural", "regular"):
        raise ValueError("representation must be natural or regular")
    data = gap_compute(group, "mckay", representation=representation,
                       gap=gap, timeout=timeout)
    data["character_value_format"] = "exact GAP cyclotomics, E(n)=exp(2*pi*i/n)"
    return data


def cohomology_groups(group, degrees, *, p=None, gap="gap", timeout=300):
    """Cohomology with trivial Z coefficients, or dimensions over Fp."""
    degrees = list(degrees)
    if not degrees:
        raise ValueError("provide at least one degree")
    for n in degrees:
        positive_int(n, "degree", 0)
    if p is not None:
        result = compute_cohomology(group, p, max(degrees), gap=gap, timeout=timeout)
        return [dict(degree=n, p=p, dimension=result.betti_numbers[n]) for n in degrees]
    data = gap_compute(group, "integral_cohomology", degrees=degrees, gap=gap, timeout=timeout)
    return [dict(degree=d["degree"], **abelian_group(d["invariants"])) for d in data]


def integral_periodicity(group, *, max_period=64, gap="gap", timeout=300):
    """Integral periodicity and least positive period, or infinity.

    A search that reaches max_period without a result gives an error.
    The period of the trivial group is 1.
    """
    positive_int(max_period, "max_period")
    return gap_compute(group, "periodicity", max_period=max_period, gap=gap, timeout=timeout)


INVARIANTS = {
    "integral_cohomology": "Integral cohomology in degrees zero to the degree limit",
    "poincare_series": "Full rational cohomology series over Fp",
    "zeros_and_poles": "Zero and pole factors of the full reduced Poincare series",
    "detection_kernel": "Essential cohomology in degrees zero to the degree limit",
    "periodicity": "Integral periodicity and least positive period",
    "betti": "Finite-field Betti numbers from degree zero to the degree limit",
    "schur_multiplier": "Second integral homology, as abelian invariant factors",
    "bogomolov_multiplier": "Bogomolov multiplier, as abelian invariant factors",
    "molien": "Molien class sum and coefficients to the degree limit",
    "mckay": "McKay arrow multiplicities and irreducible character data",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--groups", nargs="+")
    parser.add_argument("--groups-dir", type=Path, default=GROUPS_DIR)
    parser.add_argument("--invariants", nargs="+", choices=INVARIANTS)
    parser.add_argument("--p", type=int, help="prime for finite-field cohomology")
    parser.add_argument("--max-degree", type=int, default=4)
    parser.add_argument("--max-period", type=int, default=64)
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
    modular = {"betti", "poincare_series", "zeros_and_poles", "detection_kernel"}
    if modular.intersection(args.invariants) and args.p is None:
        parser.error("--p is required for finite-field cohomology")
    try:
        positive_int(args.max_degree, "max_degree", 0)
        for group in load_groups(args.groups, args.groups_dir):
            backend = dict(gap=args.gap, timeout=args.timeout)
            for name in args.invariants:
                if name == "betti":
                    result = compute_cohomology(group, args.p, args.max_degree, **backend).to_dict()
                elif name == "integral_cohomology":
                    result = cohomology_groups(group, range(args.max_degree+1), **backend)
                elif name in ("poincare_series", "zeros_and_poles"):
                    series = hilbert_poincare_series(group, args.p, **backend)
                    result = (series.to_dict() if name == "poincare_series" else
                              zeros_and_poles(group, series, **backend))
                elif name == "detection_kernel":
                    result = detection_kernel(group, args.p, max_degree=args.max_degree, **backend)
                elif name == "periodicity":
                    result = integral_periodicity(group, max_period=args.max_period, **backend)
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
