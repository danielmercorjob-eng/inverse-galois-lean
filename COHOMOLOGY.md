# Five more cohomology invariants

These functions use Python's standard library and GAP/HAP.
Sage and SymPy are not necessary.
The coefficients have the trivial group action.
The input is a `GroupSpec` from `invgal.group.load_groups`.
The program compares the group order with the declared order before it calculates a result.

| Invariant | Python API | Lean definition |
|---|---|---|
| Integral cohomology | `cohomology_groups` | `integralCohomology` |
| Full Poincare series | `hilbert_poincare_series` | `poincareSeries` |
| Zero and pole multiplicities | `zeros_and_poles` | `zeroMultiplicity`, `poleMultiplicity` |
| Detection kernels and essential cohomology | `detection_kernel` | `detectionKernel`, `essentialCohomology` |
| Integral periodicity and least period | `integral_periodicity` | `periodicityCriterion`, `integralPeriod` |

The functions are available from `invgal.invariants`.
`zeros_and_poles` is also available from `invgal.series`.
All degree limits are inclusive.

## Integral cohomology

`cohomology_groups(G, degrees)` gives H^n(G,Z) for each degree in `degrees`.
Each result has `degree`, `free_rank`, and `torsion_invariant_factors` fields.
The factors have divisibility order.
An empty factor list with `free_rank=0` means the trivial group.
The result list keeps the order and repetitions in `degrees`.

H^0(G,Z) is Z, and H^1(G,Z) is zero for finite G.
For `n >= 2`, HAP calculates the invariant factors of H^n(G,Z).
For finite groups, these factors agree with those of H_(n-1)(G,Z).
This comparison does not give a canonical isomorphism.
The integral result includes torsion.
It is not a list of Betti numbers.

To get finite-field dimensions with the same interface, set `p` to a prime.
This option uses the Betti algorithm from [INVARIANTS.md](INVARIANTS.md).

## Full Poincare series

`hilbert_poincare_series(G, p)` gives the full rational function
P(t) = sum dim H^n(G,Fp) t^n.
The result is a `RationalSeries`.
Its numerator and denominator are coprime, with constant coefficients 1.
Their coefficient lists start at degree zero.
`to_dict()` writes each rational coefficient as a string.
`coefficients(d)` gives the coefficients from degree zero to degree d.

The function uses these formulas:

- If p does not divide |G|, P(t)=1.
- If a Sylow p-subgroup is C2, P(t)=1/(1-t).
- For other cyclic Sylow p-subgroups, P(t)=(1+t^(2e-1))/(1-t^(2e)). Here e=|N_G(S)/C_G(S)|.
- For abelian groups, the Kunneth formula gives a product of the cyclic-factor series.

For other groups and primes, the function gives an error.
A coefficient list with a degree limit cannot specify the full series.
The function does not infer a full series from such a list.

## Zeros and poles

`zeros_and_poles(G, series)` uses a full `RationalSeries`.
GAP factors its reduced numerator and denominator over Q.
Each factor record gives its exact coefficients and its root multiplicity.
That multiplicity applies to each complex root of the factor.
The result gives all roots through their irreducible factors.
It does not give decimal approximations.

`root_of_unity_order` identifies cyclotomic factors.
Its value is null for other factors.
For poles, the function gives an error if a factor is not cyclotomic.
`pole_order_at_one` is the multiplicity at t=1 after cancellation.
`least_eventual_quasipolynomial_period` is the least common multiple of the pole orders as roots of unity.
For P(t)=1, this period is 1 and there are no zeros or poles.

`RationalSeries` gives coprime polynomials with constant coefficients 1.
It does not prove that a user-supplied rational function is a cohomology series.
Use `hilbert_poincare_series` to get a series from these group formulas.
In Lean, `RationalPoincarePresentation` also has a proof of equality with the full cohomology series.

## Detection kernels

`detection_kernel(G, p, max_degree=d)` gives essential cohomology in each degree from 0 to d.
This is the intersection of restriction kernels for all proper subgroups.
For finite groups, maximal subgroups give the same intersection.

To select a different family, set `subgroups` to a list of generator lists.
Each generator is a permutation image list with indices from zero to `G.degree-1`.
These lists use the same points as G.
They do not use the cycle notation from the group JSON files.
GAP verifies that each subgroup is contained in G.

`subgroups=[]` gives an empty family, so the kernel is all of H^n(G,Fp).
`subgroups=[[]]` gives the family with only the trivial subgroup.
The result has `full_presentation=false`.
It does not give generators for a full graded ideal.

Each degree record gives `kernel_dimension`.
The bar algorithm also gives `source_dimension`, `source_basis_cochains`, and `kernel_basis`.
The kernel vectors use coordinates in `source_basis_cochains`.
`group_elements` lists permutations with indices from zero, with the identity at index zero.
Cochain entries use lexicographic tuples of nonidentity element indices.
Degree zero uses the empty tuple.
`subgroup_elements` lists the element indices for each subgroup in the restriction family.

If G is not a p-group, restriction to a proper Sylow p-subgroup is injective.
Essential cohomology is then zero in all degrees.
For these groups, the result gives zero dimensions without cochain bases or group enumeration.
It applies to the two supplied groups at every prime.

The bar algorithm has these initial limits:

| Parameter | Limit |
|---|---|
| `max_elements` | 64 group elements |
| `max_cochains` | 4096 cochain coordinates in each degree |
| `max_matrix_entries` | 2,000,000 entries for each differential or restriction matrix, with its source lifts |
| `max_subgroups` | 1000 subgroups |

The algorithm also calculates the differential from degree d to degree d+1.
That differential must satisfy the same limits.
Use small groups and low degrees for specified subgroup families.
A limit gives an error. It does not give a smaller result as if it were full.

## Integral periodicity

`integral_periodicity(G, max_period=64)` first uses the finite-group periodicity criterion.
Each Sylow subgroup must be cyclic or generalized quaternion.
A noncyclic 2-group is generalized quaternion if it has only one involution.
For other groups, the result is `periodic=false`, with `period="infinity"`.

For groups with cyclic or generalized quaternion Sylow subgroups, the least positive n with H^n(G,Z) cyclic of order |G| gives the period.
HAP tests these degrees in order.
Nontrivial cyclic groups have period 2.
The trivial group has period 1 by convention.
If the search reaches `max_period` without a result, the function gives an error.
It does not report an infinite period from a finite search.

## Examples and checks

```python
from invgal.group import load_groups
from invgal.invariants import cohomology_groups, hilbert_poincare_series
from invgal.invariants import zeros_and_poles, detection_kernel, integral_periodicity

G, = load_groups(["PSL27"])
assert cohomology_groups(G, [3])[0]["torsion_invariant_factors"] == [2]
series = hilbert_poincare_series(G, 7)
assert series.coefficients(6) == (1, 0, 0, 0, 0, 1, 1)
assert zeros_and_poles(G, series)["pole_order_at_one"] == 1
assert detection_kernel(G, 7, max_degree=3)["zero_through_max_degree"]
assert integral_periodicity(G)["period"] == "infinity"
```

| Result | PSL27 | M23 |
|---|---|---|
| Integral cohomology, degrees 0 to 3 | Z, 0, 0, C2 | Z, 0, 0, 0 |
| Full series at the tested prime | p=7: (1+t^5)/(1-t^6) | p=23: (1+t^21)/(1-t^22) |
| Pole order at t=1 | 1 | 1 |
| Least eventual quasipolynomial period | 6 | 22 |
| Essential cohomology | Zero | Zero |
| Integral period | Infinity | Infinity |

The tests compare series coefficients with the HAP Betti algorithm.
They also test nonzero essential cohomology for C3 and C2 x C2.
For C2 x C2 at p=2, the essential dimensions in degrees 0 to 3 are (0,0,0,1).
S3 and Q8 have integral period 4.

Use `--invariants` with `integral_cohomology`, `poincare_series`, `zeros_and_poles`, `detection_kernel`, or `periodicity`.
The CLI detection result uses essential cohomology.
Specified subgroup families use the Python API.

```bash
python3 -m invgal.invariants --groups PSL27 --invariants integral_cohomology periodicity --max-degree 3
python3 -m invgal.invariants --groups M23 --invariants poincare_series zeros_and_poles detection_kernel --p 23 --max-degree 3
```

`--timeout` sets the time limit for each GAP call.
For the bar algorithm, it also sets a time limit for the full Python worker and its GAP processes.
If an error occurs, the program stops before it writes that result.
Previous JSON lines give completed results.
The [formalization gap list](formalisation_gaps.md) identifies the missing Lean theorems.
