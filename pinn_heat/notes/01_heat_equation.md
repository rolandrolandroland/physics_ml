# Topic: Crank–Nicolson for 1D heat

## Problem statement
We solve:

$$ T_t = \alpha T_{xx}, \quad x\in[0,L],\ t\in[0,t_{\max}]$$


## Discretization
Grid:
- $x_i = i\Delta x$, $i=0,\dots,N_x-1$
- $t_n = n\Delta t$, $n=0,\dots,N_t-1$


Second derivative:
$$
T_{xx}(x_i,t_n)\approx \frac{T_{i+1}^n - 2T_i^n + T_{i-1}^n}{\Delta x^2}
$$

## Implementation mapping
- `T[n, i]` ↔ $T_i^n$
- interior indices: $i=1,\dots,N_x-2$
- boundaries: $i=0$, $i=N_x-1$
  (start index at 0, $N_x$ total points)
## Checks / pitfalls
- Sign of Robin BC
- Stability: $r=\alpha\Delta t/\Delta x^2$

## Use Crank Nicolson method
starting from the PDE relating temperature as a function of time to the second derivative of temperature with respect to position
$ T_t = \alpha T_{xx}$

Discretize each half, substituting

$T_t = \frac{T^{n+1}_i - T^n_i}{\Delta t} $

$T^n_{xx,i} = \frac{T^n_{i+1} - 2T^n_i + T^n_{i-1}}{\Delta x^2}$ 

$T^{n+1}_{xx,i} = \frac{T^{n+1}_{i+1} - 2T^{n+1}_i + T^{n+1}_{i-1}}{\Delta x^2}$

