# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging
import os

# Import third-party modules
# Import user-defined modules
from study_da import create, submit
from study_da.utils import load_template_configuration_as_dic, write_dic_to_path

# Set up the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================
# Load the template configuration
name_template_config = "config_runIII_ions.yaml"
config, ryaml = load_template_configuration_as_dic(name_template_config)

# Update the location of the paths since everything is in the same directory in this scan
config["config_collider"]["path_collider_file_for_configuration_as_input"] = (
    "collider_file_for_configuration.json"
)
config["config_simulation"]["path_collider_file_for_tracking_as_input"] = (
    "collider_file_for_tracking.json"
)

config["config_simulation"]["path_distribution_folder_input"] = "particles"

# Drop the configuration locally
write_dic_to_path(config, name_template_config, ryaml)

# Now generate the study in the local directory
path_tree, name_main_config = create(path_config_scan="config_scan.yaml", force_overwrite=False)

# Delete the configuration
os.remove(name_template_config)


# Define the variables of interest for the submission
path_python_environment = "/afs/cern.ch/work/c/cdroin/private/study-DA/.venv"
path_python_environment_container = "/usr/local/DA_study/miniforge_docker"
path_container_image = (
    "/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cdroin/da-study-docker:df1378e8"
)
force_configure = False

# Dependencies for the executable of each generation. Only needed if one uses HTC.
dic_dependencies_per_gen = {
    1: ["acc-models-lhc"],
}


# Preconfigure submission to HTC
dic_config_jobs = {
    "generation_1" + ".py": {
        "gpu": False,
        "submission_type": "htc_docker",
        "htc_flavor": "testmatch",
    }
}


# Submit the study
submit(
    path_tree=path_tree,
    path_python_environment=path_python_environment,
    path_python_environment_container=path_python_environment_container,
    path_container_image=path_container_image,
    force_configure=force_configure,
    dic_dependencies_per_gen=dic_dependencies_per_gen,
    name_config=name_main_config,
    dic_config_jobs=dic_config_jobs,
)
