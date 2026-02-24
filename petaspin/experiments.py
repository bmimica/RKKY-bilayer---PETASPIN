from simulations import *
from pathlib import Path
import numpy as np
import pandas as pd


class experiment:
    def __init__(self, experiment_folder, master_name = 'sim0'):
        self.experiment_folder = experiment_folder 
        self.master_path = Path(self.experiment_folder) / master_name
        self.data = None
  

    def run(self):
        raise NotImplementedError("Each experiment must define its own run logic")

    def show(self):
        if self.data is None:
            print("No data to show. Run the experiment first!")
            return


class hysteresis(experiment):

    def __init__(self, experiment_folder, master, label = 'hyst'):

        super().__init__(experiment_folder, master)

        self.label = label

    def run(self, field_range, require_convergence = False):

        print('hysteresis running over field range :', field_range)
        prev_sim_path =  self.master_path
        for i, field in enumerate(field_range):
            new_sim_name = f"{self.label}_H={field}"
            new_sim_path = Path(self.experiment_folder) / new_sim_name

            # creat new simulation() object and modifies field
            new_sim = simulation.create_from_template(prev_sim_path, new_sim_path)
            new_sim.modify_parameter('input_field.dat', 'field', field)
            
            # replaces the initial state with the previous output
            m_last_path = prev_sim_path / "output" / "m_last.txt"
            minicial_path = new_sim.spatial_setup['minicial.dat']

            if m_last_path.exists():
                # 2. Read, modify, and write in basically two lines
                content = m_last_path.read_text()
                minicial_path.write_text(content.replace(',', ' '))
            else:
                print(f"m_initial setup failed for {new_sim_name}")
                break

            if require_convergence:
                return NotImplementedError(' need to put higher time simulation and create a stopping mechanism ...')

            new_sim.run()
        self.done = True
        

    # gives magnetization as function of field
    def get_H_M(self):
        rows = {}
        H_list, mH_list, dM_dt_list, mx_list, my_list, mz_list = [], [], [], [], [], []
        for sim_path in self.experiment_folder.iterdir():
            if sim_path.is_dir() and sim_path.name.startswith(self.label):
                sim = simulation(sim_path)
                output_t = sim.output_t()

                Hparams = sim.parameters['input_field.dat']
                H = Hparams['field']
                thH = Hparams['H_theta']
                phiH = Hparams['H_phi']

                # takes the last element of each component, that is last time step
                mx = output_t['mx_mean'].iloc[-1]
                my = output_t['my_mean'].iloc[-1]
                mz = output_t['mz_mean'].iloc[-1]
                dM_dt = output_t['dM_dt'].iloc[-1]
                mH = mx*np.sin(thH)*np.cos(phiH) + my*np.sin(thH)*np.sin(phiH) + mz*np.cos(thH)

                rows.append({
                'H': H,
                'mH': mH,
                'mx': mx,
                'my': my,
                'mz': mz,
                'dM_dt': dM_dt
                })

                output_H = pd.DataFrame(rows)

        output_H['H'], output_H['M'], output_H['dM_dt'], output_H['mx'], output_H['my'], output_H['mz'] = H_list, mH_list, dM_dt_list, mx_list, my_list, mz_list
        return output_H