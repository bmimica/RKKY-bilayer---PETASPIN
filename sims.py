import simulation_functions as sim
import numpy as np

sim_test = "sim0"
param_modified = "!field ext (mT)"
parameter_list = np.linspace(-350,350,70)
parameter_list[::-1].sort()
param_dat_file = "input_field.dat"
identifier = "Hext"

sim.run_hyst(sim_test, param_modified, parameter_list, param_dat_file, identifier = identifier)