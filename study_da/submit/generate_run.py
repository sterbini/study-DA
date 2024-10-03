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
        + f"source {setup_env_script}\n"
        + f"cd {job_folder}\n"
        + f"python {job_name} > output_python.txt 2> error_python.txt\n"
        + tag_str(tree_path, l_keys)
        + additionnal_command
        + "\n"
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
        else:
            if not dependency_value.startswith("/"):
                new_path_dependency = f"{abs_path}/{dependency_value}"
                dic_to_mutate[dependency] = new_path_dependency

    print("dic_to_mutate", dic_to_mutate)

    # Prepare strings for sed
    sed_commands = ""
    for dependency in dic_to_mutate:
        dependency_value = find_item_in_dict(config, dependency)
        path_dependency = dependency_value.replace("/", "\/")
        new_path_dependency = dic_to_mutate[dependency].replace("/", "\/")
        sed_commands += f'sed -i "s/{path_dependency}/{new_path_dependency}/g" {name_config}\n'

    print("sed_commands", sed_commands)

    # Return final run script
    return (
        f"#!/bin/bash\n"
        f"source {setup_env_script}\n"
        # Copy config in (what will be) the level above
        f"cp -f {abs_path}/../{name_config} .\n"
        # Create local directory on node and cd into it
        f"mkdir {local_path}\n"
        f"cd {local_path}\n"
        # Mutate the paths in config to be absolute
        f"{sed_commands}\n"
        # Run the job
        f"python {abs_path}/{job_name} > output_python.txt 2> error_python.txt\n"
        f"{tag_str(tree_path, l_keys)}"
        # Copy back output, including the new config
        f"cp -f *.txt *.parquet *.yaml {abs_path}\n"
        # Optional user defined command to run
        f"{additionnal_command}\n"
    )
