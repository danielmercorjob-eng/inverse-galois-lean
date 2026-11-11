import json
import os
import shutil
import subprocess
import sys
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from invgal.backends import InvariantError, ResourceLimit, python_compute
from invgal.cochains import BarComplex, LinearMap
from invgal.cohomology import compute_cohomology
from invgal.cohomology_series import hilbert_poincare_series
from invgal.detection import detection_kernel
from invgal.group import GroupSpec, load_groups
from invgal.invariants import cohomology_groups, integral_periodicity
from invgal.series import RationalSeries, zeros_and_poles

GAP = os.environ.get('INVGAL_GAP', shutil.which('gap'))
M23, PSL27 = load_groups(['M23', 'PSL27'])


def spec(name, degree, order, generators):
    return GroupSpec(name=name, latex=name, description=name, degree=degree,
                     order=order, generators=generators)


TRIVIAL = spec('Trivial', 2, 1, [])
C2 = spec('C2', 2, 2, [[[1, 2]]])
C3 = spec('C3', 3, 3, [[[1, 2, 3]]])
C4 = spec('C4', 4, 4, [[[1, 2, 3, 4]]])
V4 = spec('V4', 4, 4, [[[1, 2]], [[3, 4]]])
S3 = spec('S3', 3, 6, [[[1, 2, 3]], [[1, 2]]])
Q8 = spec('Q8', 8, 8, [[[1, 2, 3, 4], [5, 6, 7, 8]],
                        [[1, 5, 3, 7], [2, 8, 4, 6]]])


class CohomologyInterfaceTest(unittest.TestCase):
    def test_rational_cancellation(self):
        series = RationalSeries((1, 1), (1, 0, -1))
        self.assertEqual(series.numerator, (1,))
        self.assertEqual(series.denominator, (1, -1))
        self.assertEqual(series.coefficients(8), (1,)*9)
        self.assertEqual(RationalSeries((2,), (2, -1)).coefficients(2),
                         (1, Fraction(1, 2), Fraction(1, 4)))
        for a, b in (((1,), (0, 1)), ((0,), (1,)), ((2,), (1,))):
            with self.assertRaises(ValueError):
                RationalSeries(a, b)

    def test_constant_series_still_validates_group_order(self):
        series = RationalSeries((1,), (1,))
        with self.assertRaisesRegex(ValueError, 'declared 5'):
            zeros_and_poles(replace(C3, order=5), series, gap='/nonexistent/gap')
        result = zeros_and_poles(C3, series, gap='/nonexistent/gap')
        self.assertEqual(result['zeros'], [])
        self.assertEqual(result['poles'], [])
        self.assertEqual(result['pole_order_at_one'], 0)
        self.assertEqual(result['least_eventual_quasipolynomial_period'], 1)

    def test_betti_prefix_is_not_full_series(self):
        with self.assertRaises(TypeError):
            zeros_and_poles(C3, [1, 1, 1])

    def test_coprime_series_and_essential_vanishing(self):
        for group in (PSL27, M23):
            series = hilbert_poincare_series(group, 13, gap='/nonexistent/gap')
            self.assertEqual(series.coefficients(4), (1, 0, 0, 0, 0))
            result = detection_kernel(group, 2, max_degree=4, gap='/nonexistent/gap')
            self.assertEqual([x['kernel_dimension'] for x in result['degrees']], [0]*5)
            self.assertFalse(result['full_presentation'])

    def test_validation_before_shortcuts(self):
        for p in (True, 2.0, 1, 4):
            with self.assertRaises(ValueError):
                hilbert_poincare_series(C3, p)
            with self.assertRaises(ValueError):
                detection_kernel(PSL27, p, max_degree=2)
        for function in (hilbert_poincare_series,
                         lambda g, p: detection_kernel(g, p, max_degree=2)):
            with self.assertRaisesRegex(ValueError, 'declared'):
                function(replace(C3, order=5), 7)
        for degree in (None, -1, True):
            with self.assertRaises(ValueError):
                detection_kernel(PSL27, 2, max_degree=degree)
        for family in ('all', [None], [[[0, 0]]], [[[False, True]]]):
            with self.assertRaises(ValueError):
                detection_kernel(C2, 2, max_degree=1, subgroups=family)
        with self.assertRaises(ResourceLimit):
            detection_kernel(C2, 2, max_degree=1, subgroups=[[], []], max_subgroups=1)
        for degrees in ([], [-1], [True]):
            with self.assertRaises(ValueError):
                cohomology_groups(C2, degrees)
        with self.assertRaises(ValueError):
            integral_periodicity(C2, max_period=0)

    def test_python_worker_timeout(self):
        with self.assertRaises(ResourceLimit):
            python_compute(C2, 'detection', p=2, max_degree=4, timeout=0.001)

    def test_no_series_extrapolation(self):
        with patch('invgal.cohomology_series.gap_compute',
                   side_effect=[{'cyclic': False}, {'abelian': False}]):
            with self.assertRaisesRegex(InvariantError, 'no full-series formula'):
                hilbert_poincare_series(PSL27, 2)

    def test_bar_complex_dimensions_and_d_squared(self):
        # C3 has one cohomology class in each degree over F3.
        complex_ = BarComplex([[0, 1, 2], [1, 2, 0], [2, 0, 1]], 3)
        for n in range(4):
            self.assertEqual(len(complex_.cohomology(n)), 1)
            if n:
                cycles = LinearMap(complex_.differential(n).kernel,
                                   len(complex_.tuples(n)), 3)
                for boundary, lift in complex_.differential(n-1).pivots.values():
                    self.assertIsNotNone(cycles.solve(boundary))
        self.assertEqual(LinearMap([[1, 1], [2, 2]], 2, 3).kernel, [[1, 1]])



@unittest.skipUnless(GAP, 'install GAP/HAP or set INVGAL_GAP')
class GapCohomologyInvariantTest(unittest.TestCase):
    def setUp(self):
        self.backend = dict(gap=GAP, timeout=120)

    def test_integral_cyclic_and_bundled_groups(self):
        result = cohomology_groups(C3, range(5), **self.backend)
        self.assertEqual([x['free_rank'] for x in result], [1, 0, 0, 0, 0])
        self.assertEqual([x['torsion_invariant_factors'] for x in result], [[], [], [3], [], [3]])
        for group, expected in ((PSL27, [2]), (M23, [])):
            result = cohomology_groups(group, range(4), **self.backend)
            self.assertEqual([x['free_rank'] for x in result], [1, 0, 0, 0])
            self.assertEqual([x['torsion_invariant_factors'] for x in result], [[], [], [], expected])
        self.assertEqual(cohomology_groups(C3, [3, 1, 3], p=3, **self.backend),
                         [dict(degree=n, p=3, dimension=1) for n in [3, 1, 3]])

    def test_series_against_independent_hap_dimensions(self):
        for group, p, degree in ((C2, 2, 5), (C3, 3, 5), (C4, 2, 5),
                                 (V4, 2, 4), (S3, 3, 7), (PSL27, 7, 12), (M23, 23, 22)):
            with self.subTest(group=group.name, p=p):
                series = hilbert_poincare_series(group, p, **self.backend)
                betti = compute_cohomology(group, p, degree, **self.backend).betti_numbers
                self.assertEqual(series.coefficients(degree), betti)

    def test_zeros_poles_and_cancellation(self):
        for group, p, period, zero_orders, pole_orders in (
                (C3, 3, 1, [], [1]), (V4, 2, 1, [], [1]),
                (PSL27, 7, 6, [10], [1, 3, 6]),
                (M23, 23, 22, [6, 14, 42], [1, 11, 22])):
            series = hilbert_poincare_series(group, p, **self.backend)
            result = zeros_and_poles(group, series, **self.backend)
            self.assertEqual(result['least_eventual_quasipolynomial_period'], period)
            for key, expected in (('zeros', zero_orders), ('poles', pole_orders)):
                self.assertEqual(sorted(f['root_of_unity_order'] for f in result[key]), expected)
            self.assertEqual(result['pole_order_at_one'], 2 if group is V4 else 1)

    def test_periodicity_and_search_bound(self):
        for group, period in ((TRIVIAL, 1), (C3, 2), (S3, 4),
                              (V4, 'infinity'), (PSL27, 'infinity'), (M23, 'infinity')):
            result = integral_periodicity(group, **self.backend)
            self.assertEqual(result, dict(period=period, periodic=period != 'infinity'))
        with self.assertRaisesRegex(InvariantError, 'max_period'):
            integral_periodicity(S3, max_period=3, **self.backend)

    def test_generalized_quaternion_period(self):
        self.assertEqual(integral_periodicity(Q8, **self.backend), dict(period=4, periodic=True))

    def test_essential_detection_and_empty_family(self):
        result = detection_kernel(V4, 2, max_degree=3, **self.backend)
        self.assertEqual([x['kernel_dimension'] for x in result['degrees']], [0, 0, 0, 1])
        self.assertEqual([x['source_dimension'] for x in result['degrees']], [1, 2, 3, 4])
        for group, expected in ((C3, [0, 1, 1]), (TRIVIAL, [1, 0, 0])):
            result = detection_kernel(group, 3, max_degree=2, **self.backend)
            self.assertEqual([x['kernel_dimension'] for x in result['degrees']], expected)
        result = detection_kernel(C3, 3, subgroups=(), max_degree=2, **self.backend)
        self.assertEqual([x['kernel_dimension'] for x in result['degrees']], [1, 1, 1])
        result = detection_kernel(C3, 3, subgroups=[C3.perms], max_degree=2, **self.backend)
        self.assertEqual([x['kernel_dimension'] for x in result['degrees']], [0, 0, 0])

    def test_degreewise_restrictions(self):
        # The two coordinate C2 subgroups detect H1 of V4, but not all of H2.
        family = [[[1, 0, 2, 3]], [[0, 1, 3, 2]]]
        result = detection_kernel(V4, 2, subgroups=family, max_degree=2, **self.backend)
        self.assertEqual([x['kernel_dimension'] for x in result['degrees']], [0, 0, 1])
        with self.assertRaisesRegex(InvariantError, 'not contained'):
            detection_kernel(C3, 3, subgroups=[[[1, 0, 2]]], max_degree=1, **self.backend)

    def test_resource_limits(self):
        for options, message in ((dict(max_elements=2), 'max_elements'),
                                 (dict(max_cochains=1), 'max_cochains'),
                                 (dict(max_matrix_entries=1), 'max_matrix_entries')):
            with self.assertRaisesRegex(ResourceLimit, message):
                detection_kernel(C3, 3, max_degree=2, **options, **self.backend)

    def test_cli_five_added_invariants(self):
        names = ['integral_cohomology', 'poincare_series', 'zeros_and_poles',
                 'detection_kernel', 'periodicity']
        run = subprocess.run([sys.executable, '-m', 'invgal.invariants', '--groups', 'PSL27',
                              '--invariants', *names, '--p', '7', '--max-degree', '3', '--gap', GAP],
                             cwd=ROOT, capture_output=True, text=True, check=True, timeout=120)
        rows = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual([row['invariant'] for row in rows], names)
        self.assertEqual(rows[0]['result'][3]['torsion_invariant_factors'], [2])
        self.assertEqual(rows[2]['result']['least_eventual_quasipolynomial_period'], 6)
        self.assertTrue(rows[3]['result']['zero_through_max_degree'])
        self.assertFalse(rows[4]['result']['periodic'])


if __name__ == '__main__':
    unittest.main()
