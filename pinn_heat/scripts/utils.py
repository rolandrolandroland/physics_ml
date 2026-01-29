import torch

# need a script that takes data in the form that it goes into the fdm solver
# and returns data in the format that can be fed into the pinn solver
# so that both models can use the same variables
def generate_pinn_data(u_ic_fn, u_bc_left_fn, u_bc_right_fn, L, t_max, n_phys, n_ic, n_bc):
    # n_phys is the number of points to use in physics part of PINN model
    # L is domain length
    # t_max is maximum amount of time
    x_phys = torch.rand(n_phys, 1) * L
    t_phys = torch.rand(n_phys, 1) * t_max

    # for initial conditions, we want a linear grid of points for domain
    x_init = torch.linspace(0, L, n_ic).view(-1, 1)
    # for time, they are all just 0
    t_init = torch.zeros_like(x_init)

    # return the u for initial conditions based on input function
    u_ic_target = torch.tensor(u_ic_fn(x_init.numpy()), dtype=torch.float32)

    # time for boundary conditions = random times
    t_bc = torch.rand(n_bc, 1) * t_max
    # x for left boundary is 0
    x_left = torch.zeros_like(t_bc)
    # x for right boundary is the length of the domain
    x_right = torch.ones_like(t_bc) * L

    u_bc_left_target = torch.tensor(u_bc_left_fn(t_bc.numpy()), dtype=torch.float32)
    u_bc_right_target = torch.tensor(u_bc_right_fn(t_bc.numpy()), dtype=torch.float32)

    return (x_phys, t_phys), (x_init, t_init, u_ic_target), (x_left, x_right, t_bc, u_bc_left_target, u_bc_right_target)