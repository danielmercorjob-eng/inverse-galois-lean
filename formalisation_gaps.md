# Lean definitions and missing theorems

Three Lean files define the ten invariants with Mathlib.
`CohomologyInvariants.lean` adds integral cohomology, restriction kernels, rational series presentations, and periodicity.
`GroupCohomologyInvariants.lean` adds the full Poincare series to the Betti definitions.
The files contain no `sorry` declarations and no new axioms.
They compile with Lean 4.27.0 and Mathlib commit `a3a10db0e9d66acbebf76c5e6a135066525ac900`.

| Invariant | Lean definition | Missing theorems |
|---|---|---|
| Betti numbers | `Module.finrank` of H^n(G,Fp) with trivial coefficients | Comparison with the HAP resolution and fusion algorithm |
| Schur multiplier | H_2(G,Z) | Finiteness, the covering-group interpretation, and duality with H^2(G,Q/Z) |
| Bogomolov multiplier | Intersection of restriction kernels in H^2(G,Q/Z) for all abelian subgroups | Finiteness, the comparison with HAP's homological dual, and the vanishing theorems |
| Molien series | Determinant sum for the dual of a matrix representation in characteristic zero | Molien's theorem and the permutation-cycle formula |
| McKay arrow multiplicity | Dimension of Hom(W,V tensor U) for simple U and W | A full finite index of irreducible isomorphism classes and the character inner-product formula |
| Integral cohomology | H^n(G,Z) with trivial coefficients | The invariant-factor comparison with HAP and integral homology in degree n-1 |
| Full Poincare series | Formal power series with integer Betti coefficients | Finite generation, rationality, cyclic Sylow formulas, and the Kunneth comparison |
| Zeros and poles | Root multiplicities in a reduced rational presentation | Existence of `RationalPoincarePresentation`, uniqueness of its polynomials, and comparison with GAP factorization |
| Detection kernels | Intersection of Mathlib restriction kernels in each degree | The normalized bar comparison, maximal-subgroup reduction, and the transfer argument for essential vanishing |
| Integral periodicity | Cyclicity of all abelian subgroups, and the least positive degree with H^n(G,Z) cyclic of order `Nat.card G` | Equivalence with integral Tate periodicity, the Sylow criterion, and comparison with the period search |

The Poincare series has actual cohomology dimensions as coefficients.
A rational presentation must contain a proof of equality with that series.
The definitions do not assume rationality as an axiom.
The root multiplicities use coprime polynomials, so cancellation occurs before zeros and poles are defined.

The detection definitions give submodules in each degree.
They do not give a graded cohomology ring or a full graded detection ideal.
The file proves the kernel membership rules and the empty-family case.
It also gives the degree-zero integral cohomology isomorphism and the infinite-period criterion.

The period definition uses positive-degree integral cohomology.
The comparison with Tate cohomology and periodic resolutions is a different formalization task.
This work is necessary for a proof of the full periodicity interpretation.

The Betti file proves finite dimensionality and b0=1.
It also proves the length and entries of the Betti list.

The Bogomolov definition uses the additive quotient Q/Z.
Its restriction maps are Mathlib's cohomology pullbacks with identity coefficient maps.
The result is an additive subgroup.

The Molien definition uses the inverse transpose for the dual action.
It gives a formal power series for a matrix representation.
Python accepts only the natural and regular permutation representations.

The McKay definition gives the arrow multiplicity for two simple representations.
Python uses GAP's character table to index the irreducible representations.
Lean does not prove that this index is full.

The files do not prove that the Python results are correct.
They also do not identify the JSON permutation groups with the abstract Lean group G.
The missing comparison theorems are different formalization tasks.

To compile the three files, use a Mathlib project:

```bash
python3 check_lean.py --mathlib-project /path/to/existing/mathlib-project --audit-axioms
```

The script uses that project's toolchain and imports.
It gives an error for each Lean warning.
It writes the compiled files into a temporary directory.
The axiom audit rejects axioms other than Lean's standard logical axioms.
