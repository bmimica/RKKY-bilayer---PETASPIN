import os

root_dir = r"F:\benja\Bilayer RKKY\t=5nm_hystloop\sim0"

Nx = 50 # x number of sites
Ny = 50 # y number of sites
Nz = 5  # z number of sites

def create_file(file_name, values):
    if len(values) < Nz:
        print(f"Error: Provided {len(values)} Ms values for {Nz} layers.")
        return

    file_path = os.path.join(root_dir, file_name)
    with open(file_path, 'w') as f:
        for z in range(Nz):
            current_ms = values[z]
            num_sites_per_layer = Nx * Ny
            
            # Write the Ms value for every site in this layer
            for _ in range(num_sites_per_layer):
                f.write(f"{current_ms}\n")
    print(f"File created: {file_path} with {Nx*Ny*Nz} lines.")

def create_vector_file(file_name, vectors):
    if len(vectors) < Nz:
        print(f"Error: Need {Nz} vectors, but only got {len(vectors)}.")
        return

    file_path = os.path.join(root_dir, file_name)
    with open(file_path, 'w') as f:
        for z in range(Nz):
            # Select the [Mx, My, Mz] for the current layer
            mx, my, mz = vectors[z]
            num_sites_per_layer = Nx * Ny
            
            # Format the vector string once to save time
            vector_str = f"{mx} {my} {mz}\n"
            
            for _ in range(num_sites_per_layer):
                f.write(vector_str)

    print(f"Vector file created: {file_path}")


create_file("MS_file.dat", [7.4e5, 0, 7.4e5, 7.4e5, 7.4e5])
create_file("shape.dat", [1, 0, 1, 1, 1])

initial_state =  [
    [1,0,0], 
    [0,0,0], 
    [1,0,0], 
    [1,0,0], 
    [1,0,0]
]
create_vector_file("minicial.dat",initial_state)
