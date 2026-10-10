"""A1-3 (SPEC-L1 §7): the block solver against dense Gaussian elimination."""
import random

import pytest

layer1 = pytest.importorskip("layer1")
from layer1 import solver  # noqa: E402


def dense_solve(a, b):
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                for j in range(c, n + 1):
                    m[r][j] -= f * m[c][j]
    return [m[i][n] / m[i][i] for i in range(n)]


@pytest.mark.parametrize("seed", range(8))
def test_a1_3_block_solver_and_last_block_inverse(seed):
    rnd = random.Random(seed)
    t = rnd.randint(1, 7)
    n = 4 * t
    a = [[0.0] * n for _ in range(n)]
    diag, off = [], []
    for k in range(t):
        r = [[rnd.gauss(0, 1) for _ in range(4)] for _ in range(4)]
        d = [[sum(r[i][m] * r[j][m] for m in range(4)) + (4.0 if i == j else 0.0) for j in range(4)] for i in range(4)]
        for i in range(4):
            for j in range(4):
                a[4 * k + i][4 * k + j] = d[i][j]
        diag.append([d[i][j] for i in range(4) for j in range(4)])
    for k in range(t - 1):
        u = [rnd.uniform(-1, 1) for _ in range(4)]
        off.append(u)
        for i in range(4):
            a[4 * k + i][4 * (k + 1) + i] = a[4 * (k + 1) + i][4 * k + i] = u[i]
    rhs = [[rnd.gauss(0, 1) for _ in range(4)] for _ in range(t)]
    y, last = solver.solve(diag, off, rhs)
    yd = dense_solve(a, [v for r in rhs for v in r])
    assert max(abs(p - q) for p, q in zip([v for r in y for v in r], yd)) < 1e-9
    for c in range(4):
        e = [0.0] * n
        e[4 * (t - 1) + c] = 1.0
        col = dense_solve(a, e)[4 * (t - 1):]
        assert max(abs(last[4 * i + c] - col[i]) for i in range(4)) < 1e-9


@pytest.mark.parametrize("seed", range(4))
def test_a1_3_marginal_covariances_equal_the_dense_inverse(seed):
    rnd = random.Random(100 + seed)
    t = rnd.randint(1, 6)
    n = 4 * t
    a = [[0.0] * n for _ in range(n)]
    diag, off = [], []
    for k in range(t):
        r = [[rnd.gauss(0, 1) for _ in range(4)] for _ in range(4)]
        d = [[sum(r[i][m] * r[j][m] for m in range(4)) + (4.0 if i == j else 0.0) for j in range(4)] for i in range(4)]
        for i in range(4):
            for j in range(4):
                a[4 * k + i][4 * k + j] = d[i][j]
        diag.append([d[i][j] for i in range(4) for j in range(4)])
    for k in range(t - 1):
        u = [rnd.uniform(-1, 1) for _ in range(4)]
        off.append(u)
        for i in range(4):
            a[4 * k + i][4 * (k + 1) + i] = a[4 * (k + 1) + i][4 * k + i] = u[i]
    cov = solver.marginal_covariances(diag, off)
    for k in range(t):
        for c in range(4):
            e = [0.0] * n
            e[4 * k + c] = 1.0
            col = dense_solve(a, e)
            assert max(abs(cov[k][4 * i + c] - col[4 * k + i]) for i in range(4)) < 1e-9
