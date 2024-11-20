# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging

# Import third-party modules
# Import user-defined modules
from study_da import create, submit

# Set up the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================

# Generate the study in the local directory
path_tree, name_main_config = create(path_config_scan="config_scan.yaml", force_overwrite=False)

# Define the variables of interest for the submission
path_python_environment = "/afs/cern.ch/work/c/cdroin/private/study-DA/.venv"
path_python_environment_container = "/usr/local/DA_study/miniforge_docker"
path_container_image = (
    "/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cdroin/da-study-docker:757f55da"
)
force_configure = False

# Dependencies for the executable of each generation. Only needed if one uses HTC.
dic_dependencies_per_gen = {
    1: ["acc-models-lhc"],
    2: ["path_collider_file_for_configuration_as_input"],
    3: [
        "path_collider_file_for_tracking_as_input",
        "path_distribution_folder_input",
    ],
}

# Dic copy_back_per_gen (only for HTC)
dic_copy_back_per_gen = {
    1: {"parquet": True, "yaml": True, "txt": True, "json": True, "zip": True},
    2: {"parquet": True, "yaml": True, "txt": True, "json": True, "zip": True},
    3: {"parquet": True, "yaml": True, "txt": True, "json": False, "zip": False},
}

# To bring back the "particles" folder from gen 1
dic_additional_commands_per_gen = {
    1: "cp -r particles $path_job/particles \n",
    2: "",
}


# Preconfigure submission to HTC
dic_config_jobs = {
    "generation_1" + ".py": {
        "request_gpu": False,
        "submission_type": "htc",
        "htc_flavor": "microcentury",
    },
    "generation_2" + ".py": {
        "request_gpu": False,
        "submission_type": "htc",
        "htc_flavor": "microcentury",
    },
    "generation_3" + ".py": {
        "request_gpu": False,
        "submission_type": "htc",
        "htc_flavor": "espresso",
    },
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
    dic_copy_back_per_gen=dic_copy_back_per_gen,
    dic_additional_commands_per_gen=dic_additional_commands_per_gen,
    keep_submit_until_done=True,
    wait_time=15,
)
