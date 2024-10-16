# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import logging
from typing import Any, Optional

# Local imports
from . import GenerateScan, SubmitScan

# ==================================================================================================
# --- Main functions
# ==================================================================================================


def create(
    path_config: str = "config_scan.yaml",
    tree_file: bool = True,
    force_overwrite: bool = True,
    dic_parameter_all_gen: Optional[dict[str, dict[str, Any]]] = None,
    dic_parameter_all_gen_naming: Optional[dict[str, dict[str, Any]]] = None,
) -> None:
    """
    Create a study based on the configuration file.

    Args:
        path_config (str, optional): Path to the configuration file. Defaults to "config_scan.yaml".
        tree_file (bool, optional): Flag to create the tree file. Defaults to True.
        force_overwrite (bool, optional): Flag to force overwrite the study. Defaults to True.
        dic_parameter_all_gen (Optional[dict[str, dict[str, Any]]], optional): Dictionary of
            parameters for the scan, if not provided through the scan config. Defaults to None.
        dic_parameter_all_gen_naming (Optional[dict[str, dict[str, Any]]], optional): Dictionary of
            parameters for the naming of the scan subfolders, if not provided through the scan
            config. Defaults to None.

    Returns:
        None
    """
    logging.info(f"Create study from configuration file: {path_config}")
    study = GenerateScan(path_config=path_config)
    study.create_study(
        tree_file=tree_file,
        force_overwrite=force_overwrite,
        dic_parameter_all_gen=dic_parameter_all_gen,
        dic_parameter_all_gen_naming=dic_parameter_all_gen_naming,
    )


def create_single_job(
    name_main_configuration: str,
    name_executable_generation_1: str,
    name_executable_generation_2: Optional[str] = None,
    name_executable_generation_3: Optional[str] = None,
    name_study: str = "single_job_study",
    tree_file: bool = True,
    force_overwrite: bool = True,
):
    """
    Create a single job study (not a parametric scan) with the specified configuration and
    executables. Limited to three generations.

    Args:
        name_main_configuration (str): The name of the main configuration file.
        name_executable_generation_1 (str): The name of the executable for the first generation.
        name_executable_generation_2 (Optional[str], optional): The name of the executable for the
            second generation. Defaults to None.
        name_executable_generation_3 (Optional[str], optional): The name of the executable for the
            third generation. Defaults to None.
        name_study (str, optional): The name of the study. Defaults to "single_job_study".
        tree_file (bool, optional): Whether to create a tree file. Defaults to True.
        force_overwrite (bool, optional): Whether to force overwrite existing files.
            Defaults to True.

    Returns:
        None
    """
    # Generate the scan dictionnary
    dic_scan = {
        "name": name_study,
        "dependencies": {"main_configuration": name_main_configuration},
        "structure": {
            "generation_1": {
                "executable": name_executable_generation_1,
            },
        },
    }

    if name_executable_generation_2 is not None:
        dic_scan["structure"]["generation_2"] = {
            "executable": name_executable_generation_2,
        }

    if name_executable_generation_3 is not None:
        dic_scan["structure"]["generation_3"] = {
            "executable": name_executable_generation_3,
        }

    # Create the study
    logging.info(f"Create single job study: {name_study}")
    study = GenerateScan(dic_scan=dic_scan)
    study.create_study(
        tree_file=tree_file,
        force_overwrite=force_overwrite,
    )


def submit(
    path_tree: str,
    path_python_environment: str,
    path_python_environment_container: str = "",
    path_container_image: Optional[str] = None,
    force_configure: bool = False,
    dic_config_jobs: Optional[dict[str, dict[str, Any]]] = None,
    dic_additional_commands_per_gen: Optional[dict[int, str]] = None,
    dic_dependencies_per_gen: Optional[dict[int, list[str]]] = None,
    name_config: str = "config.yaml",
    one_generation_at_a_time: bool = False,
    keep_submit_until_done: bool = False,
    wait_time: float = 30,
):
    # Instantiate the study (does not affect already existing study)
    study_sub = SubmitScan(
        path_tree=path_tree,
        path_python_environment=path_python_environment,
        path_python_environment_container=path_python_environment_container,
        path_container_image=path_container_image,
    )

    # Configure the jobs (will only configure if not already done)
    study_sub.configure_jobs(force_configure=force_configure, dic_config_jobs=dic_config_jobs)

    # Submit the jobs (only submit the jobs that are not already submitted or finished)
    if keep_submit_until_done:
        study_sub.keep_submit_until_done(
            wait_time=wait_time,
            dic_additional_commands_per_gen=dic_additional_commands_per_gen,
            dic_dependencies_per_gen=dic_dependencies_per_gen,
            name_config=name_config,
            one_generation_at_a_time=one_generation_at_a_time,
        )
    else:
        study_sub.submit(
            one_generation_at_a_time=one_generation_at_a_time,
            dic_additional_commands_per_gen=dic_additional_commands_per_gen,
            dic_dependencies_per_gen=dic_dependencies_per_gen,
            name_config=name_config,
        )
