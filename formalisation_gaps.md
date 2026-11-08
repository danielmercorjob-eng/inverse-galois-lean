# Lean definitions and missing theorems

`GroupCohomologyInvariants.lean` and `FiniteGroupInvariants.lean` define the five invariants with Mathlib.
The files contain no `sorry` declarations and no new axioms.
They compile with Lean 4.27.0 and Mathlib commit `a3a10db0e9d66acbebf76c5e6a135066525ac900`.

| Invariant | Lean definition | Missing theorems |
|---|---|---|
| Betti numbers | `Module.finrank` of H^n(G,Fp) with trivial coefficients | Comparison with the HAP resolution and fusion algorithm |
| Schur multiplier | H_2(G,Z) | Finiteness, the covering-group interpretation, and duality with H^2(G,Q/Z) |
| Bogomolov multiplier | Intersection of restriction kernels in H^2(G,Q/Z) for all abelian subgroups | Finiteness, the comparison with HAP's homological dual, and the vanishing theorems |
| Molien series | Determinant sum for the dual of a matrix representation in characteristic zero | Molien's theorem and the permutation-cycle formula |
| McKay arrow multiplicity | Dimension of Hom(W,V tensor U) for simple U and W | A full finite index of irreducible isomorphism classes and the character inner-product formula |

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

To compile the two files, use a Mathlib project:

```bash
python3 check_lean.py --mathlib-project /path/to/existing/mathlib-project --audit-axioms
```

The script uses that project's toolchain and imports.
It gives an error for each Lean warning.
It writes the compiled files into a temporary directory.
The axiom audit rejects axioms other than Lean's standard logical axioms.
