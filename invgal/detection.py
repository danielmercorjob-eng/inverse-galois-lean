"""Degreewise kernels of cohomology restrictions to subgroups."""

from .backends import ResourceLimit, checked_perms, positive_int, python_compute
from .cohomology_series import check_prime


def detection_kernel(group, p, *, max_degree, subgroups=None, gap="gap", timeout=300,
                     max_elements=64, max_cochains=4096, max_matrix_entries=2000000,
                     max_subgroups=1000):
    """Intersection of restriction kernels in degrees 0 to max_degree, inclusive.

    With subgroups=None, the function calculates essential cohomology.
    Each subgroup is a list of generators in zero-based permutation image
    notation. An empty family has kernel H^n(G,Fp).
    """
    check_prime(p)
    checked_perms(group)
    for name, value, minimum in (("max_degree", max_degree, 0),
                                 ("max_elements", max_elements, 1),
                                 ("max_cochains", max_cochains, 1),
                                 ("max_matrix_entries", max_matrix_entries, 1),
                                 ("max_subgroups", max_subgroups, 1)):
        positive_int(value, name, minimum)
    if subgroups is not None:
        if not isinstance(subgroups, (list, tuple)):
            raise ValueError("subgroups must be a list of generator lists")
        for generators in subgroups:
            if not isinstance(generators, (list, tuple)) or any(
                    not isinstance(g, (list, tuple)) or len(g) != group.degree
                    or any(type(x) is not int for x in g)
                    or sorted(g) != list(range(group.degree)) for g in generators):
                raise ValueError("subgroup generators must be permutation image lists")
        subgroups = [list(generators) for generators in subgroups]
        if len(subgroups) > max_subgroups:
            raise ResourceLimit("restriction family exceeds max_subgroups")
    q = group.order
    while q % p == 0:
        q //= p
    if subgroups is None and q != 1:
        return dict(p=p, max_degree=max_degree, full_presentation=False,
                    degrees=[dict(degree=n, kernel_dimension=0) for n in range(max_degree+1)],
                    zero_through_max_degree=True,
                    certification="restriction to a proper Sylow subgroup is injective")
    return python_compute(group, "detection", p=p, subgroups=subgroups,
                          max_degree=max_degree, max_elements=max_elements,
                          max_cochains=max_cochains, max_matrix_entries=max_matrix_entries,
                          max_subgroups=max_subgroups, gap=gap, timeout=timeout)
