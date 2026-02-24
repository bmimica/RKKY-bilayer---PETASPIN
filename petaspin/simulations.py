import os
import re
import subprocess
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import stat



class simulation:

    def __init__(self, sim_path):

        self.sim_path = Path(sim_path)

        config_path = self.sim_path / "file_configuration"
        self.global_files = {f.name : f for f in config_path.iterdir() if f.is_file()}
        self._parameters_cache = None

        self.spatial_setup = {f.name : f for f in self.sim_path.iterdir() if f.is_file()}

        output_path = self.sim_path / "output"
        self.output_files = {f.name : f for f in  output_path.iterdir() if f.is_file()}

    
    # copies a folder and creates a new instance of the class:
        # sim2 = create_from_template('path1', 'path2') -> creates the instance sim2 with the files and setup of 'path1' in direction 'path2'
    @classmethod
    def create_from_template(cls, template_path, target_path, overwrite=True):
        template_path = Path(template_path)
        target_path = Path(target_path)

        if target_path.exists() and overwrite:
            def remove_readonly(func, path, excinfo):
                os.chmod(path, stat.S_IWRITE)
                func(path)
            
            shutil.rmtree(target_path, onerror=remove_readonly)
            print(f"Overwriting existing simulation at: {target_path.name}")

        if not target_path.exists():
            shutil.copytree(template_path, target_path)
        
        # Return a NEW instance of the simulation class pointing to the new path
        return cls(target_path)


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

    # output as a function of simulation time
    def output_t(self):
        output_files = self.output_files

        try:
            layx = output_files["output_layx.txt"]
            layy = output_files["output_layy.txt"]
            layz = output_files["output_layz.txt"]
        except KeyError as e:
            print(f'Missing file {e}')

        # THIS IS IMPLEMENTED FOR MULTILAYER STACKING I DONT KNOW HOW LOGIC WORKS FOR COMPLEX GEOMTRIES...
        
        # takes the mean of all columns after the first one
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

        # first element is erased so that the length is the same as dM_dt
        output_t = pd.DataFrame({
            'time': time[1:],
            'M': M[1:],
            'mx_mean': mx_mean[1:],
            'my_mean': my_mean[1:],
            'mz_mean': mz_mean[1:],
            'dM_dt': dM_dt
        })
        return output_t
    
    
    def convergence(self, threshold = 1e-3, plot = False, convergence = False):
        output = self.output()
        time = output['time']
        M = output['M']
        dM_dt = output['dM_dt']

        if plot: 
            fig, ax1 = plt.subplots(figsize=(10, 6))

            ax1.plot(time*1e9, M, label='mx', alpha=0.7)
            ax1.set_xlabel('Time (ns)')
            ax1.set_ylabel('m - normalized magnetization', color='black')

            # Right Axis: The Derivative (dM/dt)
            ax2 = ax1.twinx() 
            # We often use a log scale because dM/dt drops exponentially as it converges
            ax2.semilogy(time*1e9, np.abs(dM_dt), label='|dm/dt|', color='red', linestyle='--')

            th = np.array([threshold for i in range(len(time))])
            ax2.semilogy(time*1e9, np.abs(dM_dt), label='|dm/dt|', color='red', linestyle='--')
            ax2.semilogy(time*1e9, th, label='threshold', color='orange', linestyle='-', alpha = 0.5)
            ax2.set_ylabel('|dm/dt| (1/s) - normalized m derivative', color='red')

            plt.title("Stability")
            plt.show()

        # check if the mean of last elements are less than threshold
        s = np.mean(np.abs(dM_dt[-10:]))
        if s < threshold:
            convergence = True
        return convergence



    