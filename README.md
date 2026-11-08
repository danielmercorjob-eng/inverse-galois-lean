# inverse-galois-lean

A Python generator for Lean 4 variants of the **inverse Galois problem** for finite
permutation groups. The output is in the format of
[Formal Conjectures](https://github.com/google-deepmind/formal-conjectures).

It started from the
[Epoch AI FrontierMath open problem for M₂₃](https://epoch.ai/frontiermath/open-problems/inverse-galois):

> Find a degree 23 polynomial with integer coefficients, each with fewer than 100 decimal
> digits, whose splitting field over ℚ has Galois group M₂₃.

Groups are data. Each group is a JSON file in [`groups/`](groups). The repository includes
M₂₃ and PSL(2, 7).

The generator writes problem files into a local Formal Conjectures clone, under
`FormalConjectures/InverseGalois/<Group>/`. Each generated file:

- follows the Formal Conjectures file template (copyright header, `module`,
  `public import FormalConjecturesUtil`, module docstring with references);
- is self-contained: it defines the group as a subgroup of `Equiv.Perm (Fin n)` and has its own
  namespace, `InverseGaloisVariants.<Group><Variant>`;
- has **exactly one `sorry`**: the proof of its main theorem. The `@[category test]` checks of
  the generators are proved by `decide`.

## Usage

Requires Python 3.9+ and nothing else.

```bash
./generate.py --list                    # show the variants and their status; write nothing
./generate.py                           # all groups, default variants
./generate.py --groups M23 --digits 100 50 none
cd ~/formal-conjectures && lake build   # builds the new files; everything else is cached
```

| Option | Meaning |
|---|---|
| `--fc-root PATH` | Formal Conjectures checkout (default `~/formal-conjectures`) |
| `--subdir DIR` | output directory inside it (default `FormalConjectures/InverseGalois`) |
| `--groups G …` | groups to use (default: every file in `groups/`) |
| `--groups-dir DIR` | where to read group files from |
| `--actions abstract roots` | how the Galois group is stated (see below) |
| `--normalizations any monic monic_irreducible` | conditions on $f$ |
| `--digits N … none` | coefficients have fewer than $N$ decimal digits; `none` for no bound |
| `--real-roots k … none` | exact number of real roots |
| `--no-realizable`, `--no-regular` | skip the two field-theoretic variants |
| `--skip-unknown` | only generate variants whose status the group file settles |
| `--clean` | delete previously generated files of the selected groups first (hand-written files are kept) |
| `--build` | run `lake --wfail build` on the generated modules |

## Variants

For a group $G \le S_n$, polynomial variants are the product of these axes:

- **Galois group (`--actions`)**
  - `abstract`: `Nonempty ((f.map (Int.castRingHom ℚ)).Gal ≃* G)`.
  - `roots`: for some bijection between the complex roots and `Fin n`, the image of the
    Galois action is exactly `G ≤ Equiv.Perm (Fin n)`.
- **Normalization:** any polynomial, monic, or monic and irreducible. The irreducible option is
  skipped for intransitive groups, where it is false.
- **Digit bound:** `(Nat.digits 10 (f.coeff i).natAbs).length < N` for all `i`. The default
  bounds are those of the group's known polynomials, plus no bound.
- **Real roots:** complex conjugation acts on the roots as the identity or as an involution of
  $G$. So the possible counts are $n$ and the fixed-point counts of involutions. The generator
  computes these by random sampling and rejects other counts.

There are also two standalone variants:

- **`Realizable`:** a finite Galois extension of ℚ has Galois group $G$.
- **`RegularOverRatFunc`:** $G$ is a regular Galois group over ℚ(t).

### Status

Each variant gets one of three statuses:

- **`solved`**: it follows from the group file by an elementary argument. Either a known
  polynomial satisfies all its conditions, or it has no digit bound and no real-root
  condition and $G$ is realizable over ℚ. In that case scaling gives a monic polynomial, and a
  transitive Galois group makes it irreducible.
- **`open`**: the group file records it as open. Every polynomial variant is open when
  realizability is open.
- **`unknown`**: the group file does not settle it. These files get
  `@[category research open]` and say so in their docstring. Use `--skip-unknown` to omit them.

## Group files

```jsonc
{
  "name": "PSL27",                        // Lean identifier, folder name
  "latex": "\\mathrm{PSL}(2, 7)",
  "description": "the simple group ... acting on the $7$ points of the Fano plane",
  "degree": 7,
  "order": 168,                           // checked by Schreier–Sims
  "generators": [[[1, 2, 3, 4, 5, 6, 7]], [[3, 5], [6, 7]]],   // 1-indexed cycles
  "identification": "... is the only transitive group of degree $7$ of that order.",
  "status": {"realizable": "solved"},     // optional: realizable, regular = solved | open
  "known_polynomials": [
    // Either coefficients (lowest degree first), from which the degree, digit bound,
    // monicity and number of real roots (Sturm) are computed ...
    {"coefficients": [3, -7, 0, 0, 0, 0, 0, 1], "root_action": true, "source": "..."}
    // ... or declared properties: {"digits": 100, "monic": true, "real_roots": 7, ...}
  ],
  "notes": {"realizable": "...", "regular": "..."},
  "references": [{"title": "...", "url": "..."}]
}
```

`root_action: true` records that the polynomial's Galois action on its roots is the group's
permutation action up to relabelling.

The generator checks the declared order and fails on a mismatch. The order identifies $G$ only
together with the `identification` note, so check that note when you add a group.

## Five finite-group invariants

The repository also computes five invariants from the same verified group JSON
files, with Python 3.9+ and [GAP](https://www.gap-system.org/)/
[HAP](https://gap-packages.github.io/hap/). Sage is not required.

| Invariant | Python API | Lean definition |
|---|---|---|
| Finite-field Betti numbers through degree d | `invgal.cohomology.compute_cohomology` | `FiniteGroupCohomology.bettiNumber` |
| Schur multiplier H_2(G,Z) | `invgal.invariants.schur_multiplier` | `FiniteGroupInvariants.schurMultiplier` |
| Bogomolov multiplier B0(G) | `invgal.invariants.bogomolov_multiplier` | `FiniteGroupInvariants.bogomolovMultiplier` |
| Molien series | `invgal.series.molien_series` | `FiniteGroupInvariants.molienSeries` |
| McKay arrow multiplicities | `invgal.invariants.mckay_quiver` | `FiniteGroupInvariants.mckayMultiplicity` |

For Molien and McKay computations, choose the natural permutation representation
(the default) or the regular representation. The Python code uses only its
standard library and invokes GAP as a separate process. On Debian/Ubuntu:

```bash
sudo apt-get install gap gap-hap
python3 -m invgal.invariants --list
python3 -m invgal.invariants --groups PSL27 --invariants betti --p 2 --max-degree 4
python3 -m invgal.invariants --groups M23 --invariants betti --p 23 --max-degree 22
python3 -m invgal.invariants --groups PSL27 M23 --invariants schur_multiplier bogomolov_multiplier molien mckay
python3 -m invgal.invariants --groups M23 --invariants molien --representation regular --max-degree 4
```

Select a GAP executable with `--gap PATH`. `--timeout SECONDS` limits each GAP
call (default 300 seconds). Each output line is JSON with the group, invariant
name and result. A failed or timed-out calculation exits with an error; it does
not return partial data as a complete invariant. Earlier JSON lines, if any,
still describe completed calculations. GAP's optional `cohomolo` package
accelerates large-group Schur multiplier calculations when installed.

See [INVARIANTS.md](INVARIANTS.md) for exact output conventions, Python examples,
algorithms and practical limits on PSL27 and M23. The two Lean files define the
mathematical quantities using Mathlib; they do not certify the Python results.
[formalisation_gaps.md](formalisation_gaps.md) records the remaining comparison
and interpretation theorems.

## Development

```bash
python3 -m unittest discover -s tests   # includes GAP tests when available
python3 -m invgal.group                 # check every group file
```

Set `INVGAL_GAP=/path/to/gap` to run the GAP/HAP integration tests with a specific
executable. Without GAP, those integration tests are skipped. To compile the
standalone definitions against an existing Mathlib project:

```bash
python3 check_lean.py --mathlib-project /path/to/mathlib-project --audit-axioms
```

The definitions were checked with Lean 4.27.0 and Mathlib commit `a3a10db0e9d6`,
with warnings treated as errors.
