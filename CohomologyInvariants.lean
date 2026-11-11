import FiniteGroupInvariants

/-!
# Integral cohomology, full series, restriction kernels, and periodicity

The coefficients have the trivial action.
These definitions do not verify the Python/GAP results.
`formalisation_gaps.md` identifies the missing comparison theorems.
-/

noncomputable section

namespace FiniteGroupInvariants

variable (G : Type) [Group G] [Finite G]

/-- Integral cohomology with trivial coefficients. The group includes its torsion. -/
abbrev integralCohomology (n : ℕ) := groupCohomology (Rep.trivial ℤ G ℤ) n

/-- Degree-zero integral cohomology is the coefficient group. -/
def integralCohomologyZeroEquiv : integralCohomology G 0 ≃+ ℤ :=
  ((CategoryTheory.forget₂ (ModuleCat ℤ) AddCommGrpCat).mapIso
    (groupCohomology.H0IsoOfIsTrivial (Rep.trivial ℤ G ℤ))).addCommGroupIsoToAddEquiv

/-- The intersection of restriction kernels for a specified subgroup family. -/
def detectionKernel (G : Type) [Group G] [Finite G] (p : ℕ) [Fact p.Prime]
    (family : Set (Subgroup G)) (n : ℕ) :
    Submodule (ZMod p) (groupCohomology (Rep.trivial (ZMod p) G (ZMod p)) n) :=
  ⨅ (H : Subgroup G) (_ : H ∈ family),
    LinearMap.ker (pullback (ZMod p) (ZMod p) H.subtype n)

/-- Essential cohomology in degree `n`. -/
def essentialCohomology (p : ℕ) [Fact p.Prime] (n : ℕ) :=
  detectionKernel G p {H | H ≠ ⊤} n

@[simp]
theorem mem_detectionKernel (p : ℕ) [Fact p.Prime] (family : Set (Subgroup G))
    (n : ℕ) (x : groupCohomology (Rep.trivial (ZMod p) G (ZMod p)) n) :
    x ∈ detectionKernel G p family n ↔
      ∀ H ∈ family, pullback (ZMod p) (ZMod p) H.subtype n x = 0 := by
  simp [detectionKernel]

@[simp]
theorem detectionKernel_empty (p : ℕ) [Fact p.Prime] (n : ℕ) :
    detectionKernel G p ∅ n = ⊤ := by
  simp [detectionKernel]

@[simp]
theorem mem_essentialCohomology (p : ℕ) [Fact p.Prime] (n : ℕ)
    (x : groupCohomology (Rep.trivial (ZMod p) G (ZMod p)) n) :
    x ∈ essentialCohomology G p n ↔
      ∀ H : Subgroup G, H ≠ ⊤ → pullback (ZMod p) (ZMod p) H.subtype n x = 0 := by
  simp [essentialCohomology]

/-- A reduced rational presentation with a certificate for the full series.
This file does not prove that such a certificate exists. -/
structure RationalPoincarePresentation (p : ℕ) [Fact p.Prime] where
  numerator : Polynomial ℚ
  denominator : Polynomial ℚ
  coprime : IsCoprime numerator denominator
  numerator_zero : numerator.coeff 0 = 1
  denominator_zero : denominator.coeff 0 = 1
  series_agreement :
    PowerSeries.map (Int.castRingHom ℚ) (FiniteGroupCohomology.poincareSeries G p) *
      (denominator : PowerSeries ℚ) = (numerator : PowerSeries ℚ)

/-- Multiplicity of an algebraic zero of the full rational series in the certificate. -/
def zeroMultiplicity (p : ℕ) [Fact p.Prime]
    (S : RationalPoincarePresentation G p) (z : ℂ) : ℕ :=
  Polynomial.rootMultiplicity z (S.numerator.map (algebraMap ℚ ℂ))

/-- Multiplicity of an algebraic pole after cancellation. The polynomials in `S` are coprime. -/
def poleMultiplicity (p : ℕ) [Fact p.Prime]
    (S : RationalPoincarePresentation G p) (z : ℂ) : ℕ :=
  Polynomial.rootMultiplicity z (S.denominator.map (algebraMap ℚ ℂ))

/-- All abelian subgroups are cyclic.
This file does not prove equivalence with integral Tate periodicity. -/
def periodicityCriterion : Prop :=
  ∀ H : Subgroup G, (∀ a b : H, a * b = b * a) → IsCyclic H

/-- Least positive degree with integral cohomology cyclic of order `|G|`, or infinity.
The comparison with Tate periodicity is a missing theorem. -/
def integralPeriod : WithTop ℕ := by
  classical
  exact if h : ∃ d, 0 < d ∧ Nonempty (integralCohomology G d ≃+ ZMod (Nat.card G)) then
      ↑(Nat.find h)
    else ⊤

omit [Finite G] in
theorem integralPeriod_eq_top_iff :
    integralPeriod G = ⊤ ↔
      ¬ ∃ d, 0 < d ∧ Nonempty (integralCohomology G d ≃+ ZMod (Nat.card G)) := by
  classical
  simp [integralPeriod]

end FiniteGroupInvariants
