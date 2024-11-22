# Customizing internal code

It can sometimes be needed to customize the code of study-DA to implement a feature that is not natively present. For instance, implementing a new way of doing the luminosity levelling, or even adding some custom checks when building the collider from a MAD-X model.

Note that this goes a bit beyond customizing the template scripts, since, in this case, we would like to change the internal code of the tool (although we can do this using only the template scripts, see below).

## Scan configuration

We will use an extremely simple scan configuration, with only one generation. Indeed, this tutorial is not about doing a scan or even configure a collider, but simply to illustrate how to modify the template scripts. You should be able to easily adapt this example to a multi-generational scan.

```yaml title="config_scan.yaml"
# ==================================================================================================
# --- Structure of the study ---
# ==================================================================================================
name: example_custom_ost

# List all useful files that will be used by executable in generations below
# These files are placed at the root of the study
dependencies:
  main_configuration: config_hllhc16.yaml
  custom_ost: custom_files/custom_ost.py

structure:
  # First generation is always at the root of the study
  # such that config_hllhc16.yaml is accessible as ../config_hllhc16.yaml
  generation_1:
    executable: custom_files/generation_1.py
```

What you can already note here is that:

- we use a custom script for the first generation, `custom_files/generation_1.py`. We will show later the modifications brought to this script (with respect to the default), to use custom code.
- we added a dependency as a custom modules for the OST (optics specific tools), `custom_files/custom_ost.py`. Indeed, we assume that the internal code to modify is the OST.

## Study configuration

The configuration is the [template one](../../template_files/configurations/config_hllhc16.md) for HL-LHC v1.6.

## Template script

This is where the interesting changes are being made.

```python title="generation_1.py"
"""This is a template script for generation 1 of simulation study, in which ones generates a
particle distribution and a collider from a MAD-X model."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging
import os
import sys

# Import user-defined modules
from study_da.generate import MadCollider, ParticlesDistribution
from study_da.utils import (
    load_dic_from_path,
    set_item_in_dic,
    write_dic_to_path,
)

# Add path to custom_mad_collider (might need to add ../.., etc. depending on the generation)
sys.path.append("..")
import custom_ost

# Set up the logger here if needed


# ==================================================================================================
# --- Override the MadCollider class
# ==================================================================================================
class MadColliderCustom(MadCollider):
    def __init__(self, configuration: dict):
        super().__init__(configuration)

        self._ost = custom_ost


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
    # Build object for generating collider from custom MadCollider class
    mc = MadColliderCustom(config_mad)

    # Alternatively, you could directly use the MadCollider class and just update the OST
    # mc = MadCollider(config_mad)
    # mc._ost = custom_ost

    # Or even more precise, you could define a function yourself and override it in the default ost
    # ! Note that the number of arguments must be the same as the original function
    # mc = MadCollider(config_mad)
    # mc.ost.check_madx_lattices = lambda a: print("This is a fake check")

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
# --- Parameters placeholders definition
# ==================================================================================================
dict_mutated_parameters = {}  ###---parameters---###
path_configuration = "{}  ###---main_configuration---###"
# In case the placeholders have not been replaced, use default path
if path_configuration.startswith("{}"):
    path_configuration = "config.yaml"

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

If you look at the script, you will see that several possibilities are shown to customize the internal code of the tool.

The most elegant way of proceeding is to inherit from and override the `MadCollider` class. To this end, we first import our custom module, `custom_ost`, and then define a new class, `MadColliderCustom`, that inherits from `MadCollider`. We then override the `_ost` attribute of the `MadCollider` class with our custom module. This is likely the most flexible way of customizing the code, as you can change any method or attribute of the `MadCollider` class, and solve potential paths or dependencies conflicts.

Alternatively, you could directly use the `MadCollider` class and just update the `_ost` attribute. This is shown as a comment in the script. This is less flexible than the first method, but it is easier to implement. If you choose this approach, you can of course comment out the MadColliderCustom class.

In both of these cases, you just have to modify the initial ```optics_specific_tools.py``` (that you can find, for instance, on [GitHub](https://github.com/ColasDroin/study-DA/blob/master/study_da/generate/version_specific_files/hllhc16/optics_specific_tools.py)) as you please, and put it in the `custom_files` folder.

Finally, you could define a function yourself and override it in the default ost. This is also shown in as commented lines. This is a more surgical way of customizing the code, but note that the new function you define must have a behaviour similar to the original one (same number of arguments, same return type, etc.). If you choose this approach, you don't even have to define a custom OST file.

!!! warning "Changes must be consistent with the original code"
    Be careful when customizing the internal code of the tool. If you change the behaviour of the code, you might break the study. Make sure that the changes you make are consistent with the original code.

!!! note "For extensive changes, just fork the repository and modify the internal code"
    If you need to make extensive changes to the internal code, it is probably simpler to fork the repository and modify the classes/methods you need. This might help you avoiding path or import conflicts.

## Study generation

In this case, generation is done as usual, with, for instance, the following script:

```python title="generate.py"
# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import os

# Import third-party modules
# Import user-defined modules
from study_da import create, submit
from study_da.utils import load_template_configuration_as_dic, write_dic_to_path

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================

# Generate the study in the local directory
path_tree, name_main_config = create(path_config_scan="config_scan.yaml", force_overwrite=False)

# ==================================================================================================
# --- Script to submit the study
# ==================================================================================================

# In case gen_1 is submitted locally
dic_additional_commands_per_gen = {
    # To clean up the folder after the first generation if submitted locally
    1: "rm -rf final_* modules optics_repository optics_toolkit tools tracking_tools temp mad_collider.log __pycache__ twiss* errors fc* optics_orbit_at* \n"
}

# Submit the study
submit(
    path_tree=path_tree,
    path_python_environment="/afs/cern.ch/work/c/cdroin/private/study-DA/.venv",
    name_config=name_main_config,
    dic_additional_commands_per_gen=dic_additional_commands_per_gen,
)

```

And that's it!
