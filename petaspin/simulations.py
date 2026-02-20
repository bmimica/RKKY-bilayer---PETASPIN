import os
import re
import subprocess
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt



class simulation:

    def __init__(self, sim_path):

        self.sim_path = Path(sim_path)

        config_path = self.sim_path / "file_configuration"
        self.global_files = {f.name : f for f in config_path.iterdir() if f.is_file()}
        self._parameters_cache = None

        self.spatial_setup = {f.name : f for f in self.sim_path.iterdir() if f.is_file()}

        output_path = self.sim_path / "output"
        self.output_files = {f.name : f for f in  output_path.iterdir() if f.is_file()}

        


    # Setup functions : 

    # saves parameters from a specific dat file into a dictionary
    def get_all_parameters(self, dat_file):
        file_path = self.global_files[dat_file]
        params = {}

        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                # Skip lines that are empty or start with a comment //
                if not line or line.startswith("//"):
                    continue     
                # Reads lines that contain the '!' delimiter
                if "!" in line:
                    # Split line into: [value] ! [name and comments]
                    parts = line.split("!")
                    raw_value = parts[0].strip()
                    name_part = parts[1].strip().split()[0]

                    try:
                        params[name_part] = float(raw_value)
                    except ValueError:
                        # If the left side isn't a number (like a file path), skip it
                        continue
        return params
    
    # Saves the parameters of all dat files into a dictionary
    @property
    def parameters(self):
        # use parameters cache so it doesn't compute everytime
        if self._parameters_cache is None:
            parameters = {} 
            for file_name in self.global_files:
                parameters[file_name] = self.get_all_parameters(file_name)
            self._parameters_cache = parameters
        return self._parameters_cache
    
    # computes time step
    @property
    def timestep(self):
        omega =  self.parameter['geometry.dat']['omega']
        multiply = self.parameter['geometry.dat']['multiply']
        mu0 = 4*np.pi*1e-7 
        gamma = self.parameter['ferromagnet.dat']['gama']
        Ms = self.parameter['ferromagnet.dat']['Ms_const']
        return (omega*multiply)/(mu0*gamma*Ms)

    
    # modifies a parameter in a .dat file
    def modify_parameter(self, dat_file, parameter, new_value):
        setup_files = self.setup_files
        pattern = re.compile(rf"^\s*([\d.+-eE]+)\s+{re.escape(parameter)}")
        with open(setup_files[dat_file], "r") as file:
            lines = file.readlines()
        with open(setup_files[dat_file], "w") as file:
            for line in lines:
                match = pattern.search(line)
                if match:
                    # Replace the first number in the line with new_value
                    new_line = re.sub(r"^\s*[\d.+-eE]+", f"{new_value:.3e}", line)
                    file.write(new_line)
                    print(f"Updated line in file {dat_file}: {new_line.strip()}")
                else:
                    file.write(line)

        # clears the cache so that the parameters are computed again.
        self._parameters_cache = None


    # Execution functions :

    def run(self):
        sim_path = self.sim_path
        exe_path = os.path.join(sim_path, "codePetaspin.exe")
        subprocess.run([exe_path], cwd=sim_path)


    # Output functions :

    def convergence(self, plot = False, return_data = False):
        output_files = self.output_files
        
        try:
            layx = output_files["output_layx.txt"]
            layy = output_files["output_layy.txt"]
            layz = output_files["output_layz.txt"]
        except KeyError as e:
            print(f'Missing file {e}')

        # THIS IS IMPLEMENTED FOR MULTILAYER STACKING I DONT KNOW HOW LOGIC WORKS FOR COMPLEX GEOMTRIES...

        df_x = pd.read_csv(layx, sep='\s+', header=None)
        time = df_x[0]
        mx_mean = df_x.iloc[:, 1:].mean(axis=1)
        df_y = pd.read_csv(layy, sep='\s+', header=None)
        my_mean = df_y.iloc[:, 1:].mean(axis=1)
        df_z = pd.read_csv(layz, sep='\s+', header=None)
        mz_mean = df_z.iloc[:, 1:].mean(axis=1)

        M = np.sqrt(mx_mean**2 + my_mean**2 + mz_mean**2)
        dM = np.diff(M)
        dt = np.diff(time)
        dM_dt = dM/dt

        if not return_data and not plot:
            return
        
        if plot: 
            fig, ax1 = plt.subplots(figsize=(10, 6))

            ax1.plot(time*1e9, M, label='mx', alpha=0.7)
            ax1.set_xlabel('Time (ns)')
            ax1.set_ylabel('m - normalized magnetization', color='black')

            # Right Axis: The Derivative (dM/dt)
            ax2 = ax1.twinx() 
            # We often use a log scale because dM/dt drops exponentially as it converges
            ax2.semilogy(time[1:]*1e9, np.abs(dM_dt), label='|dm/dt|', color='red', linestyle='--')
            ax2.set_ylabel('|dm/dt| (1/s) - normalized m derivative', color='red')

            plt.title("Stability")
            plt.show()

            plt.plot(time, mx_mean, label='mx', alpha=0.7)
            plt.show()

            plt.plot(time, my_mean, label='mx', alpha=0.7)
            plt.show()

            plt.plot(time, mz_mean, label='mx', alpha=0.7)
            plt.show()
        return time, M , dM/dt



    