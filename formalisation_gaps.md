# Formalisation scope for the five invariants

`GroupCohomologyInvariants.lean` and `FiniteGroupInvariants.lean` define all five
selected quantities using actual Mathlib constructions. They contain no
`sorry` declarations or new axioms. They were checked with Lean 4.27.0 and
Mathlib commit `a3a10db0e9d66acbebf76c5e6a135066525ac900`.

| Invariant | Definition supplied | Additional theorems not supplied |
|---|---|---|
| Finite-field Betti numbers | `Module.finrank` of actual trivial-coefficient group cohomology | Comparison with the Python/HAP resolution and fusion algorithm. Finite dimensionality, b0=1, list length and list entries are proved. |
| Schur multiplier | Actual second integral group homology | Finiteness, covering-group interpretation and duality with H^2(G,Q/Z). |
| Bogomolov multiplier | Intersection of restriction kernels in actual H^2(G,Q/Z), over all abelian subgroups | Finiteness, duality with HAP's nonabelian-exterior-square quotient, and the abelian/simple vanishing theorems used by Python. |
| Molien series | Exact finite determinant sum on the dual of a given characteristic-zero matrix representation | Molien's theorem identifying the series with the invariant-ring Hilbert series, and the class-cycle formula used by Python. |
| McKay arrow multiplicity | Dimension of equivariant Hom(W,V tensor U), with simple U and W | Finite enumeration of irreducible isomorphism classes and the character inner-product computation. |

The Bogomolov coefficients are the actual additive quotient Q/Z. Restriction
maps are Mathlib's group-cohomology pullbacks, using identity coefficient maps;
they are not arbitrary maps supplied as assumptions. The definition is an
additive subgroup, avoiding any ambiguity between equivalent integer-module
instances on Q/Z.

The Molien definition takes a representation into a general linear matrix
group, uses the inverse transpose for the dual action, and produces an exact
formal power series. Its mathematical definition applies more generally than
the natural/regular permutation representations supported by Python.

The McKay definition gives the intrinsic arrow rule. Vertices are irreducible
representations up to isomorphism. Python provides a finite indexing through
GAP's character table; a formal enumeration and proof that this indexing is
complete are separate from the arrow definition.

The finite-generation and invariant-theory comparison theorems above require
substantial additional Lean development. None is replaced by a postulated axiom
or a constant containing a Python result. These files do not certify the
computations or connect the JSON permutation groups to the abstract group G.

To recheck both modules without modifying an existing Mathlib project:

```bash
python3 check_lean.py --mathlib-project /path/to/existing/mathlib-project --audit-axioms
```

The helper uses that project's toolchain and imports, treats warnings as errors,
and writes compiled modules to a temporary directory.
