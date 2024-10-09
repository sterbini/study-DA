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
def tag_str(tree_path: str, l_keys: list[str]) -> str:
    """ "
    Generates a shell script snippet to tag a job as finished if it was successful.
    Args:
        tree_path (str): The path to the tree structure where the job is logged.
        l_keys (list[str]): A list of keys to be included in the log.
    Returns:
        str: A formatted string containing the shell script snippet.
    """
    # Tag the job as finished with all keys from l_keys
    return f"""
# Ensure job run was successful and tag as finished
if [ $? -eq 0 ]; then
    python -m study_da.submit.scripts.log_finish {tree_path} {' '.join(l_keys)}
fi\n
"""


def generate_run_file(
    job_folder: str,
    job_name: str,
    setup_env_script: str,
    generation_number: int,
    tree_path: str,
    l_keys: list[str],
    htc: bool = False,
    additionnal_command: str = "",
    l_dependencies: list[str] | None = None,
    name_config: str = "config.yaml",
) -> str:
    """
    Generates a run file for a job, either for local/Slurm or HTC environments.

    Args:
        job_folder (str): The folder where the job is located.
        job_name (str): The name of the job script.
        setup_env_script (str): The script to set up the environment.
        generation_number (int): The generation number.
        tree_path (str): The path to the tree structure.
        l_keys (list[str]): A list of keys to access the job in the tree.
        htc (bool, optional): Whether the job shoud be run on HTCondor. Defaults to False.
        additionnal_command (str, optional): Additional command to run. Defaults to "".
        l_dependencies (list[str] | None, optional): List of dependencies (only for HTC jobs).
            Defaults to None.
        name_config (str, optional): The name of the configuration file. Defaults to "config.yaml".

    Returns:
        str: The generated run file content.
    """
    if htc:
        if l_dependencies is None:
            l_dependencies = []
        return _generate_run_file_htc(
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
    # Local, or Slurm
    else:
        return _generate_run_file(
            job_folder,
            job_name,
            setup_env_script,
            tree_path,
            l_keys,
            additionnal_command,
        )


def _generate_run_file(
    job_folder: str,
    job_name: str,
    setup_env_script: str,
    tree_path: str,
    l_keys: list[str],
    additionnal_command: str = "",
) -> str:
    """
    Generates a run file for local or Slurm environments.

    Args:
        job_folder (str): The folder where the job is located.
        job_name (str): The name of the job script.
        setup_env_script (str): The script to set up the environment.
        tree_path (str): The path to the tree structure.
        l_keys (list[str]): A list of keys to access the job in the tree.
        additionnal_command (str, optional): Additional command to run. Defaults to "".

    Returns:
        str: The generated run file content.
    """
    return (
        "#!/bin/bash\n"
        f"# Load the environment\n"
        f"source {setup_env_script}\n\n"
        f"# Move into the job folder and run it\n"
        f"cd {job_folder}\n\n"
        f"python {job_name} > output_python.txt 2> error_python.txt\n"
        # Tag the job
        f"{tag_str(tree_path, l_keys)}"
        f"# Store abs path as a variable in case it's needed for additional commands\n"
        f"path_job=$(pwd)\n"
        f"# Optional user defined command to run\n"
        f"{additionnal_command}\n"
    )


def _generate_run_file_htc(
    job_folder: str,
    job_name: str,
    setup_env_script: str,
    generation_number: int,
    tree_path: str,
    l_keys: list[str],
    additionnal_command: str = "",
    l_dependencies: list[str] | None = None,
    name_config: str = "config.yaml",
) -> str:
    """
    Generates a run file for HTC environments.

    Args:
        job_folder (str): The folder where the job is located.
        job_name (str): The name of the job script.
        setup_env_script (str): The script to set up the environment.
        generation_number (int): The generation number.
        tree_path (str): The path to the tree structure.
        l_keys (list[str]): A list of keys to access the job in the tree.
        additionnal_command (str, optional): Additional command to run. Defaults to "".
        l_dependencies (list[str] | None, optional): List of dependencies (only for HTC jobs).
            Defaults to None.
        name_config (str, optional): The name of the configuration file. Defaults to "config.yaml".

    Returns:
        str: The generated run file content.
    """
    if l_dependencies is None:
        l_dependencies = []
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
        path_dependency = dependency_value.replace("/", "\/")  # type: ignore
        new_path_dependency = dic_to_mutate[dependency].replace("/", "\/")  # type: ignore
        sed_commands += f'sed -i "s/{path_dependency}/{new_path_dependency}/g" ../{name_config}\n'

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
        f"{sed_commands}\n"
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
