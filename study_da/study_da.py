# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import logging
from typing import Any, Optional

# Local imports
from .generate.generate_scan import GenerateScan
from .submit.submit_scan import SubmitScan

# ==================================================================================================
# --- Main functions
# ==================================================================================================


def create(
    path_config_scan: str = "config_scan.yaml",
    force_overwrite: bool = False,
    dic_parameter_all_gen: Optional[dict[str, dict[str, Any]]] = None,
    dic_parameter_all_gen_naming: Optional[dict[str, dict[str, Any]]] = None,
) -> tuple[str, str]:
    """
    Create a study based on the configuration file.

    Args:
        path_config_scan (str, optional): Path to the configuration file for the scan.
            Defaults to "config_scan.yaml".
        force_overwrite (bool, optional): Flag to force overwrite the study. Defaults to False.
        dic_parameter_all_gen (Optional[dict[str, dict[str, Any]]], optional): Dictionary of
            parameters for the scan, if not provided through the scan config. Defaults to None.
        dic_parameter_all_gen_naming (Optional[dict[str, dict[str, Any]]], optional): Dictionary of
            parameters for the naming of the scan subfolders, if not provided through the scan
            config. Defaults to None.

    Returns:
        tuple[str, str]: The path to the tree file and the name of the main configuration file.
    """
    logging.info(f"Create study from configuration file: {path_config_scan}")
    study = GenerateScan(path_config=path_config_scan)
    study.create_study(
        force_overwrite=force_overwrite,
        dic_parameter_all_gen=dic_parameter_all_gen,
        dic_parameter_all_gen_naming=dic_parameter_all_gen_naming,
    )

    # Get variables of interest for the submission
    path_tree = study.path_tree
    name_main_configuration = study.config["dependencies"]["main_configuration"]

    return path_tree, name_main_configuration


def create_single_job(
    name_main_configuration: str,
    name_executable_generation_1: str,
    name_executable_generation_2: Optional[str] = None,
    name_executable_generation_3: Optional[str] = None,
    name_study: str = "single_job_study",
    force_overwrite: bool = False,
) -> str:
    """
    Create a single job study (not a parametric scan) with the specified configuration and
    executables. Limited to three generations.

    Args:
        name_main_configuration (str): The name of the main configuration file for the study.
        name_executable_generation_1 (str): The name of the executable for the first generation.
        name_executable_generation_2 (Optional[str], optional): The name of the executable for the
            second generation. Defaults to None.
        name_executable_generation_3 (Optional[str], optional): The name of the executable for the
            third generation. Defaults to None.
        name_study (str, optional): The name of the study. Defaults to "single_job_study".
        force_overwrite (bool, optional): Whether to force overwrite existing files.
            Defaults to False.

    Returns:
        str: The path to the tree file.
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
        force_overwrite=force_overwrite,
    )

    return study.path_tree


def submit(
    path_tree: str,
    path_python_environment: str = "",
    path_python_environment_container: str = "",
    path_container_image: Optional[str] = None,
    force_configure: bool = False,
    dic_config_jobs: Optional[dict[str, dict[str, Any]]] = None,
    one_generation_at_a_time: bool = False,
    keep_submit_until_done: bool = False,
    wait_time: float = 30,
    dic_additional_commands_per_gen: Optional[dict[int, str]] = None,
    dic_dependencies_per_gen: Optional[dict[int, list[str]]] = None,
    dic_copy_back_per_gen: Optional[dict[int, dict[str, bool]]] = None,
    name_config: str = "config.yaml",
) -> None:
    """
    Submits the jobs to the cluster. Note that copying back large files (e.g. json colliders)
    can trigger a throttling mechanism in AFS.

    The following arguments are only used for HTC jobs submission:
    - dic_additional_commands_per_gen
    - dic_dependencies_per_gen
    - dic_copy_back_per_gen
    - name_config

    Args:
        path_tree (str): The path to the tree file.
        path_python_environment (str): The path to the python environment. Default to "".
        path_python_environment_container (str): The path to the python environment in the
            container. Default to "".
        path_container_image (Optional[str], optional): The path to the container image.
            Defaults to None.
        force_configure (bool, optional): Whether to force reconfiguration. Defaults to False.
        dic_config_jobs (Optional[dict[str, dict[str, Any]]], optional): A dictionary containing
            the configuration of the jobs. Defaults to None.
        one_generation_at_a_time (bool, optional): Whether to submit one full generation at a
            time. Defaults to False.
        keep_submit_until_done (bool, optional): Whether to keep submitting jobs until all jobs
            are finished or failed. Defaults to False.
        wait_time (float, optional): The wait time between submissions in minutes. Defaults to 30.
        dic_additional_commands_per_gen (dict[int, str], optional): Additional commands per
            generation. Defaults to None.
        dic_dependencies_per_gen (dict[int, list[str]], optional): Dependencies per generation.
            Only used when doing a HTC submission. Defaults to None.
        dic_copy_back_per_gen (Optional[dict[int, dict[str, bool]]], optional): A dictionary
            containing the files to copy back per generation. Accepted keys are "parquet",
            "yaml", "txt", "json", "zip" and "all". Defaults to None, corresponding to copying
            back only "light" files, i.e. parquet, yaml and txt.
        name_config (str, optional): The name of the configuration file for the study.
            Defaults to "config.yaml".

    Returns:
        None
    """
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
            one_generation_at_a_time=one_generation_at_a_time,
            dic_additional_commands_per_gen=dic_additional_commands_per_gen,
            dic_dependencies_per_gen=dic_dependencies_per_gen,
            dic_copy_back_per_gen=dic_copy_back_per_gen,
            name_config=name_config,
        )
    else:
        study_sub.submit(
            one_generation_at_a_time=one_generation_at_a_time,
            dic_additional_commands_per_gen=dic_additional_commands_per_gen,
            dic_dependencies_per_gen=dic_dependencies_per_gen,
            dic_copy_back_per_gen=dic_copy_back_per_gen,
            name_config=name_config,
        )
