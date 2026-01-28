import os
import shutil
import stat
import subprocess

# directory where simulations are
root_dir = r"F:\benja\Bilayer RKKY\Simulations\t1=5nm_t2=15nm_hystloop"

# solves permission error when deleting folders
def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

# modifies a parameter in a .dat file
def modify_file(sim_path, dat_file, target_param, new_value):
    import re

    dat_file_path = os.path.join(sim_path, "file_configuration", dat_file)
    if not os.path.exists(dat_file_path):
        print(f"File {dat_file} does not exist in {sim_path}")
        return
    
    with open(dat_file_path, "r") as file:
        lines = file.readlines()

    modified = False 
    # Read and modify the file
    with open(dat_file_path, "w") as file:
        for line in lines:
            if target_param in line:
                # Replace the first number in the line with new_value
                new_line = re.sub(r"^\s*[\d.+-eE]+", f"{new_value:.2e}", line)
                file.write(new_line)
                modified = True
                print(f"Updated line in file {dat_file}: {new_line.strip()}")
            else:
                file.write(line)

    if not modified:
        print(f"Parameter '{target_param}' not found in {dat_file}")


def run_hyst(original_sim, target_param, h_vals, param_dat_file, identifier = "H="):
    # an example simulation to be copied
    
    prev_sim = os.path.join(root_dir, original_sim)
    simulations_list = []

    # parameters to be changed in the simulations
    for new_parameter in h_vals:
        new_sim = "sim_" + identifier + f"{new_parameter:.1e}"
        new_sim_path = os.path.join(root_dir, new_sim)
        simulations_list.append(new_sim_path)

        # change minitial -> 

        if os.path.exists(new_sim_path):
            shutil.rmtree(new_sim_path, onerror=remove_readonly) # deletes existing folder to avoid conflicts
            print(f"Simulation overwritten : '{new_sim}'")
        else:
            print(f"Simulation created : '{new_sim}'")

        shutil.copytree(prev_sim, new_sim_path)
        modify_file(new_sim_path, param_dat_file, target_param, float(new_parameter))

        # the following code modifies minicial
        minicial_path = os.path.join(new_sim_path, "minicial.dat")
        m_last_path = os.path.join(prev_sim, "output", "m_last.txt")

        if os.path.exists(m_last_path):
            # Read from the original source
            with open(m_last_path, 'r') as f:
                content = f.read()
            
            # 3. Create the new file in the NEW directory with the space modification
            # This effectively "copies and modifies" in one step without touching the original
            updated_content = content.replace(',', ' ')
            
            with open(minicial_path, 'w') as f:
                f.write(updated_content)
            
            print(f"Successfully transferred and formatted state from {prev_sim}")
        else:
            print(f"Warning: Could not find previous state at {minicial_path}")

        exe_path = os.path.join(new_sim_path, "codePetaspin.exe")
        subprocess.run([exe_path], cwd=new_sim_path)

        prev_sim = os.path.join(root_dir, new_sim)

    

# example 
'''
sim_test = "example_parameter"
param_modified = "A(J/m) exchange constant"
parameter_list = [1e-11, 2e-11]
param_dat_file = "ferromagnet.dat"
identifier = "A"

run_simulations(sim_test, param_modified, parameter_list, param_dat_file, identifier = identifier)
'''