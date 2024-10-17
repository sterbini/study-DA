"""This is a template script for generation 1 of simulation study, in which ones generates a
particle distribution and a collider from a MAD-X model."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import contextlib
import logging
import os
import time

# Import third-party modules
import numpy as np
import pandas as pd
import xtrack as xt

# Import user-defined modules
from study_da.generate import XsuiteCollider, XsuiteTracking
from study_da.utils import (
    load_dic_from_path,
    set_item_in_dic,
    write_dic_to_path,
)

# Set up the logger here if needed


# ==================================================================================================
# --- Script functions
# ==================================================================================================


def load_collider(full_configuration):
    collider = XsuiteCollider._load_collider(
        full_configuration["config_simulation"]["path_collider_file_for_tracking_as_input"]
    )
    collider.build_trackers()
    return collider


def track_particles(full_configuration, collider):
    # Get emittances
    n_emitt_x = full_configuration["config_collider"]["config_beambeam"]["nemitt_x"]
    n_emitt_y = full_configuration["config_collider"]["config_beambeam"]["nemitt_y"]
    xst = XsuiteTracking(full_configuration["config_simulation"], n_emitt_x, n_emitt_y)

    # Prepare particle distribution
    particles, particle_id, l_amplitude, l_angle = xst.prepare_particle_distribution_for_tracking(
        collider
    )

    # Track
    particles_dict = xst.track(collider, particles)

    # Convert particles to dataframe
    particles_df = pd.DataFrame(particles_dict)

    # ! Very important, otherwise the particles will be mixed in each subset
    # Sort by parent_particle_id
    particles_df = particles_df.sort_values("parent_particle_id")

    # Assign the old id to the sorted dataframe
    particles_df["particle_id"] = particle_id

    # Register the amplitude and angle in the dataframe
    particles_df["normalized amplitude in xy-plane"] = l_amplitude
    particles_df["angle in xy-plane [deg]"] = l_angle * 180 / np.pi

    # Add some metadata to the output for better interpretability
    particles_df.attrs["configuration"] = full_configuration
    particles_df.attrs["date"] = time.strftime("%Y-%m-%d %H:%M:%S")

    # Save output
    particles_df.to_parquet(
        full_configuration["config_simulation"]["path_distribution_file_output"]
    )


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
        set_item_in_dic(full_configuration, key, value)

    # Configure collider
    collider = load_collider(full_configuration)

    # Drop updated configuration
    name_configuration = os.path.basename(path_configuration)
    write_dic_to_path(full_configuration, name_configuration, ryaml)

    # Track particles and save to disk
    track_particles(full_configuration, collider)

    logging.info("Script finished")
