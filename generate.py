#!/usr/bin/env python3
"""Generate Lean variants of the inverse Galois problem into Formal Conjectures.

Groups are described by JSON files in `groups/`. For each group, every generated file is a
self-contained Formal Conjectures problem file with exactly one `sorry`. By default, files are
written to `<formal-conjectures>/FormalConjectures/Other/InverseGalois/<Group>/`.

Examples:
    ./generate.py --list                        # show the variants, write nothing
    ./generate.py                               # all groups, default variants
    ./generate.py --groups M23 --digits 100 50 none
    ./generate.py --clean --build               # regenerate, then `lake --wfail build` them
"""

import argparse
import itertools
import subprocess
import sys
from pathlib import Path

from invgal.group import GROUPS_DIR, load_groups
from invgal.variants import ACTIONS, GENERATED_MARKER, NORMALIZATIONS, Variant, render

DEFAULT_FC_ROOT = Path.home() / "formal-conjectures"
DEFAULT_SUBDIR = "FormalConjectures/InverseGalois"


def optional_int(s):
    return None if s.lower() == "none" else int(s)


def variants_for(group, args):
    out = []
    if not args.no_realizable:
        out.append(Variant(group, kind="realizable"))
    if not args.no_regular:
        out.append(Variant(group, kind="regular"))
    known = sorted({k.digits for k in group.known if k.digits is not None})
    digits = args.digits or known + [None]
    real_roots = args.real_roots or [None, *group.real_root_counts()]
    normalizations = [m for m in args.normalizations
                      if group.transitive or m != "monic_irreducible"]
    for action, norm, d, real in itertools.product(args.actions, normalizations, digits,
                                                   real_roots):
        out.append(Variant(group, action=action, normalization=norm, digits=d, real_roots=real))
    if args.skip_unknown:
        out = [v for v in out if v.status != "unknown"]
    return out


def module_name(fc_root: Path, path: Path) -> str:
    return ".".join(path.relative_to(fc_root).with_suffix("").parts)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fc-root", type=Path, default=DEFAULT_FC_ROOT,
                   help=f"Formal Conjectures checkout (default: {DEFAULT_FC_ROOT})")
    p.add_argument("--subdir", default=DEFAULT_SUBDIR,
                   help=f"output directory inside the checkout (default: {DEFAULT_SUBDIR})")
    p.add_argument("--groups-dir", type=Path, default=GROUPS_DIR,
                   help="directory of group JSON files (default: groups/)")
    p.add_argument("--groups", nargs="+", help="group names to use (default: all)")
    p.add_argument("--actions", nargs="+", choices=ACTIONS, default=list(ACTIONS),
                   help="abstract: Gal(f) ≃* G; roots: action on the complex roots is G")
    p.add_argument("--normalizations", nargs="+", choices=NORMALIZATIONS,
                   default=list(NORMALIZATIONS))
    p.add_argument("--digits", nargs="+", type=optional_int,
                   help="coefficients have fewer than N decimal digits; 'none' for no bound "
                        "(default: the bounds of the group's known polynomials, and none)")
    p.add_argument("--real-roots", nargs="+", type=optional_int,
                   help="exact number of real roots, or 'none' (default: none and every "
                        "possible count)")
    p.add_argument("--no-realizable", action="store_true",
                   help="skip the variant 'G is a Galois group over Q'")
    p.add_argument("--no-regular", action="store_true",
                   help="skip the variant 'G is a regular Galois group over Q(t)'")
    p.add_argument("--skip-unknown", action="store_true",
                   help="only generate variants whose status the group file settles")
    p.add_argument("--list", action="store_true", help="list the variants and exit")
    p.add_argument("--clean", action="store_true",
                   help="first delete previously generated files of the selected groups")
    p.add_argument("--build", action="store_true",
                   help="run `lake --wfail build` on the generated modules")
    args = p.parse_args()

    try:
        groups = load_groups(args.groups, args.groups_dir)
        for g in groups:
            g.verify()
        variants = [v for g in groups for v in variants_for(g, args)]
    except (ValueError, AssertionError) as e:
        sys.exit(f"error: {e}")

    if args.list:
        for v in variants:
            print(f"{v.status:8} {v.group.name}/{v.stem}")
        print(f"{len(variants)} variants")
        return

    fc_root = args.fc_root.expanduser().resolve()
    if not (fc_root / "lakefile.toml").exists() or not (fc_root / "FormalConjecturesUtil").is_dir():
        sys.exit(f"error: {fc_root} is not a Formal Conjectures checkout")
    out_root = fc_root / args.subdir

    if args.clean:
        for g in groups:
            for f in (out_root / g.name).glob("*.lean"):
                if GENERATED_MARKER in f.read_text():
                    f.unlink()

    try:
        rendered = [(v, render(v)) for v in variants]  # fail before writing anything
    except ValueError as e:
        sys.exit(f"error: {e}")
    paths = []
    for v, text in rendered:
        assert text.count("sorry") == 1, f"{v.stem}: expected exactly one sorry"
        path = out_root / v.group.name / f"{v.stem}.lean"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        paths.append(path)
        print(f"{v.status:8} {path.relative_to(fc_root)}")
    print(f"wrote {len(paths)} files under {out_root}")

    modules = [module_name(fc_root, p) for p in paths]
    if args.build:
        sys.exit(subprocess.call(["lake", "--wfail", "build", *modules], cwd=fc_root))
    print(f"\nTo build them:\n  cd {fc_root} && lake --wfail build {modules[0]} ...")


if __name__ == "__main__":
    main()
