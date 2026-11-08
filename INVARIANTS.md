# Five finite-group invariants

These computations consume `GroupSpec` values from `invgal.group.load_groups`.
They check the actual order of the permutation group against its declared order.
They use standard-library Python and GAP/HAP, with no Sage dependency or code.
The associated Mathlib definitions compile without admitted proofs or new axioms.

## Algorithms and outputs

### 1. Finite-field Betti numbers

`compute_cohomology(G, p, max_degree, gap="gap", timeout=300)` returns a
`CohomologyResult` with `betti_numbers` in degrees 0 through the inclusive bound.
These are the dimensions of H^n(G,Fp) with **trivial coefficients**, not integral
ranks. Both the prime and the degree bound can vary. In coprime characteristic,
or when only degree zero is requested, the computation needs no GAP process.

Otherwise, degree one comes from G's abelianization. In degrees 2 and above the
backend builds one HAP resolution of a Sylow p-subgroup through degree d+1 and
reuses it. `PrimePartDerivedFunctor` imposes fusion from the full group. Over a
field the resulting homology and cohomology dimensions agree. Returning only
the Sylow Betti numbers would be wrong; the S3 mod-3 test checks this distinction.
See the [HAP finite-group tutorial](https://gap-packages.github.io/hap/tutorial/chap7.html).

```python
from invgal.group import load_groups
from invgal.cohomology import compute_cohomology

G, = load_groups(["PSL27"])
result = compute_cohomology(G, p=2, max_degree=4)
assert result.betti_numbers == (1, 0, 1, 2, 1)
```

### 2. Schur multiplier

`schur_multiplier(G)` returns `free_rank` and `torsion_invariant_factors` of
H_2(G,Z). It does **not** compute H^2(G,Z). For a finite group this is finite,
so its free rank is zero. Empty torsion factors mean the trivial group.

The default backend is HAP's integral homology computation. On groups of order
above 100,000, an installed `cohomolo` package is used to compute the primary
parts instead. Results are normalized to invariant factors in divisibility
order. PSL27 gives C2 and M23 gives the trivial group.

### 3. Bogomolov multiplier

`bogomolov_multiplier(G)` returns the same abelian-group output format for B0(G).
HAP computes the homological dual quotient; it has the same **abstract invariant
factors** as the cohomological group in the Lean definition. The output does not
include cocycle representatives or a canonical duality isomorphism.

Abelian groups and finite simple groups use their vanishing theorems. Both
bundled groups are simple, so both answers are trivial. General groups use HAP's
`BogomolovMultiplier` algorithm; the S3 test exercises that path. See
[HAP's multiplier API](https://gap-packages.github.io/hap/doc/chap15.html) and
[Kunyavskii's finite-simple-group vanishing theorem](https://arxiv.org/abs/0712.4069).

### 4. Molien series

`molien_series(G, representation="natural", max_degree=6)` returns the **full**
exact Molien rational function as a compressed class sum, plus its coefficient
prefix through `max_degree`. The degree bound limits only that displayed prefix.

For a permutation with c_l cycles of length l, the determinant denominator is
product_l (1-t^l)^c_l. The JSON answer specifies

```
(1/order) * sum(class_size / product((1-t^length)^count))
```

using `order` and a list of `terms`, each with its `class_size` and `cycles`
(length,count) pairs. This is an exact rational-function representation, without
expanding a huge numerator or denominator. Coefficients are exact integers.
For the regular representation an element of order l has |G|/l such cycles.
The regular representation of M23 therefore needs no 10,200,960-dimensional
matrix or expanded denominator.

The representation is part of the invariant. The natural action is the one
stored in the group JSON; it can differ between isomorphic permutation models.
The regular choice depends only on the abstract group. Arbitrary matrix inputs
are outside this implementation's scope.

### 5. McKay arrow multiplicities

`mckay_quiver(G, representation="natural")` returns `vertex_dimensions`, an
`arrows` matrix, and exact character data. Vertex i is the i-th irreducible
character returned by GAP. Entry (i,j) is

```
dim Hom_G(rho_j, V tensor rho_i) = <chi_V * chi_i, chi_j>.
```

The natural and regular choices of V are the same as for Molien computations.
`unit_index` identifies the trivial representation, which GAP does not always
put first. The rows and columns use zero-based indices throughout the Python
output. `class_sizes`, `class_orders`, and character-value vectors refer to the
same conjugacy-class ordering.

Character values are exact GAP cyclotomic strings: `E(n)` denotes exp(2*pi*i/n).
They are data, not Python expressions to evaluate. Bases and irreducible labels
may vary between GAP versions. The code computes the arrow matrix directly from
character inner products, without constructing the entire representation-ring
multiplication tensor.

## Practical scale and verification

The tests run the actual bundled permutation groups, not stored answers:

| Computation | PSL27 | M23 |
|---|---|---|
| Betti numbers | p=2 through degree 4: (1,0,1,2,1) | p=23 through degree 22: 1 in degrees 0,21,22 and zero between |
| Schur multiplier | C2 | trivial |
| Bogomolov multiplier | trivial | trivial |
| Natural Molien coefficients through degree 4 | (1,1,2,4,7) | (1,1,2,3,5) |
| McKay natural representation | 6 irreducible vertices | 17 irreducible vertices |

Small cyclic and elementary abelian groups check cohomology dimensions and
multipliers. S3 checks Sylow fusion and the general Bogomolov algorithm. McKay
tests check sum(dim rho_i)^2=|G| and weighted row dimensions; for the regular
representation its arrow matrix is dim(rho_i)*dim(rho_j).

Higher degrees and different primes can be much harder. M23's Sylow 2-subgroup
has order 128; the characteristic-2 Betti calculation through degree 4 previously
exceeded a 300-second limit. The characteristic-23 example is much smaller.
There is no assertion of practical computation in arbitrary degrees. Schur and
character computations on M23 took seconds to tens of seconds in development.

```bash
INVGAL_GAP=/path/to/gap python3 -m unittest discover -s tests -v
python3 check_lean.py --mathlib-project /path/to/existing/mathlib-project --audit-axioms
```

The Lean files specify the mathematics. They are not a verification of GAP,
HAP, group identification, integer linear algebra or the JSON interface.
