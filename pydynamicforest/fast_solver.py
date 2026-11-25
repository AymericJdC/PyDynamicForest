# SPDX-License-Identifier: LGPL-3.0-or-later
"""Vectorised implementation of the legacy semi-implicit scheme.

The functions of this module reproduce, without Python loops, the numerical
scheme implemented by :mod:`pydynamicforest.solver`:

- explicit first-order upwind transport of ``S[u] u`` with arithmetic face
  velocities and no flux through the boundary of the size domain;
- implicit five-point diffusion with arithmetic face coefficients and
  homogeneous Neumann conditions;
- implicit mortality ``K (1 - S[u])`` with the status of the current step.

The implicit matrix is symmetric (face coefficients are shared by the two
adjacent nodes) and strictly diagonally dominant with a positive diagonal
when the diffusion and mortality fields are non-negative and ``S <= 1``. It is
therefore symmetric positive definite, so the system can be solved either
directly (``spsolve``) or by the conjugate gradient method with a Jacobi
preconditioner.

The legacy loop implementations remain the regression reference: the tests
compare every operator of this module with its legacy counterpart.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import LinearOperator, cg, spsolve

from pydynamicforest.model import evaluate_model_fields
from pydynamicforest.numerics import compute_status_field
from pydynamicforest.types import DerivedQuantities, Parameters, State

LINEAR_SOLVERS = ("direct", "cg")


def cumulative_integral_2d_trapezoidal_vectorised(
    U: np.ndarray,
    dx: float,
    dy: float,
) -> np.ndarray:
    """Cumulative 2D trapezoidal integral, equal to the legacy recursion.

    ``J[i, j]`` is the sum of the trapezoidal cell integrals over
    ``[x_0, x_i] x [y_0, y_j]``; the first row and column are zero.
    """

    cell = 0.25 * dx * dy * (U[1:, 1:] + U[:-1, 1:] + U[1:, :-1] + U[:-1, :-1])
    J = np.zeros_like(U, dtype=float)
    J[1:, 1:] = np.cumsum(np.cumsum(cell, axis=0), axis=1)
    return J


def compute_derived_quantities_vectorised(state: State, p: Parameters) -> DerivedQuantities:
    """Vectorised counterpart of :func:`pydynamicforest.numerics.compute_derived_quantities`."""

    grid = p.numerics.grid
    J = cumulative_integral_2d_trapezoidal_vectorised(state.U, grid.dx, grid.dy)
    total_mass = float(J[-1, -1])
    S = compute_status_field(J, total_mass, p.numerics.epsilon_zero_mass)
    return DerivedQuantities(
        cumulative_distribution=J,
        status_field=S,
        total_mass=total_mass,
        minimum_density=float(np.min(state.U)),
    )


def _field(fields, name: str) -> np.ndarray:
    if isinstance(fields, dict):
        return fields[name]
    return getattr(fields, name)


def compute_transport_vectorised(
    state: State,
    p: Parameters,
    derived: DerivedQuantities,
    fields,
) -> np.ndarray:
    """Explicit upwind transport divergence, equal to ``compute_transport_legacy``.

    At the face between nodes ``k`` and ``k + 1`` of an axis, the velocity is
    the arithmetic mean of the nodal velocities and the transported quantity
    ``S u`` is taken at node ``k`` if this mean is non-negative and at node
    ``k + 1`` otherwise. Faces on the boundary of the domain carry no flux.
    """

    U = state.U
    S = derived.status_field
    Ch = _field(fields, "height_growth")
    Cd = _field(fields, "dbh_growth")
    grid = p.numerics.grid
    q = S * U

    sum_x = Ch[1:, :] + Ch[:-1, :]
    flux_x = 0.5 * sum_x * np.where(sum_x >= 0.0, q[:-1, :], q[1:, :])
    sum_y = Cd[:, 1:] + Cd[:, :-1]
    flux_y = 0.5 * sum_y * np.where(sum_y >= 0.0, q[:, :-1], q[:, 1:])

    transport = np.zeros_like(U, dtype=float)
    transport[:-1, :] += flux_x / grid.dx
    transport[1:, :] -= flux_x / grid.dx
    transport[:, :-1] += flux_y / grid.dy
    transport[:, 1:] -= flux_y / grid.dy
    return transport


def assemble_sparse_system_vectorised(
    state: State,
    p: Parameters,
    derived: DerivedQuantities,
    fields_next,
    transport: np.ndarray,
    *,
    diffusion_factor: float = 1.0,
    mortality_factor: float = 1.0,
) -> tuple[sp.csr_matrix, np.ndarray]:
    """Assemble ``A U^{n+1} = b``, equal to ``assemble_sparse_legacy_system``.

    Unknowns are ordered as in the legacy code, ``row = i * ny + j``.
    """

    for name, value in (("diffusion_factor", diffusion_factor), ("mortality_factor", mortality_factor)):
        if not np.isfinite(value) or value < 0.0:
            raise ValueError(f"{name} must be a finite non-negative number.")

    grid = p.numerics.grid
    nx, ny, dx, dy = grid.nx, grid.ny, grid.dx, grid.dy
    dt = p.numerics.time.dt
    D = float(diffusion_factor) * np.asarray(_field(fields_next, "diffusion"), dtype=float)
    K = float(mortality_factor) * np.asarray(_field(fields_next, "mortality"), dtype=float)
    S = derived.status_field

    aE = np.zeros((nx, ny))
    aW = np.zeros((nx, ny))
    aN = np.zeros((nx, ny))
    aS = np.zeros((nx, ny))
    aE[:-1, :] = 0.5 * (D[:-1, :] + D[1:, :]) / (dx * dx)
    aW[1:, :] = 0.5 * (D[1:, :] + D[:-1, :]) / (dx * dx)
    aN[:, :-1] = 0.5 * (D[:, :-1] + D[:, 1:]) / (dy * dy)
    aS[:, 1:] = 0.5 * (D[:, 1:] + D[:, :-1]) / (dy * dy)

    main = 1.0 + dt * (aE + aW + aN + aS) + dt * K * (1.0 - S)
    n = nx * ny
    A = sp.diags(
        [
            main.ravel(),
            -dt * aE[:-1, :].ravel(),
            -dt * aW[1:, :].ravel(),
            -dt * aN.ravel()[:-1],
            -dt * aS.ravel()[1:],
        ],
        [0, ny, -ny, 1, -1],
        shape=(n, n),
        format="csr",
    )
    A.eliminate_zeros()
    b = (state.U - dt * transport).ravel()
    return A, b


def solve_linear_system(
    A: sp.spmatrix,
    b: np.ndarray,
    method: str = "direct",
    x0: np.ndarray | None = None,
    rtol: float = 1e-13,
    maxiter: int = 500,
) -> np.ndarray:
    """Solve the implicit system directly or by Jacobi-preconditioned CG."""

    if method == "direct":
        return spsolve(A.tocsc(), b)
    if method == "cg":
        diagonal = A.diagonal()
        if np.any(diagonal <= 0.0):
            raise ValueError("conjugate gradient requires a positive diagonal.")
        preconditioner = LinearOperator(A.shape, matvec=lambda x: x / diagonal)
        x, info = cg(A, b, x0=x0, rtol=rtol, atol=0.0, M=preconditioner, maxiter=maxiter)
        if info != 0:
            raise RuntimeError(f"conjugate gradient did not converge (info={info}).")
        return x
    raise ValueError(f"Unknown linear solver: {method}. Expected one of {LINEAR_SOLVERS}.")


def advance_one_step_vectorised(
    state: State,
    p: Parameters,
    linear_solver: str = "direct",
) -> State:
    """Advance one time step with the vectorised scheme.

    Same time levels as ``advance_one_step_sparse_legacy``: transport and
    status at the current state, diffusion and mortality fields at
    ``t + dt``. The transport fields are evaluated with the same helper as the
    legacy solver, so that state-dependent model fields remain supported.
    """

    from pydynamicforest.solver import evaluate_model_fields_for_solver

    dt = p.numerics.time.dt
    t_next = state.time + dt
    derived = compute_derived_quantities_vectorised(state, p)
    fields_current = evaluate_model_fields_for_solver(state, p)
    fields_next = evaluate_model_fields(p, t_next)
    transport = compute_transport_vectorised(state, p, derived, fields_current)
    A, b = assemble_sparse_system_vectorised(state, p, derived, fields_next, transport)
    U_next = solve_linear_system(A, b, method=linear_solver, x0=state.U.ravel())
    return State(
        time=t_next,
        age=state.age + dt,
        U=U_next.reshape(state.U.shape),
        step_index=state.step_index + 1,
    )


def advance_one_step_vectorised_direct(state: State, p: Parameters) -> State:
    """Vectorised step with a direct sparse solve."""

    return advance_one_step_vectorised(state, p, linear_solver="direct")


def advance_one_step_vectorised_cg(state: State, p: Parameters) -> State:
    """Vectorised step with Jacobi-preconditioned conjugate gradient."""

    return advance_one_step_vectorised(state, p, linear_solver="cg")


class ConstantCoefficientStepper:
    """Vectorised stepper for time-independent model fields.

    The face velocities and the diffusion part of the implicit matrix are
    assembled once; each step only updates the status, the transport term and
    the mortality diagonal. With ``height_status_exponent = 1`` a step is
    identical to :func:`advance_one_step_vectorised` (tested). Other exponents
    replace ``S`` by ``S**gamma`` in the height component of the transport
    only, for sensitivity analyses; ``gamma < 1`` is not Lipschitz at ``S = 0``
    and lies outside the analysed class of models.
    """

    def __init__(
        self,
        p: Parameters,
        linear_solver: str = "cg",
        height_status_exponent: float = 1.0,
        check_time_independence: bool = True,
    ) -> None:
        if linear_solver not in LINEAR_SOLVERS:
            raise ValueError(f"Unknown linear solver: {linear_solver}.")
        if not np.isfinite(height_status_exponent) or height_status_exponent < 0.0:
            raise ValueError("height_status_exponent must be finite and non-negative.")
        grid = p.numerics.grid
        self.p = p
        self.linear_solver = linear_solver
        self.gamma = float(height_status_exponent)
        self.dt = p.numerics.time.dt
        self.dx, self.dy = grid.dx, grid.dy
        fields = evaluate_model_fields(p, 0.0)
        if check_time_independence:
            later = evaluate_model_fields(p, p.numerics.time.dt * max(p.numerics.time.n_steps, 1))
            for name in ("diffusion", "mortality", "height_growth", "dbh_growth"):
                if not np.array_equal(_field(fields, name), _field(later, name)):
                    raise ValueError(f"model field '{name}' depends on time; use advance_one_step_vectorised.")
        Ch, Cd = _field(fields, "height_growth"), _field(fields, "dbh_growth")
        self.mortality = np.asarray(_field(fields, "mortality"), dtype=float)
        self.sum_x = Ch[1:, :] + Ch[:-1, :]
        self.sum_y = Cd[:, 1:] + Cd[:, :-1]
        zero = np.zeros((grid.nx, grid.ny))
        dummy = State(time=0.0, age=0.0, U=zero, step_index=0)
        derived0 = DerivedQuantities(cumulative_distribution=zero, status_field=zero, total_mass=0.0, minimum_density=0.0)
        no_mortality = dict(diffusion=_field(fields, "diffusion"), mortality=np.zeros_like(zero))
        A0, _ = assemble_sparse_system_vectorised(dummy, p, derived0, no_mortality, zero)
        self.A0 = A0.tocsr()

    def status(self, U: np.ndarray) -> np.ndarray:
        J = cumulative_integral_2d_trapezoidal_vectorised(U, self.dx, self.dy)
        return compute_status_field(J, float(J[-1, -1]), self.p.numerics.epsilon_zero_mass)

    def transport(self, U: np.ndarray, S: np.ndarray) -> np.ndarray:
        Sh = S if self.gamma == 1.0 else np.clip(S, 0.0, 1.0) ** self.gamma
        qx, qy = Sh * U, S * U
        flux_x = 0.5 * self.sum_x * np.where(self.sum_x >= 0.0, qx[:-1, :], qx[1:, :])
        flux_y = 0.5 * self.sum_y * np.where(self.sum_y >= 0.0, qy[:, :-1], qy[:, 1:])
        T = np.zeros_like(U, dtype=float)
        T[:-1, :] += flux_x / self.dx
        T[1:, :] -= flux_x / self.dx
        T[:, :-1] += flux_y / self.dy
        T[:, 1:] -= flux_y / self.dy
        return T

    def step(self, U: np.ndarray) -> np.ndarray:
        S = self.status(U)
        b = (U - self.dt * self.transport(U, S)).ravel()
        A = self.A0 + sp.diags((self.dt * self.mortality * (1.0 - S)).ravel())
        return solve_linear_system(A, b, method=self.linear_solver, x0=U.ravel()).reshape(U.shape)
