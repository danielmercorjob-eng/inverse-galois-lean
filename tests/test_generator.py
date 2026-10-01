import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from invgal.group import GroupSpec, load_groups  # noqa: E402
from invgal.poly import KnownPolynomial, count_real_roots  # noqa: E402
from invgal.variants import GENERATED_MARKER, Variant, render  # noqa: E402

M23, PSL27 = load_groups(["M23", "PSL27"])


def generate(fc_root, *args, check=True):
    return subprocess.run([sys.executable, str(ROOT / "generate.py"), "--fc-root", str(fc_root),
                           *args], capture_output=True, text=True, check=check)


def fake_fc_root(tmp):
    root = Path(tmp)
    (root / "lakefile.toml").touch()
    (root / "FormalConjecturesUtil").mkdir()
    return root


class GroupTest(unittest.TestCase):
    def test_group_files_verify(self):
        for g in load_groups():
            self.assertEqual(g.verify(), g.order)

    def test_real_root_counts(self):
        # Involutions of M23 have cycle type 1^7 2^8; those of PSL(2,7) fix a line of the
        # Fano plane, i.e. 3 points.
        self.assertEqual(M23.real_root_counts(), [23, 7])
        self.assertEqual(PSL27.real_root_counts(), [7, 3])

    def test_wrong_order_is_rejected(self):
        g = GroupSpec(**{**json.loads((ROOT / "groups/PSL27.json").read_text()), "order": 21})
        with self.assertRaises(AssertionError):
            g.verify()

    def test_intransitive_group(self):
        g = GroupSpec(name="V4", latex="V_4", description="a Klein four-group", degree=4,
                      order=4, generators=[[[1, 2]], [[3, 4]]])
        self.assertFalse(g.transitive)
        self.assertEqual(g.verify(), 4)
        with self.assertRaises(ValueError):
            Variant(g, normalization="monic_irreducible")


class PolynomialTest(unittest.TestCase):
    def test_count_real_roots(self):
        self.assertEqual(count_real_roots([3, -7, 0, 0, 0, 0, 0, 1]), 3)  # x^7 - 7x + 3
        self.assertEqual(count_real_roots([1, 0, 1]), 0)
        self.assertEqual(count_real_roots([0, -1, 0, 1]), 3)
        self.assertEqual(count_real_roots([-2, 0, 0, 1]), 1)

    def test_known_polynomial_properties(self):
        k = KnownPolynomial.from_json({"coefficients": [3, -7, 0, 0, 0, 0, 0, 1]})
        self.assertEqual((k.degree, k.digits, k.monic, k.real_roots), (7, 2, True, 3))
        with self.assertRaises(ValueError):
            KnownPolynomial.from_json({"coefficients": [3, -7, 1], "real_roots": 0})


class StatusTest(unittest.TestCase):
    def test_m23(self):
        self.assertEqual(Variant(M23, digits=100).status, "solved")
        self.assertEqual(Variant(M23, digits=200, action="roots").status, "solved")
        self.assertEqual(Variant(M23, digits=99).status, "unknown")
        self.assertEqual(Variant(M23, digits=100, normalization="monic").status, "unknown")
        self.assertEqual(Variant(M23, normalization="monic_irreducible").status, "solved")
        self.assertEqual(Variant(M23, real_roots=7).status, "unknown")
        self.assertEqual(Variant(M23, kind="realizable").status, "solved")
        self.assertEqual(Variant(M23, kind="regular").status, "open")

    def test_psl27_uses_known_polynomial(self):
        self.assertEqual(Variant(PSL27, digits=2, normalization="monic_irreducible",
                                 real_roots=3, action="roots").status, "solved")
        self.assertEqual(Variant(PSL27, digits=2, real_roots=7).status, "unknown")
        self.assertEqual(Variant(PSL27, digits=1).status, "unknown")
        self.assertEqual(Variant(PSL27, kind="regular").status, "unknown")

    def test_impossible_real_root_count(self):
        with self.assertRaises(ValueError):
            Variant(M23, real_roots=5)


class RenderTest(unittest.TestCase):
    def test_rendered_files(self):
        for v in [Variant(M23, digits=100), Variant(PSL27, kind="regular"),
                  Variant(PSL27, action="roots", normalization="monic_irreducible", digits=2,
                          real_roots=3)]:
            text = render(v)
            self.assertEqual(len(re.findall(r"\bsorry\b", text)), 1, v.stem)
            self.assertIn(f"@[category research {v.category}, AMS 12]", text)
            self.assertIn(f"theorem {v.theorem_name} :", text)
            self.assertIn(f"namespace InverseGaloisVariants.{v.group.name}{v.stem}", text)
            self.assertIn("public import FormalConjecturesUtil", text)
            self.assertEqual(v.needs_complex_splits(), "splits_ℚ_ℂ" in text)
            self.assertIn(f"def {v.group.name} : Subgroup (Equiv.Perm (Fin {v.group.degree}))",
                          text)

    def test_names(self):
        v = Variant(PSL27, normalization="monic", digits=2, real_roots=3)
        self.assertEqual(v.stem, "PolyGalIsoMonicDigits2RealRoots3")
        self.assertEqual(v.theorem_name, "psl27_poly_gal_iso_monic_digits_2_real_roots_3")


class CliTest(unittest.TestCase):
    def test_default_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fake_fc_root(tmp)
            generate(root)
            base = root / "FormalConjectures/Other/InverseGalois"
            for g in ("M23", "PSL27"):
                files = list((base / g).glob("*.lean"))
                self.assertEqual(len(files), 38, g)
                for f in files:
                    self.assertEqual(len(re.findall(r"\bsorry\b", f.read_text())), 1, f.name)

    def test_skip_unknown(self):
        out = generate(Path("."), "--list", "--skip-unknown").stdout
        self.assertNotIn("unknown", out)

    def test_clean_keeps_hand_written_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fake_fc_root(tmp)
            out = root / "FormalConjectures/Other/InverseGalois/M23"
            generate(root, "--groups", "M23")
            (out / "HandWritten.lean").write_text("-- not generated\n")
            generate(root, "--groups", "M23", "--clean", "--digits", "none",
                     "--real-roots", "none", "--actions", "abstract")
            names = {f.name for f in out.glob("*.lean")}
            self.assertIn("HandWritten.lean", names)
            self.assertEqual(len(names), 1 + 2 + 3)
            for f in out.glob("Poly*.lean"):
                self.assertIn(GENERATED_MARKER, f.read_text())

    def test_rejects_non_formal_conjectures_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertNotEqual(generate(Path(tmp), check=False).returncode, 0)

    def test_unknown_group(self):
        r = generate(Path("."), "--list", "--groups", "Nope", check=False)
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
