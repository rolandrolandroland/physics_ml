# old lines of code that i no longer need but don't want to get rid of yet

# run FDM model
# run PINN model
# pick random points to use heat equation on and calculate T
xmax = 1
tmax = 1

x_phys = torch.rand(nphys, 1) * xmax
t_phys = torch.rand(nphys, 1) * tmax

# calculate initial conditions
x_init = torch.linspace(0, 1, n_init_cond) * xmax

# intial x values (evenly spaced 1d vector)
x_init = torch.linspace(0, xmax, n_init_cond).view(-1, 1)
# initial time (0's across same domain as x_init)
t_init = torch.zeros_like(x_init)

# target initial temperature everywhere
u_init_target = torch.zeros_like(x_init)
# Use your FDM functions to define PINN targets
u_ic_target = torch.tensor(T_init_fn(x_init.numpy()), dtype=torch.float32)

# define maximum temperature
umax = 100

nbc = 100
nic = 100

# for left boundary, temp (u) is always umax. generate random points in time
t_boundary = torch.rand(nbc, 1)*tmax
# x is 0 for each of those points
x_left = torch.zeros_like(t_boundary)
# generate an equal number of umax values
#u_left= torch.ones_like(t_boundary)*umax
u_left_target = torch.tensor(T_left_fn(t_boundary.numpy()), dtype=torch.float32)

# now right boundary - x will always be x max
x_right = torch.ones_like(t_boundary)*xmax
# generate u values for the right
#u_right = torch.zeros_like(t_boundary)
u_right_target = torch.tensor(T_right_fn(t_boundary.numpy()), dtype=torch.float32)


## plot heatmap of result
plt.figure(figsize=(10, 10))
plt.imshow(T, cmap='hot', extent=(0, t_max, 0, L))
plt.colorbar(label="Temperature (K)")
plt.xlabel("Time (s)")
plt.ylabel("Position")
plt.title("FDM Reference solution (CN)")
plt.show()