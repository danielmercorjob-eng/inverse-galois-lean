# inverse-galois-lean

This project uses Python to write Lean files for the inverse Galois problem.
It also calculates [five finite-group invariants](INVARIANTS.md) and [five more cohomology invariants](COHOMOLOGY.md).
The group files include M23 and PSL(2,7).

The project includes the [Epoch AI problem for M23](https://epoch.ai/frontiermath/open-problems/inverse-galois).
The polynomial must have degree 23 and integer coefficients.
Its splitting field over Q must have Galois group M23.
Each coefficient must have a decimal digit count less than 100.

## Write Lean files

Python 3.9+ is necessary for the generator.
It writes files into a local copy of [Formal Conjectures](https://github.com/google-deepmind/formal-conjectures).
The output directory is `FormalConjectures/InverseGalois/<Group>/`.
Each file defines a group and one theorem for the inverse Galois problem.
That theorem has one `sorry`, so Lean does not verify it.
The generated tests use `decide`.

Use these commands from the project directory:

```bash
./generate.py --list
./generate.py
./generate.py --groups M23 --digits 100 50 none
```

To compile the generated files, use this command in the Formal Conjectures directory:

```bash
lake build
```

| Option | Function |
|---|---|
| `--fc-root PATH` | Set the Formal Conjectures directory. The initial value is `~/formal-conjectures`. |
| `--subdir DIR` | Set the output directory in that project. The initial value is `FormalConjectures/InverseGalois`. |
| `--groups G …` | Select groups. Without this option, the generator uses all group files. |
| `--groups-dir DIR` | Select the directory with the group files. |
| `--actions abstract roots` | Select the Galois group definition. |
| `--normalizations any monic monic_irreducible` | Select the polynomial conditions. |
| `--digits N … none` | Set the decimal digit limit. Use `none` for no limit. |
| `--real-roots k … none` | Set the number of real roots. Use `none` for no condition. |
| `--no-realizable` | Do not write the `Realizable` statement. |
| `--no-regular` | Do not write the `RegularOverRatFunc` statement. |
| `--skip-unknown` | Do not write statements with an `unknown` status. |
| `--clean` | Delete earlier generated files for the selected groups. Keep other files. |
| `--build` | Compile the generated modules with `lake --wfail build`. |

### Statement options

For G in S_n, the generator uses these options:

- Galois group: an abstract isomorphism, or equality with the Galois action on the roots.
- Polynomial: a polynomial with no more conditions, a monic polynomial, or a monic irreducible polynomial.
- Decimal digit limit: limits from the known polynomials, or no limit.
- Real roots: no condition, or a permitted root count.

For an intransitive action, the generator does not write `monic_irreducible` statements.
The permitted root counts depend on complex conjugation.
The generator uses random samples of involutions to find those counts.
It rejects other requested counts.

Two more statements give conditions on field extensions:

- `Realizable`: G is a Galois group over Q.
- `RegularOverRatFunc`: G is a regular Galois group over Q(t).

Each statement has one status:

| Status | Meaning |
|---|---|
| `solved` | A known polynomial or an existence result gives a solution. |
| `open` | The group file identifies the statement as an open problem. |
| `unknown` | The group file does not give a solution or an open status. |

The generator writes `@[category research open]` for an `unknown` statement.

### Group files

Each JSON file in [groups/](groups) defines one permutation group.
This example shows the input fields:

```jsonc
{
  "name": "PSL27",
  "latex": "\\mathrm{PSL}(2, 7)",
  "description": "PSL(2,7) on the seven points of the Fano plane",
  "degree": 7,
  "order": 168,
  "generators": [[[1, 2, 3, 4, 5, 6, 7]], [[3, 5], [6, 7]]],
  "identification": "The unique transitive group of degree 7 and order 168",
  "status": {"realizable": "solved"},
  "known_polynomials": [
    {"coefficients": [3, -7, 0, 0, 0, 0, 0, 1], "root_action": true, "source": "..."}
  ],
  "notes": {"realizable": "..."},
  "references": [{"title": "...", "url": "..."}]
}
```

The generator cycles use point numbers from 1 to `degree`.
The polynomial coefficients start with the constant coefficient.
As an alternative, a known polynomial can give its `digits`, `monic`, and `real_roots` properties.
`root_action: true` means that the polynomial's Galois action and the group's permutation action agree up to a change of labels.

The program calculates the group order from the generators.
It compares that order with `order` in the JSON file.
The order does not always identify the group.
The `identification` field gives more mathematical information.

## Calculate invariants

This program uses Python 3.9+, [GAP](https://www.gap-system.org/), and [HAP](https://gap-packages.github.io/hap/).
The Python code uses its standard library.
It starts GAP as a different process.
Sage is not necessary.

| Invariant | Python function | Lean definition |
|---|---|---|
| Betti numbers over Fp | `invgal.cohomology.compute_cohomology` | `FiniteGroupCohomology.bettiNumber` |
| Schur multiplier | `invgal.invariants.schur_multiplier` | `FiniteGroupInvariants.schurMultiplier` |
| Bogomolov multiplier | `invgal.invariants.bogomolov_multiplier` | `FiniteGroupInvariants.bogomolovMultiplier` |
| Molien series | `invgal.series.molien_series` | `FiniteGroupInvariants.molienSeries` |
| McKay arrow multiplicities | `invgal.invariants.mckay_quiver` | `FiniteGroupInvariants.mckayMultiplicity` |

[COHOMOLOGY.md](COHOMOLOGY.md) gives five more invariants: integral cohomology, full Poincare series, zero and pole multiplicities, detection kernels, and integral periodicity.
These functions also use only Python and GAP/HAP.

On Debian or Ubuntu, install the dependencies with this command:

```bash
sudo apt-get install gap gap-hap
```

Use these commands from the project directory:

```bash
python3 -m invgal.invariants --list
python3 -m invgal.invariants --groups PSL27 --invariants betti --p 2 --max-degree 4
python3 -m invgal.invariants --groups M23 --invariants betti --p 23 --max-degree 22
python3 -m invgal.invariants --groups PSL27 M23 --invariants schur_multiplier bogomolov_multiplier molien mckay
python3 -m invgal.invariants --groups M23 --invariants molien --representation regular --max-degree 4
```

For Molien and McKay results, select the natural permutation representation or the regular representation.
The program uses the natural permutation representation unless you select `regular`.
Select a GAP executable with `--gap PATH`.
Set the time limit for each GAP call with `--timeout SECONDS`.
The initial time limit is 300 seconds.

Each output line gives one completed result in JSON format.
If GAP cannot complete an operation, the program stops with an error.
The previous output lines give completed results.
The optional `cohomolo` package can decrease the time to calculate large Schur multipliers.

[INVARIANTS.md](INVARIANTS.md) gives the algorithms, result formats, and time limits.
The Lean files define the mathematical quantities.
They do not prove that the Python results are correct.
[formalisation_gaps.md](formalisation_gaps.md) identifies the missing comparison theorems.
[TECHNICAL_TERMS.md](TECHNICAL_TERMS.md) gives the meanings of the project terms for the English text.

## Test the project

Use these commands:

```bash
python3 -m unittest discover -s tests
python3 -m invgal.group
```

For a different GAP executable, set `INVGAL_GAP=/path/to/gap`.
Without GAP, the test suite does not start the GAP tests.

To compile the Lean definitions, use a Mathlib project:

```bash
python3 check_lean.py --mathlib-project /path/to/mathlib-project --audit-axioms
```

The definitions compile with Lean 4.27.0 and Mathlib commit `a3a10db0e9d6`.
The command gives an error for each Lean warning.
The axiom audit rejects axioms other than Lean's standard logical axioms.
