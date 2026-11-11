"""Normalized bar cochains over a prime field for small finite groups."""

from itertools import product

from .backends import InvariantError, ResourceLimit, gap_compute


class LinearMap:
    """Row-vector linear map with kernel and preimage algorithms over Fp."""

    def __init__(self, rows, ncols, p):
        self.p, self.ncols, self.nrows = p, ncols, len(rows)
        self.pivots, self.kernel = {}, []
        for i, row in enumerate(rows):
            row = [x % p for x in row]
            origin = [int(i == j) for j in range(len(rows))]
            for pivot, (basis, lift) in sorted(self.pivots.items()):
                c = row[pivot]
                if c:
                    row = [(a-c*b) % p for a, b in zip(row, basis)]
                    origin = [(a-c*b) % p for a, b in zip(origin, lift)]
            pivot = next((j for j, x in enumerate(row) if x), None)
            if pivot is None:
                self.kernel.append(origin)
            else:
                scale = pow(row[pivot], -1, p)
                self.pivots[pivot] = ([scale*x % p for x in row],
                                      [scale*x % p for x in origin])

    def solve(self, target):
        row, answer = list(target), [0]*self.nrows
        for pivot, (basis, lift) in sorted(self.pivots.items()):
            c = row[pivot] % self.p
            if c:
                row = [(a-c*b) % self.p for a, b in zip(row, basis)]
                answer = [(a+c*b) % self.p for a, b in zip(answer, lift)]
        return None if any(x % self.p for x in row) else answer

    @property
    def rank(self):
        return len(self.pivots)


class BarComplex:
    """Normalized cochains on tuples without identity elements."""

    def __init__(self, table, p, *, max_cochains=4096, max_matrix_entries=2000000):
        self.table, self.p, self.size = table, p, len(table)
        self.max_cochains, self.max_matrix_entries = max_cochains, max_matrix_entries
        self._tuples, self._differentials, self._cohomology = {}, {}, {}

    def tuples(self, n):
        count = (self.size-1)**n
        if count > self.max_cochains:
            raise ResourceLimit(f"degree {n} exceeds max_cochains={self.max_cochains}")
        if n not in self._tuples:
            self._tuples[n] = list(product(range(1, self.size), repeat=n))
        return self._tuples[n]

    def differential(self, n):
        if n not in self._differentials:
            source, target = self.tuples(n), self.tuples(n+1)
            if len(source)*len(target) + len(source)**2 > self.max_matrix_entries:
                raise ResourceLimit("bar differential exceeds max_matrix_entries")
            lookup = {t: i for i, t in enumerate(source)}
            rows = [[0]*len(target) for _ in source]
            for j, t in enumerate(target):
                faces = [(1, t[1:]), ((-1)**(n+1), t[:-1])]
                faces.extend(((-1)**i, t[:i-1] + (self.table[t[i-1]][t[i]],) + t[i+1:])
                             for i in range(1, n+1))
                for sign, face in faces:
                    if 0 not in face:
                        rows[lookup[face]][j] = (rows[lookup[face]][j] + sign) % self.p
            self._differentials[n] = LinearMap(rows, len(target), self.p)
        return self._differentials[n]

    def cohomology(self, n):
        if n not in self._cohomology:
            cycles = self.differential(n).kernel
            previous = self.differential(n-1) if n else None
            boundaries = ([row for row, lift in previous.pivots.values()] if previous else [])
            representatives, rows = [], list(boundaries)
            span = LinearMap(rows, len(self.tuples(n)), self.p)
            for cycle in cycles:
                if span.solve(cycle) is None:
                    representatives.append(cycle)
                    rows.append(cycle)
                    span = LinearMap(rows, len(self.tuples(n)), self.p)
            self._cohomology[n] = (representatives, span, len(boundaries))
        return self._cohomology[n][0]

    def coordinates(self, n, cycle):
        self.cohomology(n)
        _, span, offset = self._cohomology[n]
        lift = span.solve(cycle)
        if lift is None:
            raise InvariantError("the cochain is not a cocycle")
        return lift[offset:]


def _restrictions(complex_, subsets):
    result = []
    for subset in subsets:
        lookup = {g: i for i, g in enumerate(subset)}
        table = [[lookup[complex_.table[g][h]] for h in subset] for g in subset]
        result.append((subset, BarComplex(table, complex_.p, max_cochains=complex_.max_cochains,
                                          max_matrix_entries=complex_.max_matrix_entries)))
    return result


def _restrict(complex_, subcomplex, subset, degree, cycle):
    lookup = {t: i for i, t in enumerate(complex_.tuples(degree))}
    restricted = [cycle[lookup[tuple(subset[g] for g in t)]] for t in subcomplex.tuples(degree)]
    return subcomplex.coordinates(degree, restricted)


def _detection(complex_, subsets, max_degree):
    restrictions = _restrictions(complex_, subsets)
    layers = []
    for n in range(max_degree+1):
        basis = complex_.cohomology(n)
        columns = sum(len(subcomplex.cohomology(n)) for subset, subcomplex in restrictions)
        if len(basis)*columns + len(basis)**2 > complex_.max_matrix_entries:
            raise ResourceLimit("restriction matrix exceeds max_matrix_entries")
        rows = [[c for subset, subcomplex in restrictions
                 for c in _restrict(complex_, subcomplex, subset, n, cycle)] for cycle in basis]
        kernel = LinearMap(rows, columns, complex_.p).kernel
        layers.append(dict(degree=n, source_dimension=len(basis), source_basis_cochains=basis,
                           kernel_basis=kernel, kernel_dimension=len(kernel)))
    return dict(degrees=layers, zero_through_max_degree=all(not x["kernel_basis"] for x in layers),
                full_presentation=False, max_degree=max_degree,
                certification="restriction matrices in the stated degrees")


def compute(group, operation, *, p, gap, timeout, max_degree, subgroups=None,
            max_elements=64, max_cochains=4096, max_matrix_entries=2000000,
            max_subgroups=1000):
    if operation != "detection":
        raise ValueError("unknown cochain operation")
    if group.order > max_elements:
        raise ResourceLimit(f"group order {group.order} exceeds max_elements={max_elements}")
    data = gap_compute(group, "finite_model", max_elements=max_elements, gap=gap, timeout=timeout)
    complex_ = BarComplex(data["table"], p, max_cochains=max_cochains,
                          max_matrix_entries=max_matrix_entries)
    subsets = gap_compute(group, "restriction_family", essential=subgroups is None,
                          subgroups=subgroups or [], max_elements=max_elements,
                          max_subgroups=max_subgroups, gap=gap, timeout=timeout)
    answer = _detection(complex_, subsets, max_degree)
    return dict(answer, p=p, subgroup_elements=subsets,
                group_elements=[[x-1 for x in g] for g in data["elements"]],
                tuple_order="lexicographic tuples of nonidentity element indices")
