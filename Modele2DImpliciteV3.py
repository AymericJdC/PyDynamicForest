import numpy as np
import matplotlib.pyplot as plt

# Parameters of the normalized computational domain

# We work with normalized variables, therefore, the computational domain is (0,1) x (0,1).

Lx = 1.0
Ly = 1.0

# Final time in years.
# Here T = 40 means that we simulate the stand over 40 years.
T = 40

# Number of grid points in the two size directions.
Nx = 40
Ny = 40

# Number of time steps.
Nt = 10000

# Space and time steps.
dx = Lx / (Nx - 1)
dy = Ly / (Ny - 1)
dt = T / Nt

# Total initial number of trees per hectare.

N0 = 4186
# Spatial grids in normalized variables.
x = np.linspace(0.0, Lx, Nx, endpoint=True)
y = np.linspace(0.0, Ly, Ny, endpoint=True)

# Time grid.
t = np.linspace(0.0, T, Nt + 1, endpoint=True)


#  Model coefficients

# Diffusion coefficient 
def D(t, x, y):
    return 0.01 / (30**2)

# Mortality coefficient.
def K(t, x, y):
    return 0.05


# Initial condition

# Center of the Gaussian initial condition in normalized variables.

h0 = 8.1 / 30.0
d0 = 0.09 / 0.45

# Standard deviations in normalized variables.

sigh = 1.5/30
sigd = 0.02/0.45

# We compute the normalization constant Z0 so that
# integral u0(x,y) dx dy = N0.
#
# Zc[i,j] approximates
# int_0^{x_i} int_0^{y_j} exp(...) dy dx.
Zc = np.zeros((Nx, Ny))

# Since the integral over a domain of zero width is zero.
Zc[0, :] = 0.0
Zc[:, 0] = 0.0

# Cumulative rectangle rule.
for i in range(1,Nx): 
        for j in range(1,Ny):
            Zc[i,j]=Zc[i-1,j]+Zc[i,j-1]-Zc[i-1,j-1]+dy*dx*(np.exp( -(x[i]-h0)**2/(2*sigh**2) -(y[j]-d0)**2/(2*sigd**2) ))

# Normalization constant.
Z0 = Zc[-1, -1]

# Initial density.
# The factor N0/Z0 ensures that the total initial mass is approximately N0.
def u0(x,y): #condition initiale
    return np.exp( -(x-h0)**2/(2*sigh**2) -(y-d0)**2/(2*sigd**2) )*N0/Z0


# Growth velocities in normalized variables


rh = 0.8 / 30.0

def Ch(t, x, y):
    return rh * (1 - x / Lx)

rd = 0.008 / 0.45

def Cd(t, x, y):
    return rd * (1 - y / Ly)


# Indexing convention for the linear system

# Converts a 2D grid index (i,j) into a 1D vector index p.
# This is needed because the linear system is written as A U^{n+1} = b.
def idx(i, j):
    return i * Ny + j


# Precomputation of coefficient values on the grid

# These arrays store K, Ch and Cd at every time and grid point.
# Since K, Ch and Cd do not actually depend on time here, this is not necessary,
# but it keeps the code close to a more general time-dependent case.
K_values = np.zeros((Nt + 1, Nx, Ny))
Ch_values = np.zeros((Nt + 1, Nx, Ny))
Cd_values = np.zeros((Nt + 1, Nx, Ny))

# Values of the initial condition on the grid.
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


#Storage of the numerical solution

# U[n,i,j] approximates u(t^n, x_i, y_j).
U = np.zeros((Nt + 1, Nx, Ny))

# Transp[n,i,j] stores the explicit transport term
# div(C S[u] u) at time t^n.
Transp = np.zeros((Nt + 1, Nx, Ny))

# Initial condition.
U[0, :, :] = u0_values

# Size of the linear system at each time step.
N = Nx * Ny


# ============================================================
# 8. Time loop
# ============================================================

for n in range(Nt):

    #  Computation of the cumulative distribution J
    # J[i,j] approximates
    # int_0^{x_i} int_0^{y_j} U(t^n, xi, eta) d eta d xi.
    #
    # The status function is then S = J / den.
    J = np.zeros((Nx, Ny))

    J[0, :] = 0.0
    J[:, 0] = 0.0

    for i in range(1, Nx):
        for j in range(1, Ny):
            J[i,j]=J[i-1,j]+J[i,j-1]-J[i-1,j-1]+dy*dx*U[n,i,j]

    # Total mass of the population at time t^n.
    # This is the denominator in the status function.
    den = J[-1, -1]

    # Numerical safety to avoid division by zero.
    if den < 1e-15:
        den = 1e-15

    #  Construction of the linear system
    #
    # We solve:
    # (I - dt * diffusion + dt * reaction) U^{n+1}= U^n - dt * transport(U^n).
    # Diffusion and mortality are implicit.
    # Transport is explicit.
    A = np.zeros((N, N), dtype=float)
    b = np.zeros(N, dtype=float)

    for i in range(Nx):
        for j in range(Ny):

            # Diffusion coefficients with homogeneous Neumann boundary conditions.
            # Missing faces at the boundary are set to zero.

            if i < Nx - 1:
                aE = 0.5 * (
                    D(t[n], x[i], y[j]) + D(t[n], x[i+1], y[j])
                ) / (dx * dx)
            else:
                aE = 0.0

            if i > 0:
                aW = 0.5 * (
                    D(t[n], x[i], y[j]) + D(t[n], x[i-1], y[j])
                ) / (dx * dx)
            else:
                aW = 0.0

            if j < Ny - 1:
                aN = 0.5 * (
                    D(t[n], x[i], y[j]) + D(t[n], x[i], y[j+1])
                ) / (dy * dy)
            else:
                aN = 0.0

            if j > 0:
                aS = 0.5 * (
                    D(t[n], x[i], y[j]) + D(t[n], x[i], y[j-1])
                ) / (dy * dy)
            else:
                aS = 0.0

            aP = aE + aW + aN + aS

            # 1D index corresponding to the point (i,j).
            p = idx(i, j)

            # Status function at the grid point (i,j).
            Sij = J[i, j] / den

            # Diagonal coefficient:
            # identity + implicit diffusion + implicit mortality.
            A[p, p] = 1 + dt * aP + dt * K_values[n, i, j] * (1 - Sij)

            # Off-diagonal coefficients from the diffusion stencil.
            if i < Nx - 1:
                A[p, idx(i+1, j)] = -aE * dt
            if i > 0:
                A[p, idx(i-1, j)] = -aW * dt
            if j < Ny - 1:
                A[p, idx(i, j+1)] = -aN * dt
            if j > 0:
                A[p, idx(i, j-1)] = -aS * dt

            # Explicit upwind transport term
            
            # We discretize div(C S[u] u) by an upwind finite
            # volume-type flux.
            #
            # The transported quantity is S[u] u.
            # ------------------------------------------------

            upwindxPlus = 0.0
            upwindxMoins = 0.0
            upwindyPlus = 0.0
            upwindyMoins = 0.0

            # Right face in the x direction.
            if i < Nx - 1:
                condxPlus = Ch_values[n, i, j] + Ch_values[n, i+1, j]

                if condxPlus >= 0:
                    upwindxPlus = Sij * U[n, i, j]
                else:
                    upwindxPlus = (J[i+1, j] / den) * U[n, i+1, j]

            # Left face in the x direction.
            if i > 0:
                condxMoins = Ch_values[n, i, j] + Ch_values[n, i-1, j]

                if condxMoins >= 0:
                    upwindxMoins = (J[i-1, j] / den) * U[n, i-1, j]
                else:
                    upwindxMoins = Sij * U[n, i, j]

            # Upper face in the y direction.
            if j < Ny - 1:
                condyPlus = Cd_values[n, i, j] + Cd_values[n, i, j+1]

                if condyPlus >= 0:
                    upwindyPlus = Sij * U[n, i, j]
                else:
                    upwindyPlus = (J[i, j+1] / den) * U[n, i, j+1]

            # Lower face in the y direction.
            if j > 0:
                condyMoins = Cd_values[n, i, j] + Cd_values[n, i, j-1]

                if condyMoins >= 0:
                    upwindyMoins = (J[i, j-1] / den) * U[n, i, j-1]
                else:
                    upwindyMoins = Sij * U[n, i, j]

            # ------------------------------------------------
            # 8.4. Discrete divergence of the transport flux
            # ------------------------------------------------
            #
            # Boundary fluxes are set to zero.
            # The following cases implement the interior points,
            # edges, and corners separately.
            # ------------------------------------------------

            # Interior points.
            if i > 0 and i < Nx - 1 and j > 0 and j < Ny - 1:
                Transp[n, i, j] = (
                    (
                        0.5 * (Ch_values[n, i+1, j] + Ch_values[n, i, j]) * upwindxPlus
                        - 0.5 * (Ch_values[n, i, j] + Ch_values[n, i-1, j]) * upwindxMoins
                    ) / dx
                    +
                    (
                        0.5 * (Cd_values[n, i, j+1] + Cd_values[n, i, j]) * upwindyPlus
                        - 0.5 * (Cd_values[n, i, j] + Cd_values[n, i, j-1]) * upwindyMoins
                    ) / dy
                )

            # Left boundary.
            if i == 0 and j > 0 and j < Ny - 1:
                Transp[n, i, j] = (
                    (
                        0.5 * (Ch_values[n, i+1, j] + Ch_values[n, i, j]) * upwindxPlus
                    ) / dx
                    +
                    (
                        0.5 * (Cd_values[n, i, j+1] + Cd_values[n, i, j]) * upwindyPlus
                        - 0.5 * (Cd_values[n, i, j] + Cd_values[n, i, j-1]) * upwindyMoins
                    ) / dy
                )

            # Right boundary.
            if i == Nx - 1 and j > 0 and j < Ny - 1:
                Transp[n, i, j] = (
                    (
                        - 0.5 * (Ch_values[n, i, j] + Ch_values[n, i-1, j]) * upwindxMoins
                    ) / dx
                    +
                    (
                        0.5 * (Cd_values[n, i, j+1] + Cd_values[n, i, j]) * upwindyPlus
                        - 0.5 * (Cd_values[n, i, j] + Cd_values[n, i, j-1]) * upwindyMoins
                    ) / dy
                )

            # Bottom boundary.
            if j == 0 and i < Nx - 1 and i > 0:
                Transp[n, i, j] = (
                    (
                        0.5 * (Ch_values[n, i+1, j] + Ch_values[n, i, j]) * upwindxPlus
                        - 0.5 * (Ch_values[n, i, j] + Ch_values[n, i-1, j]) * upwindxMoins
                    ) / dx
                    +
                    (
                        0.5 * (Cd_values[n, i, j+1] + Cd_values[n, i, j]) * upwindyPlus
                    ) / dy
                )

            # Top boundary.
            if j == Ny - 1 and i < Nx - 1 and i > 0:
                Transp[n, i, j] = (
                    (
                        0.5 * (Ch_values[n, i+1, j] + Ch_values[n, i, j]) * upwindxPlus
                        - 0.5 * (Ch_values[n, i, j] + Ch_values[n, i-1, j]) * upwindxMoins
                    ) / dx
                    +
                    (
                        - 0.5 * (Cd_values[n, i, j] + Cd_values[n, i, j-1]) * upwindyMoins
                    ) / dy
                )

            # Bottom-left corner.
            if i == 0 and j == 0:
                Transp[n, i, j] = (
                    0.5 * (Ch_values[n, i+1, j] + Ch_values[n, i, j]) * upwindxPlus / dx
                    +
                    0.5 * (Cd_values[n, i, j+1] + Cd_values[n, i, j]) * upwindyPlus / dy
                )

            # Top-left corner.
            if i == 0 and j == Ny - 1:
                Transp[n, i, j] = (
                    0.5 * (Ch_values[n, i+1, j] + Ch_values[n, i, j]) * upwindxPlus / dx
                    -
                    0.5 * (Cd_values[n, i, j] + Cd_values[n, i, j-1]) * upwindyMoins / dy
                )

            # Bottom-right corner.
            if i == Nx - 1 and j == 0:
                Transp[n, i, j] = (
                    - 0.5 * (Ch_values[n, i, j] + Ch_values[n, i-1, j]) * upwindxMoins / dx
                    +
                    0.5 * (Cd_values[n, i, j+1] + Cd_values[n, i, j]) * upwindyPlus / dy
                )

            # Top-right corner.
            if i == Nx - 1 and j == Ny - 1:
                Transp[n, i, j] = (
                    - 0.5 * (Ch_values[n, i, j] + Ch_values[n, i-1, j]) * upwindxMoins / dx
                    -
                    0.5 * (Cd_values[n, i, j] + Cd_values[n, i, j-1]) * upwindyMoins / dy
                )

            # Right-hand side:
            # U^n - dt * div(C S[U^n] U^n).
            b[p] = U[n, i, j] - dt * Transp[n, i, j]

    #  Linear solve
    
    # We solve the implicit diffusion-reaction system.
    Unext = np.linalg.solve(A, b)

    # Convert the solution vector back to a 2D grid.
    U[n+1, :, :] = Unext.reshape((Nx, Ny))


#  Plot of the initial and final solution in physical variables

Hphys = 30.0
Dphys = 0.45

# Hauteurs physiques en mètres
h_phys = x * Hphys

# Nombre d'arbres par classe de hauteur au temps initial
height_counts1 = dx * dy * np.sum(U[0, :, :], axis=1)

plt.figure(figsize=(6, 4))
plt.bar(h_phys, height_counts1, width=Hphys*dx, align='center')
plt.xlabel("height h (m)")
plt.ylabel("number of trees")
plt.title("Initial Distribution of trees (t=20 years) by height class")
plt.grid()
plt.show()

# Nombre d'arbres par classe de hauteur à la moitié du temps 

height_counts3 = dx * dy * np.sum(U[5000, :, :], axis=1)

plt.figure(figsize=(6, 4))
plt.bar(h_phys, height_counts3, width=Hphys*dx, align='center')
plt.xlabel("height h (m)")
plt.ylabel("number of trees")
plt.title("Distribution of trees by height class at time t=40 years")
plt.grid()
plt.show()

# Nombre d'arbres par classe de hauteur au temps final

height_counts2 = dx * dy * np.sum(U[-1, :, :], axis=1)

plt.figure(figsize=(6, 4))
plt.bar(h_phys, height_counts2, width=Hphys*dx, align='center')
plt.xlabel("height h (m)")
plt.ylabel("number of trees")
plt.title("Final Distribution of trees (t=60 years) by height class")
plt.grid()
plt.show()

# Diamètres physiques en cm
diam_cm = y[1:] * Dphys * 100

# Nombre d'arbres par classe de diamètre au temps initial
diam_counts1 = dx * dy * np.sum(U[0, 1:, 1:], axis=0)

plt.figure(figsize=(6, 4))
plt.bar(diam_cm, diam_counts1, width=100 * Dphys * dy)
plt.xlabel("DBH $\\phi$ (cm)")
plt.ylabel("number of trees")
plt.title("Initial distribution of trees (t=20 years) by DBH class")
plt.grid()
plt.show()

# Nombre d'arbres par classe de diamètre à la moitié du temps

diam_counts3 = dx * dy * np.sum(U[5000, 1:, 1:], axis=0)

plt.figure(figsize=(6, 4))
plt.bar(diam_cm, diam_counts3, width=100 * Dphys * dy)
plt.xlabel("DBH $\\phi$ (cm)")
plt.ylabel("number of trees")
plt.title("Distribution of trees by DBH class at time t=40 years")
plt.grid()
plt.show()

# Nombre d'arbres par classe de diamètre au temps final
diam_counts2 = dx * dy * np.sum(U[-1, 1:, 1:], axis=0)

plt.figure(figsize=(6, 4))
plt.bar(diam_cm, diam_counts2, width=100 * Dphys * dy)
plt.xlabel("DBH $\\phi$ (cm)")
plt.ylabel("number of trees")
plt.title("Final distribution of trees (t=60 years) by DBH class")
plt.grid()
plt.show()

# Diagnostics: total mass and positivity

# Total mass at each time step.
mass = np.zeros(Nt + 1)

# Minimum value of U at each time step, used to check positivity.
minU = np.zeros(Nt + 1)

for n in range(Nt + 1):
    mass[n] = dx * dy * np.sum(U[n, 1:, 1:])
    minU[n] = np.min(U[n, :, :])

print("Initial mass =", mass[0])
print("Final mass   =", mass[-1])
print("Minimum U    =", np.min(U))

plt.figure()
plt.plot(t, mass)
plt.xlabel("time")
plt.ylabel("total mass")
plt.title("Total number of trees")
plt.grid()
plt.show()