# A dummy tracking study

## Introduction

Now that the concepts have been introduced, let's see how to use the package for a dummy tracking study. This will help you understand how the package works and how to use it for an actual collider configuration.

## Creating the study

### Template scripts

The tracking is usually done in two generations to optimize the process. In the first generation, the collider is created from a MAD-X sequence. In the second generation, the tracking is performed. We will use one script per generation, and the same configuration file for both generations (although it will be mutated in the second generation to scan over some parameters).

#### Generation 1

Generation 1 usually corresponds to the step in which the Xsuite collider is created from a MAD-X sequence, and the particle distribution is created. At this step, only a few checks are performed, and the collider is not yet ready for tracking studies. For this example, we will work with the template script provided in the package to create the collider:

```python title="generation_1.py"
"""This is a template script for generation 1 of simulation study, in which ones generates a
particle distribution and a collider from a MAD-X model."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging
import os

# Import third-party modules
# Import user-defined modules
from study_da.generate import MadCollider, ParticlesDistribution
from study_da.utils import (
    load_dic_from_path,
    set_item_in_dic,
    write_dic_to_path,
)

# Set up the logger here if needed


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

    # Twiss to ensure everything is ok
    mc.activate_RF_and_twiss(collider)

    # Clean temporary files
    mc.clean_temporary_files()

    # Save collider to json
    mc.write_collider_to_disk(collider)


# ==================================================================================================
# --- Parameters definition
# ==================================================================================================
dict_mutated_parameters = {{parameters}}
path_configuration = "{{main_configuration}}"

# ==================================================================================================
# --- Script for execution
# ==================================================================================================

if __name__ == "__main__":
    logging.info("Starting script to build particle distribution and collider")

    # Load full configuration
    full_configuration, ryaml = load_dic_from_path(path_configuration)

    # Mutate parameters in configuration
    for key, value in dict_mutated_parameters.items():
        set_item_in_dic(full_configuration, key, value)

    # Dump configuration
    name_configuration = os.path.basename(path_configuration)
    write_dic_to_path(full_configuration, name_configuration, ryaml)

    # Build and save particle distribution
    build_distribution(full_configuration["config_particles"])

    # Build and save collider
    build_collider(full_configuration["config_mad"])

    logging.info("Script finished")
```

This script should very much be self-explanatory, especially if you have understood the concepts explained in the previous sections, and already have a basic knowledge of Mad-X and Xsuite. Basically, it loads the configuration file, mutates it with the parameters provided in the scan configuration (see next section), and then builds the particle distribution and the collider. You are invited to check the details of the functions (e.g. on the [GitHub repository](https://github.com/ColasDroin/study-DA/tree/master/study_da/generate/master_classes) of the package) to better understand what is happening.

The collider configuration file is then saved with the mutated parameters, so that the subsequent generation can use it.

!!! info "These template scripts should be adapted to your needs"

    The template scripts provided in the package are just that: templates. They should be adapted to your needs, especially if you have a more complex collider configuration. For example, you might want to add some checks to ensure that the collider is correctly built, or that the particle distribution is correctly generated. You might also want to add some logging to keep track of what is happening in the script. You're basically free to not use at all the convenience functions provided with the package. You can have the code for the templates in the [Templates](../../template_files/index.md) section, so you can use them as a starting point.

