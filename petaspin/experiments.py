from simulations import *

class experiment:
    def __init__(self, initial_sim_path):
        self.initial = simulation(initial_sim_path)
        self.experiment_folder = self.initial.sim_path.parent
  

    def run(self):
        raise NotImplementedError("Each experiment must define its own run logic")

    def show(self):
        if self.data is None:
            print("No data to show. Run the experiment first!")
            return


class hysteresis(experiment):

    def __init__(self, initial_sim_path, field_range):

        super().__init__(initial_sim_path)
        self.initial_sim = Path(initial_sim_path)
        self.field_range = field_range
        self.done = False

    def run(self):

        self.done = True


    def get(self, phi_deg=20, ms_file_name = 'MS_file.dat'):
        if self.done
        ms_file = self.mesh_files[ms_file_name]
        h_m_data = []
        
        for sim in 
        
        with open(ms_file, "r") as f:
                ms = f.readlines()
        
        phi_rad = np.radians(phi_deg)

        # Use r-string for regex to avoid escape sequence issues
        folder_pattern = re.compile(r"sim_Hext([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)")

        for folder in root_path.iterdir():
            if folder.is_dir():
                match = folder_pattern.search(folder.name)
                if match:
                    hext_value = float(match.group(1))
                    m_last_path = folder / "output" / "m_last.txt"
                    
                    if m_last_path.exists():
                        # Efficient reading using numpy if the file is just numbers
                        try:
                            data = np.loadtxt(m_last_path)
                            
                            m_h_vals = []
                            for i, row in enumerate(data):
                                layer_idx = i // num_sites_per_layer
                                ms = ms_array[layer_idx]
                                
                                mx, my, mz = row * ms
                                
                                # Matching your logic: only process non-zero vectors
                                if not np.allclose([mx, my, mz], 0):
                                    mh = mx * np.cos(phi_rad) + my * np.sin(phi_rad)
                                    m_h_vals.append(mh)
                            
                            if m_h_vals:
                                avg_mh = np.mean(m_h_vals)
                                h_m_data.append({"Hext": hext_value, "MH": avg_mh})
                                
                        except Exception as e:
                            print(f"Error processing {m_last_path}: {e}")

        # Return a sorted DataFrame for easy plotting
        df = pd.DataFrame(h_m_data)
        return df.sort_values("Hext").reset_index(drop=True)