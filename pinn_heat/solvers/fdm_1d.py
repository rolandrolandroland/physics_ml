# this provides an analytical solution to the 1D heat equation that will be used to validate the PINN
import numpy as np
from scipy.linalg import solve_banded

import matplotlib.pyplot as plt

def tridiag_matvec(a, b, c, u):
    Nint = len(b)

    rhs = np.zeros(Nint)
    rhs[0] = b[0]*u[0] + c[0]*u[1]
    rhs[1:-1] = a[:-1]*u[:-2] + b[1:-1]*u[1:-1] + c[1:]*u[2:]
    rhs[-1] = a[-1]*u[-2] + b[-1]*u[-1]
    return rhs

def crank_nicolson_time_march(x , t, r, T, Nx, T_left_fn, T_right_fn):
    # define number of interior temperatures as total number of temperatures -2 (for 2 boundaries
    Nint = Nx - 2

    # make rhs operator
    a_right = np.full(Nint-1, r/2, dtype=float)
    b_right = np.full(Nint, 1-r, dtype=float)
    c_right = np.full(Nint-1, r/2, dtype=float)

    # I will use scipy.linalg.solve_banded
    # make tridiagonal matrix into 3 x Nint matrix with each row a diagnonal or off diagonal
    ab = np.zeros((3, Nint), dtype=float)
    ab[0,1:] = -r/2 # c_left
    ab[1,:] = 1+r # b_left
    ab[2,:-1] = -r/2 # a_left



    # define interior unknown vector u
    Nt = len(t)
    for n in range(Nt -1):
        u = T[n, 1:-1]
        rhs = tridiag_matvec(a_right, b_right, c_right, u)

        T_left_n = T_left_fn(t[n])
        T_left_np1 = T_left_fn(t[n+1])
        T_right_n = T_right_fn(t[n])
        T_right_np1 = T_right_fn(t[n+1])

        # apply left boundary condition of T_left_fn(n)
        rhs[0] += (r/2) * (T_left_n + T_left_np1)
        # apply right boundary condition of T_right_fn(n)
        rhs[-1] += (r/2) * (T_right_n + T_right_np1)
        T[n+1, 1:-1] = solve_banded((1, 1), ab, rhs)
    return T


def solve_heat_1d_fdm(alpha, L, t_max, Nx, Nt, T_init_fn, T_left_fn, T_right_fn, method):
    # alpha is constant of conductivity
    # L is domain maximum (length)
    # t_max is domain max (time)
    # Nx is the number of points in domain (length)
    # Nt is number of points in domain (time)
    # T_init_fn is function of x for initial time T(x, t =0)
    # T_left_fn is function of t at x = 0 T(x = 0, t)
    # T_right_fn is function of t at x = L T(x = L, t)
    # method is

    # first, build spatial grid
    # Nx equally spaced points between 0 and L
    x = np.linspace(0, L, Nx)
    # build time grid
    # Nt equally spaced points between 0 and t_max
    t = np.linspace(0, t_max, Nt)

    # compute step sizes
    dx = x[1] - x[0]
    dt = t[1] - t[0]

    # create solution array
    T = np.zeros(shape = (Nt, Nx))

    # apply initial condition of n = 0 (0 time)
    # T(0, i) = T_init_fn(i)
    T[0, :] = T_init_fn(x)

    # apply left boundary condition of T_left_fn(n)
    T[: ,0] = T_left_fn(t)

    # apply right boundary condition of T_right_fn(n)
    T[:,-1] = T_right_fn(t)

    # compute diffusion number r = alpha * dt /dx^2
    # dimensionless
    # controls stability and behavior
    r = alpha * dt /(dx **2)
    if (r > 0.5):
        print(f"Warning: r is over 0.5 (r ={r})")

    if method == "explicit":
        print("Currently on functionality for method == crank_nicolson")

    elif method == "crank_nicolson":
        T = crank_nicolson_time_march(x, t, r, T, Nx, T_left_fn, T_right_fn)
    return x, t, T

if __name__ == "__main__":
    T_init_fn = lambda x : np.zeros_like(x) # initial temp is 0
    T_left_fn = lambda t : np.ones_like(t) * 100
    T_right_fn = lambda t: np.zeros_like(t)
    alpha = 0.01
    L = 1
    t_max = 2
    Nx = 50
    Nt = 200

    x, t, T = solve_heat_1d_fdm(alpha, L, t_max, Nx, Nt, T_init_fn, T_left_fn, T_right_fn, method = "crank_nicolson")
    print("simulation complete!")

    ## plot heatmap of result
    plt.figure(figsize=(10,10))
    plt.imshow(T, cmap = 'hot', extent = (0, t_max, 0, L))
    plt.colorbar(label="Temperature (K)")
    plt.xlabel("Time (s)")
    plt.ylabel("Position")
    plt.title("FDM Reference solution (CN)")
    plt.show()