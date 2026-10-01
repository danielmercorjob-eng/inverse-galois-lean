#!/usr/bin/env python3
"""Generate Lean variants of the inverse Galois problem for M23 into Formal Conjectures.

Every generated file is a self-contained Formal Conjectures problem file with exactly
one `sorry`. By default, files are written to
`<formal-conjectures>/FormalConjectures/Other/InverseGaloisM23/`.

Examples:
    ./generate.py --list                         # show the variants, write nothing
    ./generate.py                                # write the default variants
    ./generate.py --digits 100 50 none --real-roots none
    ./generate.py --clean --build                # regenerate, then `lake --wfail build` them
"""

import argparse
import itertools
import subprocess
import sys
from pathlib import Path

from igm23.group import verify_m23
from igm23.variants import (ACTIONS, GENERATED_MARKER, NORMALIZATIONS, REAL_ROOT_COUNTS,
                            Variant, render)

DEFAULT_FC_ROOT = Path.home() / "formal-conjectures"
DEFAULT_SUBDIR = "FormalConjectures/Other/InverseGaloisM23"


def optional_int(s):
    return None if s.lower() == "none" else int(s)


def build_variants(args):
    variants = []
    if not args.no_realizable:
        variants.append(Variant(kind="realizable"))
    if not args.no_regular:
        variants.append(Variant(kind="regular"))
    for action, norm, digits, real in itertools.product(
            args.actions, args.normalizations, args.digits, args.real_roots):
        variants.append(Variant(action=action, normalization=norm, digits=digits,
                                real_roots=real))
    stems = [v.stem for v in variants]
    dupes = {s for s in stems if stems.count(s) > 1}
    if dupes:
        sys.exit(f"duplicate variants: {sorted(dupes)}")
    return variants


def module_name(fc_root: Path, path: Path) -> str:
    return ".".join(path.relative_to(fc_root).with_suffix("").parts)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fc-root", type=Path, default=DEFAULT_FC_ROOT,
                   help=f"Formal Conjectures checkout (default: {DEFAULT_FC_ROOT})")
    p.add_argument("--subdir", default=DEFAULT_SUBDIR,
                   help=f"output directory inside the checkout (default: {DEFAULT_SUBDIR})")
    p.add_argument("--actions", nargs="+", choices=ACTIONS, default=list(ACTIONS),
                   help="abstract: Gal(f) ≃* M23; roots: action on the complex roots is M23")
    p.add_argument("--normalizations", nargs="+", choices=NORMALIZATIONS,
                   default=list(NORMALIZATIONS))
    p.add_argument("--digits", nargs="+", type=optional_int, default=[100, None],
                   help="coefficients have fewer than N decimal digits; 'none' for no bound "
                        "(default: 100 none)")
    p.add_argument("--real-roots", nargs="+", type=optional_int,
                   default=[None, *REAL_ROOT_COUNTS],
                   help="exact number of real roots: none, 23 or 7 (default: all three)")
    p.add_argument("--no-realizable", action="store_true",
                   help="skip the variant 'M23 is a Galois group over Q'")
    p.add_argument("--no-regular", action="store_true",
                   help="skip the variant 'M23 is a regular Galois group over Q(t)'")
    p.add_argument("--list", action="store_true", help="list the variants and exit")
    p.add_argument("--clean", action="store_true",
                   help="first delete previously generated files in the output directory")
    p.add_argument("--build", action="store_true",
                   help="run `lake --wfail build` on the generated modules")
    p.add_argument("--skip-group-check", action="store_true",
                   help="skip the Schreier-Sims check of the M23 generators")
    args = p.parse_args()

    try:
        variants = build_variants(args)
    except ValueError as e:
        sys.exit(f"error: {e}")

    if args.list:
        for v in variants:
            print(f"{v.status:7} {v.stem}")
        print(f"{len(variants)} variants")
        return

    if not args.skip_group_check:
        verify_m23()

    fc_root = args.fc_root.expanduser().resolve()
    if not (fc_root / "lakefile.toml").exists() or not (fc_root / "FormalConjecturesUtil").is_dir():
        sys.exit(f"error: {fc_root} is not a Formal Conjectures checkout")
    out = fc_root / args.subdir
    out.mkdir(parents=True, exist_ok=True)

    if args.clean:
        for f in out.glob("*.lean"):
            if GENERATED_MARKER in f.read_text():
                f.unlink()

    paths = []
    for v in variants:
        text = render(v)
        assert text.count("sorry") == 1, f"{v.stem}: expected exactly one sorry"
        path = out / f"{v.stem}.lean"
        path.write_text(text)
        paths.append(path)
        print(f"{v.status:7} {path.relative_to(fc_root)}")
    print(f"wrote {len(paths)} files to {out}")

    modules = [module_name(fc_root, p) for p in paths]
    cmd = ["lake", "--wfail", "build", *modules]
    if args.build:
        sys.exit(subprocess.call(cmd, cwd=fc_root))
    print("\nTo build them:\n  cd", fc_root, "&& lake --wfail build", " ".join(modules[:2]),
          "..." if len(modules) > 2 else "")


if __name__ == "__main__":
    main()
