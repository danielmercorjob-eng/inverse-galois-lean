import json
import os
import shutil
import subprocess
import sys
import unittest
from dataclasses import replace
from itertools import combinations_with_replacement
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from invgal.backends import InvariantError, ResourceLimit, abelian_group, run_json
from invgal.group import GroupSpec, load_groups
from invgal.invariants import bogomolov_multiplier, mckay_quiver, schur_multiplier
from invgal.series import molien_series

GAP = os.environ.get("INVGAL_GAP", shutil.which("gap"))
M23, PSL27 = load_groups(["M23", "PSL27"])


def spec(name, degree, order, generators):
    return GroupSpec(name=name, latex=name, description=name, degree=degree,
                     order=order, generators=generators)


C2 = spec("C2", 2, 2, [[[1, 2]]])
C3 = spec("C3", 3, 3, [[[1, 2, 3]]])
V4 = spec("V4", 4, 4, [[[1, 2]], [[3, 4]]])
S3 = spec("S3", 3, 6, [[[1, 2, 3]], [[1, 2]]])
TRIVIAL = spec("Trivial", 2, 1, [])


class InterfaceTest(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, "-m", "invgal.invariants", *args],
                              cwd=ROOT, capture_output=True, text=True)

    def test_lists_exactly_ten_invariants(self):
        run = self.cli("--list")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual([line.split()[0] for line in run.stdout.splitlines()],
                         ["integral_cohomology", "poincare_series", "zeros_and_poles",
                          "detection_kernel", "periodicity", "betti", "schur_multiplier",
                          "bogomolov_multiplier", "molien", "mckay"])

    def test_cli_requires_betti_prime(self):
        run = self.cli("--groups", "PSL27", "--invariants", "betti")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("--p is required", run.stderr)

    def test_cli_betti_json(self):
        run = self.cli("--groups", "PSL27", "--invariants", "betti", "--p", "5")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["result"]["betti_numbers"], [1, 0, 0, 0, 0])

    def test_abelian_normalization(self):
        self.assertEqual(abelian_group([0, 4, 3, 2]),
                         dict(free_rank=1, torsion_invariant_factors=[2, 12]))

    def test_backend_failure_cannot_return_partial_json(self):
        for source in ('print("INVGAL_JSON_BEGIN\\n[1]")',
                       'print("INVGAL_JSON_BEGIN\\n[1]\\nINVGAL_JSON_END"); raise SystemExit(1)'):
            with self.assertRaises(InvariantError):
                run_json([sys.executable, "-c", source])

    def test_backend_timeout(self):
        with self.assertRaises(ResourceLimit):
            run_json([sys.executable, "-c", "import time; time.sleep(2)"], timeout=0.02)

    def test_wrong_order_rejected_for_character_calculation(self):
        with self.assertRaisesRegex(ValueError, "declared 5"):
            mckay_quiver(replace(C3, order=5), gap="/nonexistent/gap")

    def test_invalid_representation(self):
        for function in (molien_series, mckay_quiver):
            with self.assertRaisesRegex(ValueError, "natural or regular"):
                function(C3, representation="matrices")


@unittest.skipUnless(GAP, "install GAP/HAP or set INVGAL_GAP")
class GapInvariantTest(unittest.TestCase):
    def setUp(self):
        self.backend = dict(gap=GAP, timeout=120)

    def test_schur_small_groups(self):
        self.assertEqual(schur_multiplier(C3, **self.backend)["torsion_invariant_factors"], [])
        self.assertEqual(schur_multiplier(V4, **self.backend)["torsion_invariant_factors"], [2])

    def test_schur_bundled_groups(self):
        self.assertEqual(schur_multiplier(PSL27, **self.backend)["torsion_invariant_factors"], [2])
        self.assertEqual(schur_multiplier(M23, **self.backend)["torsion_invariant_factors"], [])

    def test_bogomolov_shortcuts_and_general_algorithm(self):
        for group in (V4, S3, PSL27, M23):
            with self.subTest(group=group.name):
                self.assertEqual(bogomolov_multiplier(group, **self.backend),
                                 dict(free_rank=0, torsion_invariant_factors=[]))

    def test_natural_molien_series(self):
        self.assertEqual(molien_series(C2, max_degree=4, **self.backend)["coefficients"], [1, 1, 2, 2, 3])
        self.assertEqual(molien_series(TRIVIAL, max_degree=4, **self.backend)["coefficients"], [1, 2, 3, 4, 5])
        for group, expected in ((PSL27, [1, 1, 2, 4, 7]), (M23, [1, 1, 2, 3, 5])):
            data = molien_series(group, max_degree=4, **self.backend)
            self.assertEqual(data["coefficients"], expected)
            self.assertEqual(sum(t["class_size"] for t in data["terms"]), group.order)
            self.assertTrue(data["full_series"])
        # Independent computation: permutation invariants have a monomial-orbit
        # basis. This does not use conjugacy classes or determinant formulas.
        orbit_counts = []
        for degree in range(5):
            unseen = set(combinations_with_replacement(range(PSL27.degree), degree))
            count = 0
            while unseen:
                first = unseen.pop()
                seen, queue = {first}, [first]
                for monomial in queue:
                    for g in PSL27.perms:
                        image = tuple(sorted(g[i] for i in monomial))
                        if image not in seen:
                            seen.add(image)
                            queue.append(image)
                            unseen.discard(image)
                count += 1
            orbit_counts.append(count)
        self.assertEqual(orbit_counts, [1, 1, 2, 4, 7])

    def test_regular_m23_molien_stays_compressed(self):
        data = molien_series(M23, representation="regular", max_degree=1, **self.backend)
        self.assertEqual(data["dimension"], M23.order)
        self.assertEqual(data["coefficients"], [1, 1])
        self.assertLess(len(data["terms"]), 100)
        for term in data["terms"]:
            self.assertEqual(len(term["cycles"]), 1)
            length, count = term["cycles"][0]
            self.assertEqual(length * count, M23.order)

    def test_mckay_natural_dimension_identities(self):
        for group in (C2, PSL27, M23):
            data = mckay_quiver(group, **self.backend)
            dims = data["vertex_dimensions"]
            self.assertEqual(sum(d*d for d in dims), group.order)
            self.assertEqual(dims[data["unit_index"]], 1)
            self.assertTrue(all(v == "1" for v in data["character_values"][data["unit_index"]]))
            self.assertEqual([sum(a*d for a, d in zip(row, dims)) for row in data["arrows"]],
                             [group.degree*d for d in dims])

    def test_mckay_regular_character_formula(self):
        data = mckay_quiver(PSL27, representation="regular", **self.backend)
        dims = data["vertex_dimensions"]
        self.assertEqual(data["arrows"], [[a*b for b in dims] for a in dims])

    def test_cli_all_five(self):
        names = ["betti", "schur_multiplier", "bogomolov_multiplier", "molien", "mckay"]
        run = subprocess.run([sys.executable, "-m", "invgal.invariants", "--groups", "PSL27",
                              "--invariants", *names, "--p", "2", "--max-degree", "2",
                              "--representation", "regular", "--gap", GAP, "--timeout", "120"],
                             cwd=ROOT, capture_output=True, text=True, check=True, timeout=300)
        rows = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual([row["invariant"] for row in rows], names)
        self.assertTrue(all(row["group"] == "PSL27" for row in rows))
        self.assertEqual(rows[0]["result"]["betti_numbers"], [1, 0, 1])
        self.assertEqual(rows[1]["result"]["torsion_invariant_factors"], [2])
        self.assertEqual(rows[2]["result"]["torsion_invariant_factors"], [])
        self.assertEqual(rows[3]["result"]["representation"], "regular")
        dims = rows[4]["result"]["vertex_dimensions"]
        self.assertEqual(rows[4]["result"]["arrows"], [[a*b for b in dims] for a in dims])


if __name__ == "__main__":
    unittest.main()
