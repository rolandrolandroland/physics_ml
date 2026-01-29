# An Introduction to Physics Informed Neural Networks (PINNs)
## Physics Informed Neural Network for 1 Dimensional Heat Equation

Welcome! This is a tutorial on a good starter exercise to introduce you to PINNs by solving a 1D heat equation.
This assumes the user has some baseline knowledge of neural networks and is familiar with
concepts like optimizer functions, layers, and weights.
### Table of abbreviations
T = Temperature  
u = Unknown variable (used for temperature)  
t = time  
x = position  
$ \alpha$ = diffusion coefficient 
### What is a PINN?
PINNs work by incorporating physical laws into neural networks.
Specifically, this can be done by incorporating a physical term into the model's loss function.
Rather than just talk about this in the abstract,
we will be walking through the example of the 1D heat equation,
$ \frac{\delta T|}{dt} = \alpha \frac{\delta^2T}{dx^2}$  
We can also write this more compactly as $ T_t = \alpha T_{xx} $  

### What are we Modeling?
This project solves one of the most simple systems of heat diffusion, a 1D
rod with known thermal diffusivity $\alpha$, initial conditions, and boundary conditions.
For example, we may choose that the entire rod is at 0 K, then an
infinite heat source held at 100 K is attached to the left end at the same
time (t = 0) an infinite heat sink held at 0 K is attached to the right end.  At
any location on the rod, after any amount of time after the ends are connected,
what is the temperature of the rod?

### Model Outline
A key aspect of PINNs like this is how we train the model.
The model is trained using three sets of points
1) Initial conditions: we know the state of the rod before the experiment begins 
2) Boundary conditions: we know the function that controls the source and sink at each end. 
3) Physically determined points: For some number of random points throughout the rod,
we solve this heat equation for those points.  More on this later.   

### Solving the Physically Determined Points
This may naturally bring up the question: "If you can solve the heat equation
for the physically determined points, why not just do that for the entire system?
Why use a neural network at all?" Good question.  

We don't actually solve the temperature at these points.
Rather, we use pytorch's autorgrad function to compute the $T_t - \alpha T_{xx} = 0$.  
Let's backup and look at exactly how our PINN model works.
We define a number of cycles ('epochs' in the code) for our model to iterate.
The model initializes as some function of $T$ given inputs $x$ and $t$. 
For each iteration, our model evaluates this function to get values for the temperature at the initial and boundary conditions.
Then, we use the autograd function to take derivatives of this function to get values for
$T_t$ and $T_{xx}$ at each of the chosen random points and evaluates $T_t - \alpha T_{xx} = 0$
to get a residual (i.e., how much does the difference deviate from 0). 
Since we also know the true values for temperature at the initial and boundary conditions,
we can get a loss for the predictions for each of those as well. 
Then the losses from each category are combined into a total loss.
Since the model essentially uses random weights for its first iteration, the loss
will initially be quite high, but with each iteration the model updates its function to reduce this residual, then iterates again. 

### Evaluating the Model
To evaluate the effectiveness of the model, we compare it to temperature
values found using a finite difference method (FDM) solver.
We choose to do this using the Crank-Nicolson method.

Crank-Nicolson is a method for solving partial differential equations
(PDEs) using discretization
For a temperature $T$ as a function of distance $x$ (indexed using $i$) and time $t$ (indexed using $n$),  
$T(x_i,t_n)$ ,$T_t = \frac{T^{n+1}_i-T^n_i}{\Delta t}$  
This is just saying that the rate of change of the temperature with respect
to time is the temperature at one moment minus the temperature at the previous
moment, divided by the time that passes between the moment.  
If we want to evaluate with respect to distance instead, it is just  
$T_x = \frac{T^{n}_{i+1}-T^n_i}{\Delta t}$  
We can then find the second spatial derivative  
$T^n_{xx,i} = \frac{T^n_{i+1} - 2T^n_i + T^n_{i-1}}{\Delta x^2}$  
and then replace $n$ with $n+1$ to find another term we will need  
$T^{n+1}_{xx,i} = \frac{T^{n+1}_{i+1} - 2T^{n+1}_i + T^{n+1}_{i-1}}{\Delta x^2}$  
This gives us all of the terms that we need. For a more detailed discussion
please see either https://en.wikipedia.org/wiki/Crank%E2%80%93Nicolson_method or
https://www.sfu.ca/~rjones/bus864/notes/notes2.pdf .

Thus, we are able to compare the model in pinn_model.py to the 
results in fdm_1d.py to see how well our model works! We do this in
the solve_and_compare.py script, which also plots the results of both!