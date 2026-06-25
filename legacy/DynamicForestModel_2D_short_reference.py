import numpy as np
import matplotlib.pyplot as plt

# Short reference version of the legacy DynamicForestModel_2D.py script.
# Purpose: fast legacy-like run for regression comparison against the refactored
# implementation with simulate(x0, p, c, max_steps=10).
#
# This file intentionally keeps the original dense legacy numerical scheme,
# but uses a short simulation horizon:
#   T = 0.51, Nt = 10, dt = 0.051
# matching the first 10 time steps of the reduced reference configuration
# where T = 51 and Nt = 1000.

# Disable blocking matplotlib windows for reference runs.
plt.show = lambda *args, **kwargs: None


# -----------------------------------------------------------------------------
# Parameters of the normalized computational domain
# -----------------------------------------------------------------------------

Hphys = 50.0  # Physical height scale, m
Dphys = 0.9   # Physical DBH scale, m

Lx = 1.0
Ly = 1.0

# Short final time.
# With Nt = 10, this gives dt = 0.051, matching the first 10 steps
# of the reduced legacy reference case T = 51, Nt = 1000.
T = 0.51

# Reduced grid and short number of time steps.
Nx = 20
Ny = 20
Nt = 10

# Space and time steps.
dx = Lx / (Nx - 1)
dy = Ly / (Ny - 1)
dt = T / Nt

# Initial number of trees per hectare.
N0 = 2154.6

# Spatial grids in normalized variables.
x = np.linspace(0.0, Lx, Nx, endpoint=True)
y = np.linspace(0.0, Ly, Ny, endpoint=True)

# Time grid.
t = np.linspace(0.0, T, Nt + 1, endpoint=True)

# Stand age reference.
age0 = 18.0
age = age0 + t


# -----------------------------------------------------------------------------
# Model coefficients
# -----------------------------------------------------------------------------

def D(t, x, y):
    return 0.00001


def K(t, x, y):
    return 0.0365


# -----------------------------------------------------------------------------
# Initial condition
# -----------------------------------------------------------------------------

h0 = 10.50887557 / Hphys
d0 = 0.1176045686 / Dphys

sigh = 1.5 / Hphys
sigd = 0.04 / Dphys


def Gauss(x, y):
    return np.exp(
        -((x - h0) ** 2) / (2 * sigh**2)
        - ((y - d0) ** 2) / (2 * sigd**2)
    )


# Normalization constant using cumulative 2D trapezoidal rule,
# as in the legacy code.
Zc = np.zeros((Nx, Ny))
Zc[0, :] = 0.0
Zc[:, 0] = 0.0

for i in range(1, Nx):
    for j in range(1, Ny):
        Zc[i, j] = (
            Zc[i - 1, j]
            + Zc[i, j - 1]
            - Zc[i - 1, j - 1]
            + 0.25
            * dy
            * dx
            * (
                Gauss(x[i], y[j])
                + Gauss(x[i - 1], y[j])
                + Gauss(x[i], y[j - 1])
                + Gauss(x[i - 1], y[j - 1])
            )
        )

Z0 = Zc[-1, -1]


def u0(x, y):
    return Gauss(x, y) * N0 / Z0


# -----------------------------------------------------------------------------
# Growth velocities in normalized variables
# -----------------------------------------------------------------------------

rh = 1.78 / Hphys


def Ch(t, x, y):
    return rh * (1 - x / Lx)


rd = 0.0135 / Dphys


def Cd(t, x, y):
    return rd * (1 - y / Ly)


# -----------------------------------------------------------------------------
# Indexing convention
# -----------------------------------------------------------------------------

def idx(i, j):
    return i * Ny + j


# -----------------------------------------------------------------------------
# Precomputation of coefficients and initial condition
# -----------------------------------------------------------------------------

K_values = np.zeros((Nt + 1, Nx, Ny))
Ch_values = np.zeros((Nt + 1, Nx, Ny))
Cd_values = np.zeros((Nt + 1, Nx, Ny))
u0_values = np.zeros((Nx, Ny))

for i in range(Nx):
    for j in range(Ny):
        u0_values[i, j] = u0(x[i], y[j])

for n in range(Nt + 1):
    for i in range(Nx):
        for j in range(Ny):
            K_values[n, i, j] = K(t[n], x[i], y[j])
            Ch_values[n, i, j] = Ch(t[n], x[i], y[j])
            Cd_values[n, i, j] = Cd(t[n], x[i], y[j])


# -----------------------------------------------------------------------------
# Storage of numerical solution
# -----------------------------------------------------------------------------

U = np.zeros((Nt + 1, Nx, Ny))
Transp = np.zeros((Nt + 1, Nx, Ny))

U[0, :, :] = u0_values

N = Nx * Ny


# -----------------------------------------------------------------------------
# Time loop
# -----------------------------------------------------------------------------

for n in range(Nt):

    # Cumulative distribution J.
    J = np.zeros((Nx, Ny))
    J[0, :] = 0.0
    J[:, 0] = 0.0

    for i in range(1, Nx):
        for j in range(1, Ny):
            J[i, j] = (
                J[i - 1, j]
                + J[i, j - 1]
                - J[i - 1, j - 1]
                + 0.25
                * dy
                * dx
                * (
                    U[n, i, j]
                    + U[n, i - 1, j]
                    + U[n, i, j - 1]
                    + U[n, i - 1, j - 1]
                )
            )

    den = J[-1, -1]

    if den < 1e-15:
        den = 1e-15

    A = np.zeros((N, N), dtype=float)
    b = np.zeros(N, dtype=float)

    for i in range(Nx):
        for j in range(Ny):

            # Diffusion coefficients with homogeneous Neumann boundary conditions.
            if i < Nx - 1:
                aE = 0.5 * (
                    D(t[n + 1], x[i], y[j])
                    + D(t[n + 1], x[i + 1], y[j])
                ) / (dx * dx)
            else:
                aE = 0.0

            if i > 0:
                aW = 0.5 * (
                    D(t[n + 1], x[i], y[j])
                    + D(t[n + 1], x[i - 1], y[j])
                ) / (dx * dx)
            else:
                aW = 0.0

            if j < Ny - 1:
                aN = 0.5 * (
                    D(t[n + 1], x[i], y[j])
                    + D(t[n + 1], x[i], y[j + 1])
                ) / (dy * dy)
            else:
                aN = 0.0

            if j > 0:
                aS = 0.5 * (
                    D(t[n + 1], x[i], y[j])
                    + D(t[n + 1], x[i], y[j - 1])
                ) / (dy * dy)
            else:
                aS = 0.0

            aP = aE + aW + aN + aS

            p = idx(i, j)

            Sij = J[i, j] / den

            A[p, p] = (
                1
                + dt * aP
                + dt * K_values[n, i, j] * (1 - Sij)
            )

            if i < Nx - 1:
                A[p, idx(i + 1, j)] = -aE * dt

            if i > 0:
                A[p, idx(i - 1, j)] = -aW * dt

            if j < Ny - 1:
                A[p, idx(i, j + 1)] = -aN * dt

            if j > 0:
                A[p, idx(i, j - 1)] = -aS * dt

            # Explicit upwind transport term.
            upwindxPlus = 0.0
            upwindxMoins = 0.0
            upwindyPlus = 0.0
            upwindyMoins = 0.0

            # Right face in x direction.
            if i < Nx - 1:
                condxPlus = Ch_values[n, i, j] + Ch_values[n, i + 1, j]

                if condxPlus >= 0:
                    upwindxPlus = Sij * U[n, i, j]
                else:
                    upwindxPlus = (J[i + 1, j] / den) * U[n, i + 1, j]

            # Left face in x direction.
            if i > 0:
                condxMoins = Ch_values[n, i, j] + Ch_values[n, i - 1, j]

                if condxMoins >= 0:
                    upwindxMoins = (J[i - 1, j] / den) * U[n, i - 1, j]
                else:
                    upwindxMoins = Sij * U[n, i, j]

            # Upper face in y direction.
            if j < Ny - 1:
                condyPlus = Cd_values[n, i, j] + Cd_values[n, i, j + 1]

                if condyPlus >= 0:
                    upwindyPlus = Sij * U[n, i, j]
                else:
                    upwindyPlus = (J[i, j + 1] / den) * U[n, i, j + 1]

            # Lower face in y direction.
            if j > 0:
                condyMoins = Cd_values[n, i, j] + Cd_values[n, i, j - 1]

                if condyMoins >= 0:
                    upwindyMoins = (J[i, j - 1] / den) * U[n, i, j - 1]
                else:
                    upwindyMoins = Sij * U[n, i, j]

            # Interior points.
            if i > 0 and i < Nx - 1 and j > 0 and j < Ny - 1:
                Transp[n, i, j] = (
                    (
                        0.5
                        * (Ch_values[n, i + 1, j] + Ch_values[n, i, j])
                        * upwindxPlus
                        - 0.5
                        * (Ch_values[n, i, j] + Ch_values[n, i - 1, j])
                        * upwindxMoins
                    )
                    / dx
                    + (
                        0.5
                        * (Cd_values[n, i, j + 1] + Cd_values[n, i, j])
                        * upwindyPlus
                        - 0.5
                        * (Cd_values[n, i, j] + Cd_values[n, i, j - 1])
                        * upwindyMoins
                    )
                    / dy
                )

            # Left boundary.
            elif i == 0 and j > 0 and j < Ny - 1:
                Transp[n, i, j] = (
                    (
                        0.5
                        * (Ch_values[n, i + 1, j] + Ch_values[n, i, j])
                        * upwindxPlus
                    )
                    / dx
                    + (
                        0.5
                        * (Cd_values[n, i, j + 1] + Cd_values[n, i, j])
                        * upwindyPlus
                        - 0.5
                        * (Cd_values[n, i, j] + Cd_values[n, i, j - 1])
                        * upwindyMoins
                    )
                    / dy
                )

            # Right boundary.
            elif i == Nx - 1 and j > 0 and j < Ny - 1:
                Transp[n, i, j] = (
                    (
                        -0.5
                        * (Ch_values[n, i, j] + Ch_values[n, i - 1, j])
                        * upwindxMoins
                    )
                    / dx
                    + (
                        0.5
                        * (Cd_values[n, i, j + 1] + Cd_values[n, i, j])
                        * upwindyPlus
                        - 0.5
                        * (Cd_values[n, i, j] + Cd_values[n, i, j - 1])
                        * upwindyMoins
                    )
                    / dy
                )

            # Bottom boundary.
            elif j == 0 and i < Nx - 1 and i > 0:
                Transp[n, i, j] = (
                    (
                        0.5
                        * (Ch_values[n, i + 1, j] + Ch_values[n, i, j])
                        * upwindxPlus
                        - 0.5
                        * (Ch_values[n, i, j] + Ch_values[n, i - 1, j])
                        * upwindxMoins
                    )
                    / dx
                    + (
                        0.5
                        * (Cd_values[n, i, j + 1] + Cd_values[n, i, j])
                        * upwindyPlus
                    )
                    / dy
                )

            # Top boundary.
            elif j == Ny - 1 and i < Nx - 1 and i > 0:
                Transp[n, i, j] = (
                    (
                        0.5
                        * (Ch_values[n, i + 1, j] + Ch_values[n, i, j])
                        * upwindxPlus
                        - 0.5
                        * (Ch_values[n, i, j] + Ch_values[n, i - 1, j])
                        * upwindxMoins
                    )
                    / dx
                    + (
                        -0.5
                        * (Cd_values[n, i, j] + Cd_values[n, i, j - 1])
                        * upwindyMoins
                    )
                    / dy
                )

            # Bottom-left corner.
            elif i == 0 and j == 0:
                Transp[n, i, j] = (
                    0.5
                    * (Ch_values[n, i + 1, j] + Ch_values[n, i, j])
                    * upwindxPlus
                    / dx
                    + 0.5
                    * (Cd_values[n, i, j + 1] + Cd_values[n, i, j])
                    * upwindyPlus
                    / dy
                )

            # Top-left corner.
            elif i == 0 and j == Ny - 1:
                Transp[n, i, j] = (
                    0.5
                    * (Ch_values[n, i + 1, j] + Ch_values[n, i, j])
                    * upwindxPlus
                    / dx
                    - 0.5
                    * (Cd_values[n, i, j] + Cd_values[n, i, j - 1])
                    * upwindyMoins
                    / dy
                )

            # Bottom-right corner.
            elif i == Nx - 1 and j == 0:
                Transp[n, i, j] = (
                    -0.5
                    * (Ch_values[n, i, j] + Ch_values[n, i - 1, j])
                    * upwindxMoins
                    / dx
                    + 0.5
                    * (Cd_values[n, i, j + 1] + Cd_values[n, i, j])
                    * upwindyPlus
                    / dy
                )

            # Top-right corner.
            elif i == Nx - 1 and j == Ny - 1:
                Transp[n, i, j] = (
                    -0.5
                    * (Ch_values[n, i, j] + Ch_values[n, i - 1, j])
                    * upwindxMoins
                    / dx
                    - 0.5
                    * (Cd_values[n, i, j] + Cd_values[n, i, j - 1])
                    * upwindyMoins
                    / dy
                )

            b[p] = U[n, i, j] - dt * Transp[n, i, j]

    Unext = np.linalg.solve(A, b)
    U[n + 1, :, :] = Unext.reshape((Nx, Ny))


# -----------------------------------------------------------------------------
# Diagnostics
# -----------------------------------------------------------------------------

h_phys = x * Hphys
d_phys = y * Dphys


def topHeight(V):
    """Approximate top height: mean height of the 100 stems/ha with largest DBH."""

    cells = []

    for i in range(len(x)):
        for j in range(len(y)):
            numberOftrees = dx * dy * V[i, j]

            if numberOftrees > 0:
                cells.append((d_phys[j], h_phys[i], numberOftrees))

    cells.sort(key=lambda z: z[0], reverse=True)

    totaltrees = 0.0
    height_sum = 0.0

    for dbh, height, numbertrees in cells:
        remaining = 100 - totaltrees

        if numbertrees <= remaining:
            usedtrees = numbertrees
        else:
            usedtrees = remaining

        height_sum += usedtrees * height
        totaltrees += usedtrees

        if totaltrees >= 100:
            break

    return height_sum / totaltrees


ValueTopHeight = []

for n in range(len(t)):
    ValueTopHeight.append(topHeight(U[n, :, :]))

print("Simulated top height at final short age =", topHeight(U[-1, :, :]), "m")


def basal_area(V):
    G = 0.0

    for i in range(len(x)):
        for j in range(len(y)):
            if i == 0 or i == Nx - 1:
                wx = 0.5
            else:
                wx = 1.0

            if j == 0 or j == Ny - 1:
                wy = 0.5
            else:
                wy = 1.0

            G += (
                (np.pi / 4.0)
                * dx
                * dy
                * wx
                * wy
                * (d_phys[j] ** 2)
                * V[i, j]
            )

    return G


ValueBasalArea = []

for n in range(len(t)):
    ValueBasalArea.append(basal_area(U[n, :, :]))

print("Simulated basal area at final short age =", basal_area(U[-1, :, :]), "m²/ha")


# Optional non-blocking plots retained for compatibility but show() is disabled.

height_counts1 = dx * dy * np.sum(U[0, :, :], axis=1)

plt.figure(figsize=(6, 4))
plt.bar(h_phys, height_counts1, width=Hphys * dx, align="center")
plt.xlabel("height h (m)")
plt.ylabel("number of trees")
plt.title("Initial Distribution of trees by height class")
plt.grid()
plt.show()

height_counts2 = dx * dy * np.sum(U[-1, :, :], axis=1)

plt.figure(figsize=(6, 4))
plt.bar(h_phys, height_counts2, width=Hphys * dx, align="center")
plt.xlabel("height h (m)")
plt.ylabel("number of trees")
plt.title("Final short distribution of trees by height class")
plt.grid()
plt.show()

diam_cm = d_phys * 100

diam_counts1 = dx * dy * np.sum(U[0, :, :], axis=0)

plt.figure(figsize=(6, 4))
plt.bar(diam_cm, diam_counts1, width=100 * Dphys * dy)
plt.xlabel("DBH $\\phi$ (cm)")
plt.ylabel("number of trees")
plt.title("Initial distribution of trees by DBH class")
plt.grid()
plt.show()

diam_counts2 = dx * dy * np.sum(U[-1, :, :], axis=0)

plt.figure(figsize=(6, 4))
plt.bar(diam_cm, diam_counts2, width=100 * Dphys * dy)
plt.xlabel("DBH $\\phi$ (cm)")
plt.ylabel("number of trees")
plt.title("Final short distribution of trees by DBH class")
plt.grid()
plt.show()


# Total mass and positivity, preserving legacy mass formula.

mass = np.zeros(Nt + 1)
minU = np.zeros(Nt + 1)

for n in range(Nt + 1):
    mass[n] = dx * dy * np.sum(U[n, 1:, 1:])
    minU[n] = np.min(U[n, :, :])

print("Initial mass =", mass[0])
print("Final mass   =", mass[-1])
print("Minimum U    =", np.min(U))


plt.figure(figsize=(6, 4))
plt.plot(age, mass)
plt.xlabel("time (years)")
plt.ylabel("number of trees")
plt.title("Total number of trees")
plt.grid()
plt.show()

plt.figure(figsize=(6, 4))
plt.plot(age, ValueTopHeight)
plt.xlabel("time (years)")
plt.ylabel("Top height (m)")
plt.title("Top height")
plt.grid()
plt.show()

plt.figure(figsize=(6, 4))
plt.plot(age, ValueBasalArea)
plt.xlabel("time (years)")
plt.ylabel("Basal area (m² ha$^{-1}$)")
plt.title("Basal area")
plt.grid()
plt.show()