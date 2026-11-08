import Mathlib
import GroupCohomologyInvariants

/-!
# Schur and Bogomolov multipliers, Molien series and McKay multiplicities

Definitions for the four invariants accompanying the finite-field Betti numbers.
`formalisation_gaps.md` records the interpretation and comparison theorems not
proved here. No Python or GAP output is introduced as a Lean axiom.
-/

noncomputable section

open CategoryTheory
open CategoryTheory.MonoidalCategory
open scoped BigOperators

namespace FiniteGroupInvariants

variable (G : Type) [Group G] [Finite G]

/-- The Schur multiplier is second integral homology, not second cohomology. -/
abbrev schurMultiplier := groupHomology (Rep.trivial ℤ G ℤ) 2

/-- The divisible coefficient group `ℚ/ℤ`, with its usual `ℤ`-module structure. -/
abbrev RationalModIntegers := ℚ ⧸ AddSubgroup.zmultiples (1 : ℚ)

/-- Pullback of trivial-coefficient cohomology along a group homomorphism. -/
def pullback {K H : Type} [Group K] [Group H] (k : Type) [CommRing k]
    (M : Type) [AddCommGroup M] [Module k M] (f : H →* K) (n : ℕ) :
    groupCohomology (Rep.trivial k K M) n →ₗ[k]
      groupCohomology (Rep.trivial k H M) n :=
  (groupCohomology.map f
    { hom := ModuleCat.ofHom LinearMap.id
      comm := by intro g; simp } n).hom

/-- Bogomolov multiplier as the intersection over all abelian subgroups. -/
def bogomolovMultiplier : AddSubgroup
    (groupCohomology (Rep.trivial ℤ G RationalModIntegers) 2) :=
  ⨅ (H : Subgroup G) (_ : ∀ a b : H, a * b = b * a),
    AddMonoidHom.ker (pullback ℤ RationalModIntegers H.subtype 2).toAddMonoidHom

/-- Molien's exact formal series for the given characteristic-zero matrix representation.
The determinant uses the dual action. Its equality with the invariant-ring Hilbert
series is not proved here. -/
def molienSeries (k : Type) [Field k] [CharZero k] (ι : Type) [Fintype ι] [DecidableEq ι]
    (ρ : G →* Matrix.GeneralLinearGroup ι k) : PowerSeries k := by
  classical
  letI := Fintype.ofFinite G
  exact (Nat.card G : k)⁻¹ • ∑ g : G,
    let dual : Matrix ι ι k := (↑((ρ g)⁻¹) : Matrix ι ι k).transpose
    let polynomialMatrix : Matrix ι ι (Polynomial k) := dual.map Polynomial.C
    let denominator : Polynomial k := Matrix.det
      ((1 : Matrix ι ι (Polynomial k)) - (Polynomial.X : Polynomial k) • polynomialMatrix)
    (denominator : PowerSeries k)⁻¹

/-- Tensor multiplicity giving the number of McKay arrows from `U` to `W`. -/
def mckayMultiplicity (V U W : FDRep ℂ G) [Simple U] [Simple W] : ℕ :=
  Module.finrank ℂ (W ⟶ (V ⊗ U))

end FiniteGroupInvariants
