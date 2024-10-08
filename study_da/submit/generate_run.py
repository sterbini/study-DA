"""This module contains functions to generate the run file for a job."""

# ==================================================================================================
# --- Imports
# ==================================================================================================
# Third party imports
import yaml

# Local imports
from study_da.utils import find_item_in_dict


# ==================================================================================================
# --- Functions
# ==================================================================================================
def tag_str(tree_path, l_keys):
    # Tag the job as finished with all keys from l_keys
    return f"""
# Ensure job run was successful and tag as finished
if [ $? -eq 0 ]; then
    python -m study_da.submit.scripts.log_finish {tree_path} {' '.join(l_keys)}
fi\n
"""


def generate_run_file(
    job_folder,
    job_name,
    setup_env_script,
    generation_number,
    tree_path,
    l_keys,
    htc=False,
    additionnal_command="",
    l_dependencies=[],
    name_config="config.yaml",
):
    if htc:
        file_str = _generate_run_file_htc(
            job_folder,
            job_name,
            setup_env_script,
            generation_number,
            tree_path,
            l_keys,
            additionnal_command,
            l_dependencies,
            name_config,
        )
    else:
        file_str = _generate_run_file(
            job_folder, job_name, setup_env_script, tree_path, l_keys, additionnal_command
        )

    return file_str


def _generate_run_file(
    job_folder, job_name, setup_env_script, tree_path, l_keys, additionnal_command=""
):
    return (
        "#!/bin/bash\n"
        f"# Load the environment\n"
        f"source {setup_env_script}\n\n"
        f"# Move into the job folder and run it\n"
        f"cd {job_folder}\n\n"
        f"python {job_name} > output_python.txt 2> error_python.txt\n"
        # Tag the job
        f"{tag_str(tree_path, l_keys)}"
        f"# Optional user defined command to run\n"
        f"{additionnal_command}\n"
    )


def _generate_run_file_htc(
    job_folder,
    job_name,
    setup_env_script,
    generation_number,
    tree_path,
    l_keys,
    additionnal_command="",
    l_dependencies=[],
    name_config="config.yaml",
):
    # Get local path and abs path to current gen
    abs_path = job_folder
    local_path = abs_path.split("/")[-1]

    # Mutate all paths in config to be absolute
    with open(f"{abs_path}/../{name_config}", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    # Mutate paths to be absolute, if they're not already absolute
    dic_to_mutate = {}
    for dependency in l_dependencies:
        # Check if dependency exist, otherwise throw an error
        dependency_value = find_item_in_dict(config, dependency)
        if dependency_value is None:
            raise KeyError("The dependency you want to update doesn't exist or is set to None.")
        if not dependency_value.startswith("/"):
            new_path_dependency = f"{abs_path}/{dependency_value}"
            dic_to_mutate[dependency] = new_path_dependency

    # Prepare strings for sed
    sed_commands = ""
    for dependency in dic_to_mutate:
        dependency_value = find_item_in_dict(config, dependency)
        path_dependency = dependency_value.replace("/", "\/")
        new_path_dependency = dic_to_mutate[dependency].replace("/", "\/")
        sed_commands += f'sed -i "s/{path_dependency}/{new_path_dependency}/g" ../{name_config}'

    # Return final run script
    return (
        f"#!/bin/bash\n"
        f"# Load the environment\n"
        f"source {setup_env_script}\n\n"
        f"# Copy config in (what will be) the level above\n"
        f"cp -f {abs_path}/../{name_config} .\n\n"
        f"# Create local directory on node and cd into it\n"
        f"mkdir {local_path}\n"
        f"cd {local_path}\n\n"
        f"# Mutate the paths in config to be absolute\n"
        f"{sed_commands}\n\n"
        f"# Run the job\n"
        f"python {abs_path}/{job_name} > output_python.txt 2> error_python.txt\n\n"
        # Tag the job
        f"{tag_str(tree_path, l_keys)}"
        f"# Copy back output, including the new config\n"
        f"cp -f *.txt *.parquet *.yaml {abs_path}\n\n"
        f"# Store abs path as a variable in case it's needed for additional commands\n"
        f"path_job={abs_path}\n\n"
        f"# Optional user defined command to run\n"
        f"{additionnal_command}\n"
    )
