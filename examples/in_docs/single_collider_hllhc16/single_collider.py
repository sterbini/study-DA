# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging
import os

# Import third-party modules
# Import user-defined modules
from study_da import create_single_job, submit
from study_da.utils import (
    load_template_configuration_as_dic,
    write_dic_to_path,
)

# Set up the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================

# Load the configuration from hllhc16
name_template_config = "config_hllhc16.yaml"
config, ryaml = load_template_configuration_as_dic(name_template_config)


# Update the location of acc-models
config["config_mad"]["links"]["acc-models-lhc"] = (
    "../../../../../external_dependencies/acc-models-lhc"
)

# Track for 10 turn just to ensure there's no issue with the collider
config["config_simulation"]["n_turns"] = 10

# Save the collider produced after the configuration step
config["config_collider"]["save_output_collider"] = True

# Drop the configuration locally
local_config_name = "local_config.yaml"
write_dic_to_path(config, local_config_name, ryaml)

# Now generate the study in the local directory
path_tree = create_single_job(
    name_main_configuration=local_config_name,
    name_executable_generation_1="generation_1.py",
    name_executable_generation_2="generation_2_level_by_nb.py",
    name_study="single_job_study_hllhc16",
    force_overwrite=True,
)

# Delete the configuration file (it's copied in the study folder anyway)
os.remove(local_config_name)


# ==================================================================================================
# --- Script to submit the study
# ==================================================================================================

# Define the variables of interest for the submission
path_python_environment = "/afs/cern.ch/work/c/cdroin/private/study-DA/.venv"
force_configure = False

# Preconfigure submission to local
dic_config_jobs = {
    "generation_1" + ".py": {
        "context": "cpu",
        "submission_type": "local",
    },
    "generation_2" + ".py": {
        "context": "cpu",
        "submission_type": "local",
    },
}

# In case gen_1 is submitted locally, add a command to remove unnecessary files
dic_additional_commands_per_gen = {
    1: "rm -rf final_* modules optics_repository optics_toolkit tools tracking_tools temp "
    "mad_collider.log __pycache__ twiss* errors fc* optics_orbit_at* \n",
    2: "",
}

# Submit the study
submit(
    path_tree=path_tree,
    path_python_environment=path_python_environment,
    force_configure=force_configure,
    name_config=local_config_name,
    dic_config_jobs=dic_config_jobs,
    dic_additional_commands_per_gen=dic_additional_commands_per_gen,
    keep_submit_until_done=True,
    wait_time=1,
)
