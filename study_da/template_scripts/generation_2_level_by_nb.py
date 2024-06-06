"""This is a template script for generation 1 of simulation study, in which ones generates a
particle distribution and a collider from a MAD-X model."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import contextlib
import logging
import os

# Import third-party modules
import pandas as pd
import xtrack as xt

# Import user-defined modules
from study_da import (
    XsuiteCollider,
    XsuiteTracking,
    load_configuration_from_path,
    set_item_in_dict,
    write_configuration_to_path,
)


# ==================================================================================================
# --- Script functions
# ==================================================================================================
def configure_collider(full_configuration):
    # Get configuration
    config_collider = full_configuration["config_collider"]
    ver_hllhc_optics = full_configuration["config_mad"]["ver_hllhc_optics"]
    ver_lhc_run = full_configuration["config_mad"]["ver_lhc_run"]
    ions = full_configuration["config_mad"]["ions"]
    collider_filepath = full_configuration["config_simulation"]["collider_file"]

    # Rebuild collider
    collider = xt.Multiline.from_json(collider_filepath)

    # Build object for configuring collider
    xc = XsuiteCollider(config_collider, ver_hllhc_optics, ver_lhc_run, ions)

    # Install beam-beam
    xc.install_beam_beam_wrapper(collider)

    # Build trackers
    # For now, start with CPU tracker due to a bug with Xsuite
    # Refer to issue https://github.com/xsuite/xsuite/issues/450
    collider.build_trackers()  # (_context=context)

    # Set knobs
    xc.set_knobs(collider)

    # Match tune and chromaticity
    xc.match_tune_and_chroma(collider, match_linear_coupling_to_zero=True)

    # Set filling scheme
    xc.set_filling_and_bunch_tracked(ask_worst_bunch=False)

    # Compute the number of collisions in the different IPs
    n_collisions_ip1_and_5, n_collisions_ip2, n_collisions_ip8 = xc.compute_collision_from_scheme()

    # Do the leveling if requested
    if "config_lumi_leveling" in config_collider and not config_collider["skip_leveling"]:
        xc.level_ip1_5_by_bunch_intensity(collider, n_collisions_ip1_and_5)
        xc.level_ip2_8_by_separation(n_collisions_ip2, n_collisions_ip8, collider)
    else:
        logging.warning(
            "No leveling is done as no configuration has been provided, or skip_leveling"
            " is set to True."
        )

    # Add linear coupling
    xc.add_linear_coupling(collider)

    # Rematch tune and chromaticity
    xc.match_tune_and_chroma(collider, match_linear_coupling_to_zero=False)

    # Assert that tune, chromaticity and linear coupling are correct one last time
    xc.assert_tune_chroma_coupling(collider)

    # Configure beam-beam if needed
    if not xc.config_beambeam["skip_beambeam"]:
        xc.configure_beam_beam(collider)

    # Update configuration with luminosity now that bb is known
    l_n_collisions = [
        n_collisions_ip1_and_5,
        n_collisions_ip2,
        n_collisions_ip1_and_5,
        n_collisions_ip8,
    ]
    xc.record_final_luminosity(collider, l_n_collisions)

    # Save collider to json
    xc.write_collider_to_disk(collider, full_configuration)

    return collider


def track_particles(full_configuration, collider):
    # Get emittances
    n_emitt_x = full_configuration["config_collider"]["config_beambeam"]["nemitt_x"]
    n_emitt_y = full_configuration["config_collider"]["config_beambeam"]["nemitt_y"]
    xst = XsuiteTracking(full_configuration["config_simulation"], n_emitt_x, n_emitt_y)

    # Prepare particle distribution
    particles, particle_id = xst.prepare_particle_distribution_for_tracking(collider)

    # Track
    particles_dict = xst.track(collider, particles)

    # Convert particles to dataframe
    particles_df = pd.DataFrame(particles_dict)

    # ! Very important, otherwise the particles will be mixed in each subset
    # Sort by parent_particle_id
    particles_df = particles_df.sort_values("parent_particle_id")

    # Assign the old id to the sorted dataframe
    particles_df["particle_id"] = particle_id

    # Save output
    particles_df.to_parquet(full_configuration["config_simulation"]["path_output_particles"])


def clean():
    # Remote the correction folder, and potential C files remaining
    with contextlib.suppress(Exception):
        os.system("rm -rf correction")
        os.system("rm -f *.cc")


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
    full_configuration, ryaml = load_configuration_from_path(path_configuration)

    # Mutate parameters in configuration
    for key, value in dict_mutated_parameters.items():
        set_item_in_dict(full_configuration, key, value)

    # Configure collider
    collider = configure_collider(full_configuration)

    # Drop updated configuration
    write_configuration_to_path(full_configuration, path_configuration.split("/")[-1], ryaml)

    # Track particles and save to disk
    track_particles(full_configuration, collider)

    # Clean temporary files
    clean()

    logging.info("Script finished")
