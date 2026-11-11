import Mathlib.RingTheory.PowerSeries.Basic
import Mathlib.Algebra.Field.ZMod
import Mathlib.LinearAlgebra.FiniteDimensional.Basic
import Mathlib.RepresentationTheory.Homological.GroupCohomology.LowDegree

/-!
# Finite-field Betti numbers

This file defines the dimensions of `H^n(G, ZMod p)` with trivial coefficients.
It proves finite dimensionality and the degree-zero dimension.
It also defines a Betti list with a degree limit.
These definitions do not verify the Python/GAP results.
-/

noncomputable section

open CategoryTheory
open scoped BigOperators

namespace FiniteGroupCohomology

variable (G : Type) [Group G] [Finite G] (p : ℕ) [Fact p.Prime]

/-- Each cohomology group has finite dimension.
The cocycle space is a subspace of the cochain space with finite dimension.
Cohomology is a quotient of cocycles. -/
instance finiteDimensionalCohomology (n : ℕ) :
    FiniteDimensional (ZMod p)
      (groupCohomology (Rep.trivial (ZMod p) G (ZMod p)) n) := by
  letI := Fintype.ofFinite G
  let A := Rep.trivial (ZMod p) G (ZMod p)
  letI : IsNoetherian (ZMod p) ((groupCohomology.inhomogeneousCochains A).X n) := by
    change IsNoetherian (ZMod p) ((Fin n → G) → ZMod p)
    infer_instance
  letI : Module.Finite (ZMod p) (groupCohomology.cocycles A n) :=
    Module.Finite.of_injective (groupCohomology.iCocycles A n).hom
      ((ModuleCat.mono_iff_injective _).mp inferInstance)
  exact Module.Finite.of_surjective (groupCohomology.π A n).hom
    ((ModuleCat.epi_iff_surjective _).mp inferInstance)

/-- The degree-`n` Betti number with trivial coefficients in `𝔽_p`. -/
def bettiNumber (G : Type) [Group G] [Finite G] (p : ℕ) [Fact p.Prime] (n : ℕ) : ℕ :=
  Module.finrank (ZMod p) (groupCohomology (Rep.trivial (ZMod p) G (ZMod p)) n)

@[simp]
theorem bettiNumber_zero : bettiNumber G p 0 = 1 := by
  simpa [bettiNumber] using
    (groupCohomology.H0IsoOfIsTrivial (Rep.trivial (ZMod p) G (ZMod p))).toLinearEquiv.finrank_eq

/-- The Betti numbers from degree zero to degree `d`, inclusive. -/
def bettiNumbers (d : ℕ) : List ℕ :=
  List.ofFn fun n : Fin (d + 1) => bettiNumber G p n

@[simp]
theorem length_bettiNumbers (d : ℕ) : (bettiNumbers G p d).length = d + 1 := by
  simp [bettiNumbers]

@[simp]
theorem getElem_bettiNumbers (d n : ℕ) (h : n < (bettiNumbers G p d).length) :
    (bettiNumbers G p d)[n] = bettiNumber G p n := by
  unfold bettiNumbers at h ⊢
  rw [List.getElem_ofFn]

/-- The full Poincare series has the Betti numbers as integer coefficients. -/
def poincareSeries : PowerSeries ℤ :=
  PowerSeries.mk fun n => (bettiNumber G p n : ℤ)

@[simp]
theorem coeff_poincareSeries (n : ℕ) :
    PowerSeries.coeff n (poincareSeries G p) = (bettiNumber G p n : ℤ) := by
  simp [poincareSeries]

@[simp]
theorem constantCoeff_poincareSeries :
    PowerSeries.constantCoeff (poincareSeries G p) = 1 := by
  rw [← PowerSeries.coeff_zero_eq_constantCoeff_apply]
  simp

end FiniteGroupCohomology
