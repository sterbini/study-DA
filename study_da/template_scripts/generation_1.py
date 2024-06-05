"""This is a template script for generation 1 of simulation study, in which ones generates a
particle distribution and a collider from a MAD-X model."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging

# Import third-party modules
# Import user-defined modules
from study_da import MadCollider, ParticlesDistribution, load_configuration_from_path


# ==================================================================================================
# --- Script functions
# ==================================================================================================
def build_distribution(config_particles):
    # Build object for generating particle distribution
    distr = ParticlesDistribution(config_particles)

    # Build particle distribution
    particle_list = distr.return_distribution_as_list()

    # Write particle distribution to file
    distr.write_particle_distribution_to_disk(particle_list)


def build_collider(config_mad):
    # Build object for generating collider from mad
    mc = MadCollider(config_mad)

    # Build mad model
    mad_b1b2, mad_b4 = mc.prepare_mad_collider()

    # Build collider from mad model
    collider = mc.build_collider(mad_b1b2, mad_b4)

    # Twiss to ensure eveyrthing is ok
    mc.activate_RF_and_twiss(collider)

    # Clean temporary files
    mc.clean_temporary_files()

    # Save collider to json
    mc.write_collider_to_disk(collider)


# ==================================================================================================
# --- Parameters definition
# ==================================================================================================
config_filepath = "config.yaml"


# ==================================================================================================
# --- Script for execution
# ==================================================================================================

if __name__ == "__main__":
    logging.info("Starting script to build particle distribution and collider")

    # Load full configuration
    full_configuration, ryaml = load_configuration_from_path(config_filepath)

    # Build and save particle distribution
    build_distribution(full_configuration["config_particles"])

    # Build and save collider
    build_collider(full_configuration["config_mad"])

    logging.info("Script finished")
