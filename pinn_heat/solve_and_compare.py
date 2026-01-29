from solvers.pinn_model import *
from solvers.fdm_1d import *
from scripts.utils import *
# run FDM model
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

bar_label = "Temperature"
x_label = "Time (t)"
y_label = "Space (x)"

## plot heatmap of result
plt.figure(figsize=(8, 6))
# make meshgrid
t_fdm_mesh, x_fdm_mesh = np.meshgrid(t, x, indexing='ij')
plt.pcolormesh(t_fdm_mesh, x_fdm_mesh, T, cmap='hot', shading='auto')
plt.colorbar(label=bar_label)
plt.xlabel(x_label)
plt.ylabel(y_label)
plt.title("FDM Reference solution (CN)")
plt.show()



nphys = 1000
n_init_cond = 100

phys_data, ic_data, bc_data =  generate_pinn_data(u_ic_fn = T_init_fn,
                                                  u_bc_left_fn =T_left_fn ,
                                                  u_bc_right_fn = T_right_fn,
                                                  L = L,
                                                  t_max =t_max,
                                                  n_phys = nphys,
                                                  n_ic = n_init_cond,
                                                  n_bc = n_init_cond)



# initialize model
model = HeatPINN()

# determine if cpu or gpu is best
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# move model to proper device
model.to(device)

# choose optimizer function
optimizer = torch.optim.Adam(model.parameters())

# choose loss function
mse_loss = nn.MSELoss()


# make training loop
ntrain = 10000
# define variable for how often to print the loss
print_freq = 100

x_init = ic_data[0]
t_init = ic_data[1]
u_init_target = ic_data[2]

x_left = bc_data[0]
x_right = bc_data[1]
t_boundary = bc_data[2]
u_left_target = bc_data[3]
u_right_target = bc_data[4]

x_phys = phys_data[0]
t_phys = phys_data[1]

x_init, t_init, u_init_target = x_init.to(device), t_init.to(device), u_init_target.to(device)
x_left, x_right, t_boundary = x_left.to(device), x_right.to(device), t_boundary.to(device)
u_left_target, u_right_target = u_left_target.to(device), u_right_target.to(device)
x_phys, t_phys = x_phys.to(device), t_phys.to(device)

for epoch in range(ntrain):

    # reset gradient
    optimizer.zero_grad()

    # make predictions for initial conditions
    u_pred_init = model(x_init, t_init)
    # compare predictions to known initial conditions
    loss_init = mse_loss(u_pred_init, u_init_target)

    # make predictions for boundary conditions
    u_pred_left = model(x_left, t_boundary)
    u_pred_right = model(x_right, t_boundary)
    # compare predictions to known boundary conditions
    loss_left_bc = mse_loss(u_pred_left, u_left_target)
    loss_right_bc = mse_loss(u_pred_right, u_right_target)

    # evaluate some positions using physics
    phys_res = model.compute_residual(x_phys, t_phys, alpha)
    # residuals should be 0
    loss_phys = mse_loss(phys_res, torch.zeros_like(phys_res))

    # add up all losses
    total_loss = loss_init*10 + loss_left_bc*10 + loss_right_bc*10 + loss_phys
    #backpropogate
    total_loss.backward()
    optimizer.step()

    # every so often, print loss
    if epoch % print_freq == 0:
        print(f"epoch: {epoch}, loss: {total_loss.item()}")



# plot
# create grid
# use same points as the 1d FDM solver used

x_grid = torch.linspace(0, L, Nx)
t_grid = torch.linspace(0, t_max, Nt)
T_mesh, X_mesh = torch.meshgrid(t_grid, x_grid, indexing='ij')

# 2. Flatten (Ensuring x goes to x and t goes to t)
t_input = T_mesh.reshape(-1, 1).to(device) # Remember to move to device!
x_input = X_mesh.reshape(-1, 1).to(device)

with torch.no_grad():
    u_pred = model(x_input, t_input).reshape(Nt, Nx)

plt.figure(figsize=(8, 6))
plt.pcolormesh(T_mesh.numpy(), X_mesh.numpy(), u_pred.numpy(), cmap='hot', shading='auto')
plt.colorbar(label=bar_label)
plt.xlabel(x_label)
plt.ylabel(y_label)
plt.title('PINN Predicted Heat Evolution')
plt.show()

# plot difference
# 1. Align the data (ensure both are on CPU and NumPy)
u_pinn_final = u_pred.cpu().numpy()

# 2. Calculate the difference (Residual)
# Since both are (200, 50), this math works perfectly
error_map = np.abs(T - u_pinn_final)

# 3. Plot the Difference
plt.figure(figsize=(8, 6))
plt.pcolormesh(T_mesh.numpy(), X_mesh.numpy(), error_map, cmap='viridis')
plt.colorbar(label='Absolute Error')
plt.xlabel(x_label)
plt.ylabel(y_label)
plt.title('Difference Map: |FDM - PINN|')
plt.show()

# 4. Print Accuracy
print(f"Max Deviation: {np.max(error_map):.2f} degrees")
print(f"Total Deviation: {np.sum(error_map):.2f} degrees")
## solve physically

