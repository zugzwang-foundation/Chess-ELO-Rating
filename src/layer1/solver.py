"""Exact solution of a player's Newton system (SPEC-L1 §4.2, §4.3).

The Hessian of one player's negative log posterior is block tridiagonal: 4 × 4
symmetric diagonal blocks D_k (one per time point: θ, δ_standard, δ_rapid,
δ_blitz) and diagonal off-diagonal blocks diag(U_k) linking time points k and
k + 1 (the dynamics act component by component). Block elimination solves
H·y = g exactly and leaves the inverse of the last Schur complement, which is
the marginal covariance of the last state (the Laplace covariance at the mode).
Matrices are flat lists of 16 floats, row major.
"""
from __future__ import annotations


def inv4(m: list[float]) -> list[float]:
    """Inverse of a symmetric positive definite 4 × 4 matrix by Gauss–Jordan with partial pivoting."""
    a = [m[0:4] + [1.0, 0.0, 0.0, 0.0], m[4:8] + [0.0, 1.0, 0.0, 0.0],
         m[8:12] + [0.0, 0.0, 1.0, 0.0], m[12:16] + [0.0, 0.0, 0.0, 1.0]]
    for c in range(4):
        p = max(range(c, 4), key=lambda r: abs(a[r][c]))
        if a[p][c] == 0.0:
            raise ZeroDivisionError("singular block")
        if p != c:
            a[c], a[p] = a[p], a[c]
        rc = a[c]
        f = 1.0 / rc[c]
        for j in range(8):
            rc[j] *= f
        for r in range(4):
            if r != c:
                rr = a[r]
                g = rr[c]
                if g != 0.0:
                    for j in range(8):
                        rr[j] -= g * rc[j]
    return [a[0][4], a[0][5], a[0][6], a[0][7], a[1][4], a[1][5], a[1][6], a[1][7],
            a[2][4], a[2][5], a[2][6], a[2][7], a[3][4], a[3][5], a[3][6], a[3][7]]


def matvec4(m: list[float], v: list[float]) -> list[float]:
    return [m[0] * v[0] + m[1] * v[1] + m[2] * v[2] + m[3] * v[3],
            m[4] * v[0] + m[5] * v[1] + m[6] * v[2] + m[7] * v[3],
            m[8] * v[0] + m[9] * v[1] + m[10] * v[2] + m[11] * v[3],
            m[12] * v[0] + m[13] * v[1] + m[14] * v[2] + m[15] * v[3]]


def solve(diag: list[list[float]], off: list[list[float]], rhs: list[list[float]]) -> tuple[list[list[float]], list[float]]:
    """Solve H y = rhs; returns (y per block, inverse of the last Schur complement).

    diag[k]: 4 × 4 block k (flat); off[k]: the 4 diagonal entries of the block linking k and k + 1
    (len(off) = len(diag) − 1); rhs[k]: 4 entries."""
    t = len(diag)
    sinv: list[list[float]] = []
    b: list[list[float]] = []
    for k in range(t):
        s = list(diag[k])
        bk = list(rhs[k])
        if k:
            u = off[k - 1]
            pi = sinv[k - 1]
            pb = b[k - 1]
            # S_k = D_k − U S_{k−1}^{-1} U ; b_k = r_k − U S_{k−1}^{-1} b_{k−1}  (U diagonal)
            w = matvec4(pi, pb)
            for i in range(4):
                ui = u[i]
                if ui != 0.0:
                    bk[i] -= ui * w[i]
                    row = 4 * i
                    for j in range(4):
                        uj = u[j]
                        if uj != 0.0:
                            s[row + j] -= ui * pi[row + j] * uj
        sinv.append(inv4(s))
        b.append(bk)
    y: list[list[float]] = [None] * t  # type: ignore[list-item]
    y[t - 1] = matvec4(sinv[t - 1], b[t - 1])
    for k in range(t - 2, -1, -1):
        u = off[k]
        nxt = y[k + 1]
        r = [b[k][i] - u[i] * nxt[i] for i in range(4)]
        y[k] = matvec4(sinv[k], r)
    return y, sinv[t - 1]


def marginal_covariances(diag: list[list[float]], off: list[list[float]]) -> list[list[float]]:
    """Diagonal blocks of H^{-1} for the block-tridiagonal H of `solve` (the Laplace covariance of every state):
    forward elimination, then Σ_{T−1} = S_{T−1}^{-1} and Σ_k = S_k^{-1} + S_k^{-1} U_k Σ_{k+1} U_k S_k^{-1}."""
    t = len(diag)
    sinv: list[list[float]] = []
    for k in range(t):
        s = list(diag[k])
        if k:
            u = off[k - 1]
            pi = sinv[k - 1]
            for i in range(4):
                if u[i] != 0.0:
                    row = 4 * i
                    for j in range(4):
                        if u[j] != 0.0:
                            s[row + j] -= u[i] * pi[row + j] * u[j]
        sinv.append(inv4(s))
    cov: list[list[float]] = [None] * t  # type: ignore[list-item]
    cov[t - 1] = sinv[t - 1]
    for k in range(t - 2, -1, -1):
        si, u, nxt = sinv[k], off[k], cov[k + 1]
        # M = S_k^{-1} U_k (U diagonal): M[r][c] = si[r][c] * u[c]
        m = [si[4 * r + c] * u[c] for r in range(4) for c in range(4)]
        # Σ_k = S_k^{-1} + M Σ_{k+1} M^T
        tmp = [sum(m[4 * r + a] * nxt[4 * a + c] for a in range(4)) for r in range(4) for c in range(4)]
        cov[k] = [si[4 * r + c] + sum(tmp[4 * r + a] * m[4 * c + a] for a in range(4)) for r in range(4) for c in range(4)]
    return cov
