import torch
from torch import nn
import matplotlib.pyplot as plt

class HeatPINN(nn.Module):
    # Build a class that inherits from nn.Module
    # two main jobs:
    # Predict (forward pass) and Evaluate Physics (the Residual)
    # since we are taking x and t (two variables) as input, the first layer must have two neurons
    # since we are predicting T (one variable), the final layer must have one neuron
    def __init__(self, layers = [2, 32, 32, 1]):
        super().__init__()
        # initialize module list
        self.net = nn.ModuleList()
        # build network, layer by layer
        for layer in range(len(layers) -1):
            # for layer i and i +1, connect them using linear weights
            self.net.append(nn.Linear(layers[layer], layers[layer + 1]))

        # use Tanh activation function
        # define it as activation
        self.activation = nn.Tanh()

    # forward march for making predictions
    def forward(self, x, t):
        # x and t must be concat'd into 2d matrix, expand dim = 1 (horizontal axis, columns)
        u = torch.cat([x, t], 1)
        # iterate through each layer except the last
        for layer in self.net[:-1]:
            # pass each layer through activation function
            u = self.activation(layer(u))
        # for final layer, update it manually
        u = self.net[-1](u)
        return u

    # compare to physical model
    # for a perfect network, u_t = alpha* u_(xx), or temp as a function of time equals alpha times the second derivative of temp with respect to space
    def compute_residual(self, x, t, alpha):
        # set x and t to record autograd operations
        x.requires_grad_(True)
        t.requires_grad_(True)

        # get prediction using forward method
        u_pred = self.forward(x, t)

        # get first derivative with respect to x and t
        u_grad = torch.autograd.grad(outputs = u_pred, inputs = (x,t), create_graph = True, grad_outputs = torch.ones_like(u_pred))

        # pull out the derivatives with repsect to x and t
        u_grad_x = u_grad[0]
        u_grad_t = u_grad[1]

        # get second derivative with respect to x
        u_grad_xx = torch.autograd.grad(outputs = u_grad_x, inputs = x, create_graph = True, grad_outputs = torch.ones_like(u_grad_x))[0]
        # compute residual
        R =  u_grad_t -alpha * u_grad_xx
        return R


# define function to take