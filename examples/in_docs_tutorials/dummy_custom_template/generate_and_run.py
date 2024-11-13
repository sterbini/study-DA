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
path_tree, main_configuration_file = create(
    path_config_scan="config_scan.yaml", force_overwrite=False
)

path_python_environment = "/afs/cern.ch/work/c/cdroin/private/study-DA/.venv"
path_python_environment_container = "/usr/local/DA_study/miniforge_docker"
path_container_image = (
    "/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cdroin/da-study-docker:ad541f20"
)

# Dic copy_back_per_gen (only for HTC)
dic_copy_back_per_gen = {
    2: {"txt": True},
}

# Preconfigure submission to HTC
dic_config_jobs = {
    "generation_1" + ".py": {
        "gpu": False,
        "submission_type": "local",
        "htc_flavor": "espresso",
    },
    "generation_2" + ".py": {
        "gpu": False,
        "submission_type": "htc_docker",
        "htc_flavor": "espresso",
    },
}

# Submit the study
submit(
    path_tree=path_tree,
    name_config=main_configuration_file,
    path_python_environment_container=path_python_environment_container,
    path_container_image=path_container_image,
    dic_copy_back_per_gen=dic_copy_back_per_gen,
    dic_config_jobs=dic_config_jobs,
    keep_submit_until_done=True,
    wait_time=0.1,
)
