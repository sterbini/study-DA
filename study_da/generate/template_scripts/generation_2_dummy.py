"""This is a template script for generation 1 of simulation study, in which ones generates a
particle distribution and a collider from a MAD-X model."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging

# Import third-party modules
import numpy as np
import pandas as pd

# Import user-defined modules
from study_da.utils import (
    load_dic_from_path,
    set_item_in_dict,
    write_dic_to_path,
)


# ==================================================================================================
# --- Script functions
# ==================================================================================================
def update_particles_distribution(full_configuration):
    # Get configuration
    folder_particles = full_configuration["config_simulation"]["particle_folder"]
    file_particles = full_configuration["config_simulation"]["particle_file"]
    path_particles = f"{folder_particles}/{file_particles}"

    # Load particle distribution
    particle_df = pd.read_parquet(path_particles)

    r_vect = particle_df["normalized amplitude in xy-plane"].values
    theta_vect = particle_df["angle in xy-plane [deg]"].values * np.pi / 180

    # Add r_vect and theta_vect to dataframe
    particle_df["r_vect"] = r_vect
    particle_df["theta_vect"] = theta_vect

    # Save output
    particle_df.to_parquet(full_configuration["config_simulation"]["path_output_particles"])


# ==================================================================================================
# --- Parameters definition
# ==================================================================================================
dict_mutated_parameters = {{parameters}}
path_configuration = "{{main_configuration}}"

# ==================================================================================================
# --- Script for execution
# ==================================================================================================

if __name__ == "__main__":
    logging.info("Starting script to configure collider and track")

    # Load full configuration
    full_configuration, ryaml = load_dic_from_path(path_configuration)

    # Mutate parameters in configuration
    for key, value in dict_mutated_parameters.items():
        set_item_in_dict(full_configuration, key, value)

    # Update particle distribution
    update_particles_distribution(full_configuration)

    # Drop updated configuration
    write_dic_to_path(full_configuration, path_configuration.split("/")[-1], ryaml)

    logging.info("Script finished")
