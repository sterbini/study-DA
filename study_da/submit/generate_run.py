"""
This module provides functions to generate run files for jobs in different environments
(local/Slurm and HTCondor). It includes functions to create shell script snippets for tagging
jobs as finished and generating run files with appropriate configurations.

Functions:
    tag_str(abs_job_folder: str) -> str:

    generate_run_file(abs_job_folder: str, job_name: str, setup_env_script: str,
        generation_number: int, tree_path: str, l_keys: list[str], htc: bool = False,
        additionnal_command: str = "", l_dependencies: list[str] | None = None,
        name_config: str = "config.yaml") -> str:

    _generate_run_file(job_folder: str, job_name: str, setup_env_script: str, tree_path: str,
        l_keys: list[str], additionnal_command: str = "") -> str:

    _generate_run_file_htc(job_folder: str, job_name: str, setup_env_script: str,
        generation_number: int, tree_path: str, l_keys: list[str], additionnal_command: str = "",
        l_dependencies: list[str] | None = None, name_config: str = "config.yaml") -> str:

"""

# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import os
from typing import Any

# Third party imports
import yaml

# Local imports
from study_da.utils import find_item_in_dic


# ==================================================================================================
# --- Functions
# ==================================================================================================
def tag_str(abs_job_folder: str) -> str:
    """ "
    Generates a shell script snippet to tag a job as finished if it was successful.
    Args:
        abs_job_folder (str): The (absolute) folder where the job is located.
    Returns:
        str: A formatted string containing the shell script snippet.
    """
    return f"""
# Ensure job run was successful and tag as finished, or as failed otherwise
if [ $? -eq 0 ]; then
    touch {abs_job_folder}/.finished
else
    touch {abs_job_folder}/.failed
fi\n
"""


def generate_run_file(
    abs_job_folder: str,
    job_name: str,
    setup_env_script: str,
    htc: bool = False,
    additionnal_command: str = "",
    **kwargs_htc_run_files: Any,
) -> str:
    """
    Generates a run file for a job, either for local/Slurm or HTC environments.

    Args:
        abs_job_folder (str): The (absolute) folder where the job is located.
        job_name (str): The name of the job script.
        setup_env_script (str): The script to set up the environment.
        htc (bool, optional): Whether the job shoud be run on HTCondor. Defaults to False.
        additionnal_command (str, optional): Additional command to run. Defaults to "".
        **kwargs_htc_run_files (Any): Additional keyword arguments for the generate_run_files method
                when submitting HTC jobs.

    Returns:
        str: The generated run file content.
    """
    if not htc:
        return _generate_run_file(
            abs_job_folder,
            job_name,
            setup_env_script,
            additionnal_command,
        )
    if kwargs_htc_run_files["l_dependencies"] is None:
        kwargs_htc_run_files["l_dependencies"] = []
    return _generate_run_file_htc(
        abs_job_folder,
        job_name,
        setup_env_script,
        additionnal_command,
        **kwargs_htc_run_files,
    )


def _generate_run_file(
    job_folder: str,
    job_name: str,
    setup_env_script: str,
    additionnal_command: str = "",
) -> str:
    """
    Generates a run file for local or Slurm environments.

    Args:
        job_folder (str): The folder where the job is located.
        job_name (str): The name of the job script.
        setup_env_script (str): The script to set up the environment.
        additionnal_command (str, optional): Additional command to run. Defaults to "".

    Returns:
        str: The generated run file content.
    """
    return (
        "#!/bin/bash\n"
        f"# Load the environment\n"
        f"source {setup_env_script}\n\n"
        f"# Move into the job folder\n"
        f"cd {job_folder}\n\n"
        f"# Run the job and tag\n"
        f"python {job_name} > output_python.txt 2> error_python.txt\n"
        f"{tag_str(job_folder)}"
        f"# Store abs path as a variable in case it's needed for additional commands\n"
        f"path_job=$(pwd)\n"
        f"# Optional user defined command to run\n"
        f"{additionnal_command}\n"
    )


def _generate_run_file_htc(
    job_folder: str,
    job_name: str,
    setup_env_script: str,
    additionnal_command: str = "",
    l_dependencies: list[str] | None = None,
    name_config: str = "config.yaml",
    copy_back_parquet: bool = True,
    copy_back_yaml: bool = True,
    copy_back_txt: bool = True,
    copy_back_json: bool = False,
    copy_back_zip: bool = False,
    copy_back_all: bool = False,
) -> str:
    """
    Generates a run file for HTC environments. This function also copies back the output files
    (parquet, yaml, txt, json, zip) to the job folder if requested. Note that copying back large
    files can trigger a throttling mechanism in AFS.

    Args:
        job_folder (str): The folder where the job is located.
        job_name (str): The name of the job script.
        setup_env_script (str): The script to set up the environment.
        additionnal_command (str, optional): Additional command to run. Defaults to "".
        l_dependencies (list[str] | None, optional): List of dependencies (only for HTC jobs).
            Defaults to None.
        name_config (str, optional): The name of the configuration file. Defaults to "config.yaml".
        copy_back_parquet (bool, optional): Whether to copy back parquet files. Defaults to True.
        copy_back_yaml (bool, optional): Whether to copy back yaml files. Defaults to True.
        copy_back_txt (bool, optional): Whether to copy back txt files. Defaults to True.
        copy_back_json (bool, optional): Whether to copy back json files. Defaults to False.
        copy_back_zip (bool, optional): Whether to copy back zip files. Defaults to False.
        copy_back_all (bool, optional): Whether to copy back all files. Defaults to False.

    Returns:
        str: The generated run file content.
    """
    if l_dependencies is None:
        l_dependencies = []
    # Get local path and abs path to current gen
    abs_path = job_folder
    local_path = abs_path.split("/")[-1]

    # Ensure that the name config corresponds to the name and not the path
    name_config = os.path.basename(name_config)

    # Mutate all paths in config to be absolute
    with open(f"{abs_path}/../{name_config}", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    # Mutate paths dependencies to be absolute, if they're not already absolute
    dic_to_mutate = {}
    for dependency in l_dependencies:
        # Check if dependency exist, otherwise throw an error
        dependency_value = find_item_in_dic(config, dependency)
        if dependency_value is None:
            raise KeyError("The dependency you want to update doesn't exist or is set to None.")
        if not dependency_value.startswith("/"):
            new_path_dependency = f"{abs_path}/{dependency_value}"
            dic_to_mutate[dependency] = new_path_dependency

    # Prepare strings for sed
    sed_commands = ""
    for dependency in dic_to_mutate:
        dependency_value = find_item_in_dic(config, dependency)
        path_dependency = dependency_value.replace("/", "\/")  # type: ignore
        new_path_dependency = dic_to_mutate[dependency].replace("/", "\/")  # type: ignore
        sed_commands += f'sed -i "s/{path_dependency}/{new_path_dependency}/g" ../{name_config}\n'

    # Prepare the copy back commands
    copy_back_commands = "cp -f"
    if copy_back_parquet:
        copy_back_commands += " *.parquet"
    if copy_back_yaml:
        copy_back_commands += " *.yaml"
    if copy_back_txt:
        copy_back_commands += " *.txt"
    if copy_back_json:
        copy_back_commands += " *.json"
    if copy_back_zip:
        copy_back_commands += " *.zip"
    if copy_back_all:
        copy_back_commands += " *"
    if copy_back_commands == "cp -f":
        copy_back_commands = ""
    else:
        copy_back_commands += f" {abs_path}\n"

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
        f"# Run the job and tag\n"
        f"python {abs_path}/{job_name} > output_python.txt 2> error_python.txt\n\n"
        f"{tag_str(job_folder)}"
        f"# Delete the config file from the above directory, otherwise it will be copied back and overwrite the new config\n"
        f"rm ../{name_config}\n"
        f"# Copy back output, including the new config\n"
        f"{copy_back_commands}\n"
        f"# Store abs path as a variable in case it's needed for additional commands\n"
        f"path_job={abs_path}\n\n"
        f"# Optional user defined command to run\n"
        f"{additionnal_command}\n"
    )
