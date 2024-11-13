# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import os

# Import third-party modules
# Import user-defined modules
from study_da import create, submit

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================
# Generate the arrays of parameters to scan
l_device_number = []
l_qx = []
l_qy = []
l_qx_for_naming = []
l_qy_for_naming = []
device_number = 0
for qx in [62.310, 62.311]:
    for qy in [60.320, 60.321]:
        # Distribute the simulation over the GPUs, knowing that only 4 GPUs are available
        l_device_number.append(device_number % 4)
        l_qx.append({key: qx for key in ["lhcb1", "lhcb2"]})
        l_qy.append({key: qy for key in ["lhcb1", "lhcb2"]})
        l_qx_for_naming.append(qx)
        l_qy_for_naming.append(qy)
        device_number += 1

# Store the parameters in a dictionary
dic_parameter_all_gen = {
    "generation_2": {
        # "device_number": l_device_number,
        "qx": l_qx,
        "qy": l_qy,
    }
}

dic_parameter_all_gen_naming = {
    "generation_2": {
        # "device_number": l_device_number,
        "qx": l_qx_for_naming,
        "qy": l_qy_for_naming,
    }
}

# Generate the study in the local directory
path_tree, name_main_config = create(
    path_config_scan="config_scan.yaml",
    force_overwrite=False,
    dic_parameter_all_gen=dic_parameter_all_gen,
    dic_parameter_all_gen_naming=dic_parameter_all_gen_naming,
)

# ==================================================================================================
# --- Script to submit the study
# ==================================================================================================

# In case gen_1 is submitted locally
dic_additional_commands_per_gen = {
    # To clean up the folder after the first generation if submitted locally
    1: "rm -rf final_* modules optics_repository optics_toolkit tools tracking_tools temp mad_collider.log __pycache__ twiss* errors fc* optics_orbit_at* \n"
}

# Dependencies for the executable of each generation. Only needed if one uses HTC or Slurm.
dic_dependencies_per_gen = {
    2: ["path_collider_file_for_configuration_as_input", "path_distribution_folder_input"],
}


# Preconfigure submission to HTC
dic_config_jobs = {
    "generation_1" + ".py": {
        # We leave CPU for gen 1 context as it doesn't do tracking
        "gpu": False,
        "submission_type": "local",
    },
    "generation_2" + ".py": {
        # We use GPU for gen 2 context as it does tracking
        # Note that the context is also set in the config file
        "gpu": True,
        "submission_type": "htc_docker",
        "htc_flavor": "tomorrow",
    },
}

# Submit the study
submit(
    path_tree=path_tree,
    path_python_environment="/afs/cern.ch/work/c/cdroin/private/study-DA/.venv",
    path_python_environment_container="/usr/local/DA_study/miniforge_docker",
    path_container_image="/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cdroin/da-study-docker:df1378e8",
    dic_dependencies_per_gen=dic_dependencies_per_gen,
    name_config=name_main_config,
    dic_additional_commands_per_gen=dic_additional_commands_per_gen,
    dic_config_jobs=dic_config_jobs,
)
