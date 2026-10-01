import random
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from igm23.group import (DEGREE, GEN1_CYCLES, GEN2_CYCLES, ID, from_cycles, mul,  # noqa: E402
                         verify_m23)
from igm23.variants import GENERATED_MARKER, Variant, render  # noqa: E402


def generate(fc_root, *args):
    return subprocess.run([sys.executable, str(ROOT / "generate.py"), "--fc-root", str(fc_root),
                           *args], capture_output=True, text=True, check=True).stdout


def fake_fc_root(tmp):
    root = Path(tmp)
    (root / "lakefile.toml").touch()
    (root / "FormalConjecturesUtil").mkdir()
    return root


class GroupTest(unittest.TestCase):
    def test_generators_generate_m23(self):
        self.assertEqual(verify_m23(), 10200960)

    def test_involutions_fix_seven_points(self):
        # Justifies the restriction of real root counts to 23 and 7.
        gens = [from_cycles(GEN1_CYCLES), from_cycles(GEN2_CYCLES)]
        rng = random.Random(0)
        found = 0
        for _ in range(200):
            g = ID
            for _ in range(30):
                g = mul(g, rng.choice(gens))
            order, h = 1, g
            while h != ID:
                h, order = mul(h, g), order + 1
            if order % 2 == 0:
                inv = ID
                for _ in range(order // 2):
                    inv = mul(inv, g)
                self.assertEqual(sum(inv[i] == i for i in range(DEGREE)), 7)
                found += 1
        self.assertGreater(found, 10)


class VariantTest(unittest.TestCase):
    def test_status(self):
        self.assertEqual(Variant().status, "solved")
        self.assertEqual(Variant(action="roots").status, "solved")
        self.assertEqual(Variant(digits=200).status, "solved")
        self.assertEqual(Variant(digits=99).status, "open")
        self.assertEqual(Variant(normalization="monic").status, "open")
        self.assertEqual(Variant(normalization="monic", digits=None).status, "solved")
        self.assertEqual(Variant(real_roots=7, digits=None).status, "open")
        self.assertEqual(Variant(kind="realizable").status, "solved")
        self.assertEqual(Variant(kind="regular").status, "open")

    def test_rejects_impossible_real_root_count(self):
        with self.assertRaises(ValueError):
            Variant(real_roots=5)

    def test_rendered_file(self):
        for v in [Variant(), Variant(action="roots", normalization="monic_irreducible",
                                     digits=50, real_roots=23),
                  Variant(kind="realizable"), Variant(kind="regular")]:
            text = render(v)
            self.assertEqual(len(re.findall(r"\bsorry\b", text)), 1, v.stem)
            self.assertIn(f"@[category research {v.status}, AMS 12]", text)
            self.assertIn(f"theorem {v.theorem_name} :", text)
            self.assertIn(f"namespace InverseGaloisM23.{v.stem}", text)
            self.assertTrue(text.startswith("/-\nCopyright"))
            self.assertIn("public import FormalConjecturesUtil", text)
            self.assertEqual(v.needs_complex_splits(), "splits_ℚ_ℂ" in text)

    def test_theorem_name(self):
        v = Variant(normalization="monic", digits=50, real_roots=7)
        self.assertEqual(v.stem, "PolyGalIsoMonicDigits50SevenRealRoots")
        self.assertEqual(v.theorem_name, "m23_poly_gal_iso_monic_digits_50_seven_real_roots")


class CliTest(unittest.TestCase):
    def test_default_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fake_fc_root(tmp)
            generate(root, "--skip-group-check")
            files = sorted((root / "FormalConjectures/Other/InverseGaloisM23").glob("*.lean"))
            self.assertEqual(len(files), 38)
            for f in files:
                self.assertEqual(len(re.findall(r"\bsorry\b", f.read_text())), 1, f.name)

    def test_clean_keeps_hand_written_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fake_fc_root(tmp)
            out = root / "FormalConjectures/Other/InverseGaloisM23"
            generate(root, "--skip-group-check")
            (out / "HandWritten.lean").write_text("-- not generated\n")
            generate(root, "--skip-group-check", "--clean", "--digits", "100",
                     "--real-roots", "none", "--actions", "abstract")
            names = {f.name for f in out.glob("*.lean")}
            self.assertIn("HandWritten.lean", names)
            self.assertEqual(len(names), 1 + 2 + 3)
            for f in out.glob("Poly*.lean"):
                self.assertIn(GENERATED_MARKER, f.read_text())

    def test_rejects_non_formal_conjectures_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, str(ROOT / "generate.py"), "--fc-root", tmp,
                                "--skip-group-check"], capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
