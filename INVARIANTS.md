# First five finite-group invariants

[COHOMOLOGY.md](COHOMOLOGY.md) gives five more cohomology invariants.

The input to each function is a `GroupSpec` from `invgal.group.load_groups`.
The program compares the group order with the `order` field before it calculates an invariant.
The program uses Python and GAP/HAP.
They do not use Sage.

## 1. Betti numbers over Fp

`compute_cohomology(G, p, max_degree, gap="gap", timeout=300)` gives a `CohomologyResult`.
Its `betti_numbers` tuple contains the dimensions of H^n(G,Fp) from degree 0 to `max_degree`, inclusive.
The coefficients have the trivial G-action.
These dimensions are not the ranks of integral cohomology.

You can change the prime p and the degree limit.
For degree 0, the function does not start GAP.
If p does not divide |G|, the function gives (1,0,0,...) without GAP.

Degree 1 uses the abelianization of G.
For higher degrees, HAP calculates one resolution of a Sylow p-subgroup through degree `max_degree+1`.
The program uses that resolution for each requested degree.
`PrimePartDerivedFunctor` includes the fusion relations from G.
Homology and cohomology have the same dimensions over a field.
The [HAP tutorial](https://gap-packages.github.io/hap/tutorial/chap7.html) gives more information.

```python
from invgal.group import load_groups
from invgal.cohomology import compute_cohomology

G, = load_groups(["PSL27"])
result = compute_cohomology(G, p=2, max_degree=4)
assert result.betti_numbers == (1, 0, 1, 2, 1)
```

## 2. Schur multiplier

`schur_multiplier(G)` gives the invariant factors of H_2(G,Z).
It does not calculate H^2(G,Z).
The result contains `free_rank` and `torsion_invariant_factors`.
An empty list of torsion factors means the trivial group.
For a finite group, `free_rank` is zero.

HAP calculates the integral homology.
For groups with order above 100,000, the program uses `cohomolo` if that package is available.
That package calculates the primary parts of the multiplier.
Each invariant factor divides the next factor.
PSL27 gives C2.
M23 gives the trivial group.

## 3. Bogomolov multiplier

`bogomolov_multiplier(G)` gives the abstract invariant factors of B0(G).
It uses the same result fields as `schur_multiplier`.

HAP calculates a homological dual quotient.
That quotient has the same abstract invariant factors as the cohomological group in Lean.
The result does not contain cocycles or a canonical duality isomorphism.
The [HAP multiplier API](https://gap-packages.github.io/hap/doc/chap15.html) gives more information.

For abelian groups and finite simple groups, the program uses the applicable vanishing theorem.
[Kunyavskii proves vanishing for finite simple groups](https://arxiv.org/abs/0712.4069).
The two supplied groups are finite simple groups, so each result is the trivial group.
For other groups, the program uses HAP's `BogomolovMultiplier` algorithm.
The S3 test uses this algorithm.

## 4. Molien series

`molien_series(G, representation="natural", max_degree=6)` gives the full Molien series as a sum of rational functions.
It also gives the coefficients from degree 0 to `max_degree`, inclusive.
The degree limit applies only to this coefficient list.

For each conjugacy class, the result includes `class_size` and `cycles`.
Each item in `cycles` is a pair `(length,count)`.
The fields `order` and `terms` define this rational function:

```text
(1/order) * sum(class_size / product((1-t^length)^count))
```

The coefficient list contains integers.
The rational function keeps its class-sum form.
The program does not expand its numerator or denominator.

For the regular representation, an element of order l has |G|/l cycles.
Thus, a matrix with 10,200,960 rows is not necessary for M23.

The natural permutation representation uses the action in the group JSON file.
An isomorphic group with a different action can have a different Molien series.
The regular representation depends only on the abstract group.
The function does not accept other matrix representations.

## 5. McKay arrow multiplicities

`mckay_quiver(G, representation="natural")` gives `vertex_dimensions`, `arrows`, and character data.
Vertex i is the i-th irreducible character from GAP.
Entry (i,j) of `arrows` is this multiplicity:

```text
dim Hom_G(rho_j, V tensor rho_i) = <chi_V * chi_i, chi_j>
```

V is the natural permutation representation or the regular representation.
`unit_index` identifies the trivial representation.
GAP does not always put that representation first.
All vertex indices start at zero.

`class_sizes`, `class_orders`, and character vectors use the same conjugacy-class order.
Character values use GAP cyclotomic strings.
`E(n)` means `exp(2*pi*i/n)`.
These strings are data, not Python expressions.
GAP versions can use different bases and irreducible labels.

The program calculates the arrows from character inner products.
It does not calculate the full multiplication table of the representation ring.

## Tests and time limits

The tests calculate results from the supplied permutation generators.
They do not read stored results.

| Result | PSL27 | M23 |
|---|---|---|
| Betti numbers | p=2, degrees 0 to 4: (1,0,1,2,1) | p=23, degrees 0 to 22: 1 at 0,21,22 and 0 elsewhere |
| Schur multiplier | C2 | Trivial group |
| Bogomolov multiplier | Trivial group | Trivial group |
| Natural Molien coefficients, degrees 0 to 4 | (1,1,2,4,7) | (1,1,2,3,5) |
| McKay vertices | 6 | 17 |

The small-group tests include cyclic groups, elementary abelian groups, and S3.
The S3 test compares the cohomology dimensions after the fusion relations.
The McKay tests use character identities.
For the regular representation, the arrow multiplicity is `dim(rho_i)*dim(rho_j)`.

Different primes and higher degrees can use much more time.
M23 has a Sylow 2-subgroup of order 128.
At p=2, GAP did not complete the Betti result through degree 4 in 300 seconds or less.
The tested M23 example uses p=23 and degree 22.
GAP completed the Schur multiplier and character operations for M23 in seconds to tens of seconds.

To select a GAP executable for the tests, use this command:

```bash
INVGAL_GAP=/path/to/gap python3 -m unittest discover -s tests -v
```

The Lean definitions do not verify the GAP results or the JSON interface.
[formalisation_gaps.md](formalisation_gaps.md) identifies the missing theorems.
