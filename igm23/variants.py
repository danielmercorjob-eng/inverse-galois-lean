"""Variants of the inverse Galois problem for M23 and their Lean statements.

Each `Variant` becomes one self-contained Lean file in the Formal Conjectures layout,
with exactly one `sorry`: the proof of the main theorem.
"""

import textwrap
from dataclasses import dataclass
from typing import Optional

from .group import DEGREE, GEN1_CYCLES, GEN2_CYCLES, cycles_to_str, from_cycles, zero_indexed

REFERENCE_URL = "https://epoch.ai/frontiermath/open-problems/inverse-galois"
REFERENCE = f"[Epoch AI, FrontierMath Open Problems: Inverse Galois problem for M23]({REFERENCE_URL})"

KINDS = ("polynomial", "realizable", "regular")
ACTIONS = ("abstract", "roots")
NORMALIZATIONS = ("any", "monic", "monic_irreducible")
# Complex conjugation acts on the roots as an element of order at most 2 of M23. The
# involutions of M23 have cycle type 1^7 2^8, so a polynomial with Galois group M23 has
# either 23 or 7 real roots. Other counts give provably false statements.
REAL_ROOT_COUNTS = (23, 7)
# Epoch AI reports that a polynomial with coefficients of fewer than 100 digits is known.
KNOWN_DIGIT_BOUND = 100

QPOLY = "(f.map (Int.castRingHom ℚ))"


@dataclass(frozen=True)
class Variant:
    kind: str = "polynomial"
    action: str = "abstract"
    normalization: str = "any"
    digits: Optional[int] = KNOWN_DIGIT_BOUND  # "fewer than `digits` decimal digits"
    real_roots: Optional[int] = None

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"unknown kind {self.kind!r}")
        if self.kind != "polynomial":
            return
        if self.action not in ACTIONS:
            raise ValueError(f"unknown action {self.action!r}")
        if self.normalization not in NORMALIZATIONS:
            raise ValueError(f"unknown normalization {self.normalization!r}")
        if self.digits is not None and self.digits < 1:
            raise ValueError("digit bound must be at least 1")
        if self.real_roots is not None and self.real_roots not in REAL_ROOT_COUNTS:
            raise ValueError(
                f"real root count must be one of {REAL_ROOT_COUNTS}: complex conjugation "
                "acts as an involution of M23, and these fix exactly 7 points")

    # -- naming -------------------------------------------------------------

    @property
    def stem(self) -> str:
        """The Lean module (file) name, in UpperCamelCase."""
        if self.kind == "realizable":
            return "Realizable"
        if self.kind == "regular":
            return "RegularOverRatFunc"
        parts = ["Poly", {"abstract": "GalIso", "roots": "RootAction"}[self.action]]
        parts.append({"any": "", "monic": "Monic", "monic_irreducible": "MonicIrreducible"}
                     [self.normalization])
        parts.append("Unbounded" if self.digits is None else f"Digits{self.digits}")
        parts.append({None: "", 23: "TotallyReal", 7: "SevenRealRoots"}[self.real_roots])
        return "".join(parts)

    @property
    def theorem_name(self) -> str:
        out = []
        for i, ch in enumerate(self.stem):
            if ch.isupper() and i > 0 and not self.stem[i - 1].isupper():
                out.append("_")
            elif ch.isdigit() and i > 0 and not self.stem[i - 1].isdigit():
                out.append("_")
            out.append(ch.lower())
        return "m23_" + "".join(out)

    # -- status ---------------------------------------------------------------

    @property
    def status(self) -> str:
        """`solved` or `open`, following the Formal Conjectures `category` attribute.

        Conservative: a variant is `solved` only when it follows from the Epoch AI result
        (a polynomial of degree 23 with coefficients of fewer than 100 digits) by an
        elementary argument. Everything else is marked `open`.
        """
        if self.kind == "realizable":
            return "solved"
        if self.kind == "regular":
            return "open"
        if self.real_roots is not None:
            return "open"  # the signature of the known polynomial is not recorded here
        if self.digits is None:
            # A transitive Galois group makes the polynomial irreducible, and scaling
            # makes it monic.
            return "solved"
        if self.digits >= KNOWN_DIGIT_BOUND and self.normalization == "any":
            return "solved"
        return "open"

    # -- Lean -------------------------------------------------------------------

    def title(self) -> str:
        if self.kind == "realizable":
            return "$M_{23}$ is a Galois group over $\\mathbb{Q}$"
        if self.kind == "regular":
            return "$M_{23}$ as a regular Galois group over $\\mathbb{Q}(t)$"
        bits = []
        if self.normalization == "monic":
            bits.append("monic")
        elif self.normalization == "monic_irreducible":
            bits.append("monic irreducible")
        bits.append("polynomial")
        title = "A degree-23 " + " ".join(bits) + " with Galois group $M_{23}$"
        extra = []
        if self.digits is not None:
            extra.append(f"coefficients of fewer than {self.digits} digits")
        if self.real_roots == 23:
            extra.append("all roots real")
        elif self.real_roots is not None:
            extra.append(f"exactly {self.real_roots} real roots")
        if self.action == "roots":
            extra.append("as a permutation group of the roots")
        return title + (" (" + "; ".join(extra) + ")" if extra else "")

    def docstring(self) -> str:
        if self.kind == "realizable":
            return ("There is a finite Galois extension $L / \\mathbb{Q}$ whose Galois group "
                    "is isomorphic to $M_{23}$.")
        if self.kind == "regular":
            return ("There is a finite Galois extension $L / \\mathbb{Q}(t)$ with Galois group "
                    "isomorphic to $M_{23}$ in which $\\mathbb{Q}$ is algebraically closed.")
        adj = {"any": "", "monic": "monic ", "monic_irreducible": "monic "}[self.normalization]
        s = f"There is a {adj}polynomial $f \\in \\mathbb{{Z}}[x]$ of degree $23$"
        conds = []
        if self.normalization == "monic_irreducible":
            conds.append("irreducible over $\\mathbb{Q}$")
        if self.digits is not None:
            conds.append(f"whose coefficients each have fewer than ${self.digits}$ decimal digits")
        if self.real_roots == 23:
            conds.append("with all $23$ roots real")
        elif self.real_roots is not None:
            conds.append(f"with exactly ${self.real_roots}$ real roots")
        if conds:
            s += ", " + ", ".join(conds) + ","
        if self.action == "abstract":
            s += " whose Galois group over $\\mathbb{Q}$ is isomorphic to $M_{23}$."
        else:
            s += (" whose Galois group acts on the $23$ complex roots exactly as $M_{23}$ acts on"
                  " $\\{0, \\dots, 22\\}$, for some labelling of the roots.")
        return s

    def statement(self) -> str:
        """The Lean statement, indented for use after `theorem name :`."""
        if self.kind == "realizable":
            return ("∃ (L : Type) (_ : Field L) (_ : Algebra ℚ L),\n"
                    "      FiniteDimensional ℚ L ∧ IsGalois ℚ L ∧ Nonempty ((L ≃ₐ[ℚ] L) ≃* M23)")
        if self.kind == "regular":
            emb = "((algebraMap (RatFunc ℚ) L).comp (algebraMap ℚ (RatFunc ℚ)))"
            return ("∃ (L : Type) (_ : Field L) (_ : Algebra (RatFunc ℚ) L),\n"
                    "      FiniteDimensional (RatFunc ℚ) L ∧ IsGalois (RatFunc ℚ) L ∧\n"
                    "      Nonempty ((L ≃ₐ[RatFunc ℚ] L) ≃* M23) ∧\n"
                    f"      ∀ x : L, {emb}.IsIntegralElem x →\n"
                    f"        x ∈ {emb}.range")
        conds = ["f.natDegree = 23"]
        if self.normalization in ("monic", "monic_irreducible"):
            conds.append("f.Monic")
        if self.normalization == "monic_irreducible":
            conds.append(f"Irreducible {QPOLY}")
        if self.digits is not None:
            conds.append(f"(∀ i, (Nat.digits 10 (f.coeff i).natAbs).length < {self.digits})")
        if self.real_roots is not None:
            conds.append(f"({QPOLY}.rootSet ℝ).ncard = {self.real_roots}")
        if self.action == "abstract":
            conds.append(f"Nonempty ({QPOLY}.Gal ≃* M23)")
        else:
            conds.append(f"∃ e : {QPOLY}.rootSet ℂ ≃ Fin 23,\n"
                         f"        Set.range (fun g ↦ e.permCongr (Gal.galActionHom {QPOLY} ℂ g)) =\n"
                         "          (M23 : Set (Equiv.Perm (Fin 23)))")
        return "∃ f : ℤ[X], " + " ∧\n      ".join(conds)

    def needs_complex_splits(self) -> bool:
        return self.kind == "polynomial" and self.action == "roots"


def _formperm(cycle):
    return "[" + ", ".join(map(str, cycle)) + "].formPerm"


def _gen2_spot_checks():
    """Values of `gen₂` (0-indexed) checked by `decide` in each generated file:
    one step of each cycle, and the first three fixed points."""
    perm = from_cycles(GEN2_CYCLES)
    points = [c[0] for c in zero_indexed(GEN2_CYCLES)]
    points += [i for i in range(DEGREE) if perm[i] == i][:3]
    return [(i, perm[i]) for i in points]


COPYRIGHT_YEAR = 2026
HEADER = f"""/-
Copyright {COPYRIGHT_YEAR} The Formal Conjectures Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-/
module

public import FormalConjecturesUtil
"""

GENERATED_MARKER = "Generated by inverse-galois-m23"


def _wrap(text: str, first: str = "", width: int = 100) -> str:
    """Wrap `text` to `width` columns; `first` prefixes the first line only."""
    return textwrap.fill(text, width=width, initial_indent=first, subsequent_indent="",
                         break_long_words=False, break_on_hyphens=False)


def _check_lines(text: str, stem: str, width: int = 100):
    for n, line in enumerate(text.splitlines(), 1):
        if len(line) > width and "http" not in line:
            raise ValueError(f"{stem}.lean:{n} is longer than {width} characters")


def render(v: Variant, namespace_root: str = "InverseGaloisM23") -> str:
    """The full contents of the Lean file for `v`."""
    gen1 = "(1 2 … 23)"
    gen2_cycles = cycles_to_str(GEN2_CYCLES)
    gen2 = " *\n    ".join(_formperm(c) for c in zero_indexed(GEN2_CYCLES))
    checks = " ∧\n    ".join(f"gen₂ {i} = {j}" for i, j in _gen2_spot_checks())
    local_instance = ("\nattribute [local instance] Polynomial.Gal.splits_ℚ_ℂ\n"
                      if v.needs_complex_splits() else "")
    status_note = {
        "solved": "Epoch AI reports the existence of such a polynomial as solved "
                  "(Huang et al.); there is no formal proof.",
        "open": "This variant is marked open because we know of no source that settles it.",
    }[v.status]
    definition_note = (
        f"Here $M_{{23}}$ is the subgroup of `Equiv.Perm (Fin 23)` generated by `{gen1}` and "
        f"`{gen2_cycles}` (written 1-indexed). This group is transitive of order $10200960$, "
        "and $M_{23}$ is the only transitive group of degree $23$ of that order.")
    text = f"""{HEADER}
/-!
# Inverse Galois problem for $M_{{23}}$

{_wrap("Variant: " + v.title() + ".")}

{_wrap(v.docstring())}

{_wrap(status_note)}

{_wrap(definition_note)}

*Reference:* {REFERENCE}

{GENERATED_MARKER}.
-/

@[expose] public section

namespace {namespace_root}.{v.stem}

open Polynomial
{local_instance}
/-- The $23$-cycle `{gen1}`, written 0-indexed as `i ↦ i + 1`. -/
def gen₁ : Equiv.Perm (Fin 23) := (List.finRange 23).formPerm

/-- The permutation `{gen2_cycles}`,
with every point shifted down by one. -/
def gen₂ : Equiv.Perm (Fin 23) :=
    {gen2}

/-- The Mathieu group $M_{{23}}$ in its natural action on $23$ points. -/
def M23 : Subgroup (Equiv.Perm (Fin 23)) := Subgroup.closure {{gen₁, gen₂}}

@[category test, AMS 20]
theorem gen₁_spec : gen₁ 0 = 1 ∧ gen₁ 22 = 0 := by decide

@[category test, AMS 20]
theorem gen₂_spec :
    {checks} := by
  decide

{_wrap(v.docstring() + " -/", first="/-- ")}
@[category research {v.status}, AMS 12]
theorem {v.theorem_name} :
    {v.statement()} := by
  sorry

end {namespace_root}.{v.stem}
"""
    _check_lines(text, v.stem)
    return text
