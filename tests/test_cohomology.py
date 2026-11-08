import json
import os
import shutil
import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from invgal.backends import InvariantError
from invgal.cohomology import compute_cohomology
from invgal.group import GroupSpec, load_groups

M23, PSL27 = load_groups(["M23", "PSL27"])
GAP = os.environ.get("INVGAL_GAP", shutil.which("gap"))


def small_group(name, degree, order, generators):
    return GroupSpec(name=name, latex=name, description=name, degree=degree,
                     order=order, generators=generators)


C3 = small_group("C3", 3, 3, [[[1, 2, 3]]])
C4 = small_group("C4", 4, 4, [[[1, 2, 3, 4]]])
V4 = small_group("V4", 4, 4, [[[1, 2]], [[3, 4]]])
S3 = small_group("S3", 3, 6, [[[1, 2, 3]], [[1, 2]]])


class CohomologyTest(unittest.TestCase):
    def test_coprime_characteristic_needs_no_backend(self):
        for group in (M23, PSL27):
            result = compute_cohomology(group, 13, 6, gap="/nonexistent/gap")
            self.assertEqual(result.betti_numbers, (1, 0, 0, 0, 0, 0, 0))
            self.assertEqual(result.max_degree, 6)

    def test_degree_zero_in_modular_characteristic_needs_no_backend(self):
        self.assertEqual(compute_cohomology(C3, 3, 0, gap="/nonexistent/gap").betti_numbers, (1,))

    def test_trivial_group(self):
        for generators in ([], [[]]):
            group = small_group("Trivial", 2, 1, generators)
            self.assertEqual(compute_cohomology(group, 2, 4).betti_numbers, (1, 0, 0, 0, 0))

    def test_wrong_order_rejected_before_shortcut(self):
        with self.assertRaisesRegex(ValueError, "declared 5"):
            compute_cohomology(replace(C3, order=5), 7, 2)

    def test_malformed_permutation_rejected(self):
        with self.assertRaisesRegex(ValueError, "permutation"):
            compute_cohomology(replace(C3, generators=[[[1, 2], [2, 3]]]), 3, 2)

    def test_invalid_parameters(self):
        for p in (-3, 0, 1, 4, 9, 25, 2.0, True):
            with self.subTest(p=p), self.assertRaisesRegex(ValueError, "prime integer"):
                compute_cohomology(C3, p, 2)
        for degree in (-1, 1.5, True):
            with self.assertRaisesRegex(ValueError, "max_degree"):
                compute_cohomology(C3, 3, degree)
        for timeout in (0, -1, float("inf"), float("nan"), None):
            with self.assertRaisesRegex(ValueError, "timeout"):
                compute_cohomology(C3, 3, 2, timeout=timeout)

    def test_missing_gap(self):
        with self.assertRaisesRegex(InvariantError, "cannot execute"):
            compute_cohomology(C3, 3, 2, gap="/nonexistent/gap")

    def test_incomplete_or_invalid_betti_sequence_rejected(self):
        for values in ([1], [0, 1, 1], [1, -1, 1], [1, True, 1], "111"):
            with patch("invgal.cohomology.gap_compute", return_value=values):
                with self.assertRaisesRegex(InvariantError, "Betti sequence"):
                    compute_cohomology(C3, 3, 2)

    def test_cli_json(self):
        run = subprocess.run([sys.executable, "-m", "invgal.cohomology", "--groups", "PSL27",
                              "--p", "5", "--max-degree", "3"],
                             cwd=ROOT, capture_output=True, text=True, check=True)
        data = json.loads(run.stdout)
        self.assertEqual(data["betti_numbers"], [1, 0, 0, 0])
        self.assertEqual(data["max_degree"], 3)
        self.assertEqual(data["p"], 5)


@unittest.skipUnless(GAP, "install GAP/HAP or set INVGAL_GAP")
class GapCohomologyTest(unittest.TestCase):
    def compute(self, group, p, degree):
        return compute_cohomology(group, p, degree, gap=GAP, timeout=120).betti_numbers

    def test_cyclic_groups(self):
        self.assertEqual(self.compute(C3, 3, 5), (1,) * 6)
        self.assertEqual(self.compute(C4, 2, 5), (1,) * 6)

    def test_elementary_abelian_group(self):
        self.assertEqual(self.compute(V4, 2, 4), (1, 2, 3, 4, 5))

    def test_fusion_changes_sylow_answer(self):
        self.assertEqual(self.compute(S3, 3, 7), (1, 0, 0, 1, 1, 0, 0, 1))
        self.assertEqual(self.compute(S3, 2, 4), (1,) * 5)

    def test_degree_one(self):
        self.assertEqual(self.compute(C3, 3, 1), (1, 1))
        self.assertEqual(self.compute(PSL27, 2, 1), (1, 0))

    def test_psl27(self):
        self.assertEqual(self.compute(PSL27, 2, 4), (1, 0, 1, 2, 1))

    def test_m23(self):
        self.assertEqual(self.compute(M23, 23, 22), (1,) + (0,) * 20 + (1, 1))


if __name__ == "__main__":
    unittest.main()
