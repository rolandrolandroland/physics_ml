## Introduction
### 08/17/2026
The initial version of this project contains a single-module simulator.  We simulate a simple thermoelectric system of:

cold reservoir <== cold node <==> thermoelectric module <==> hot node <==> hot reservoir

We use the class ThermoelectricParameters to represent this.

We also have the functions
1. `peltier_heat`: returns the Peltier heating effect, = S x I x T, Seebeck coeffiecient times current times temperature
2. `joule_heating`: returns the Joule heating: $I^2R$, or current squared times resistance 
3. `conductive_heat_leak`: returns heat that 'leaks' or diffuses from the hot side to the colds side = $K (T_h - T_c)$ or 
thermal conductivity times the difference in temperatures between the hot side and cold side
4. `cold_side_heat`: returns the heat removed from the cold side $Q_c$ which is $Peltier\ heat - \frac{1}{2} Joule\ heating - conductive\ heat\ leak$
5. `hot_side_heat`: returns heat added to hot side, which is $Peltier\ heat + \frac{1}{2} Joule\ heating - conductive\ heat\ leak$
6. `voltage`: returns voltage, which is applied voltage plus Seebeck voltage, $Seebeck \ coefficient *(T_h - T_c) + IR$
7. `electrical_power` returns power produced by system, $P = IV$
8. `coefficient_of_performance`: cooling efficiency = $\frac{Q_c}{IV} = \frac{Q_c}{P}$

Now, what does the transient.py script do?
1. `TwoNodeThermalParameters` class: creates an object with four attributes, thermal capacitance ($C$) and reservoir conductance ($G$) for both the hot and cold sides
2. `two_node_rhs`: function that does the majority of the work. This is solving for the temperature changes of both sides