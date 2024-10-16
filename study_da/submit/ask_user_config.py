"""
This module contains functions to prompt the user for various job configuration settings.

Functions:
    ask_and_set_context(dic_gen: dict[str, Any]) -> None:

    ask_and_set_htc_flavour(dic_gen: dict[str, Any]) -> None:

    ask_and_set_run_on(dic_gen: dict[str, Any]) -> None:

    ask_keep_setting(job_name: str) -> bool:

    ask_skip_configured_jobs() -> bool:
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
from typing import Any


# ==================================================================================================
# --- Functions
# ==================================================================================================
def ask_and_set_context(dic_gen: dict[str, Any]) -> None:
    """
    Prompts the user to select a context for the job and sets it in the provided dictionary.

    Args:
        dic_gen (dict[str, Any]): The dictionary containing job configuration.
    """
    while True:
        try:
            context = input(
                f"What type of context do you want to use for job {dic_gen['file']}?"
                " 1: cpu, 2: cupy, 3: opencl. Default is cpu."
            )
            context = 1 if context == "" else int(context)
            if context in range(1, 4):
                break
            else:
                raise ValueError
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 3.")

    dict_context = {
        1: "cpu",
        2: "cupy",
        3: "opencl",
    }
    dic_gen["context"] = dict_context[context]


def ask_and_set_htc_flavour(dic_gen: dict[str, Any]) -> None:
    """
    Prompts the user to select an HTCondor job flavor and sets it in the provided dictionary.

    Args:
        dic_gen (dict[str, Any]): The dictionary containing job configuration.
    """
    while True:
        try:
            submission_type = input(
                f"What type of htc job flavour do you want to use for job {dic_gen['file']}?"
                f" 1: espresso, 2: microcentury, 3: longlunch, 4: workday, 5: tomorrow,"
                f" 6: testmatch, 7: nextweek. Default is espresso."
            )
            submission_type = 1 if submission_type == "" else int(submission_type)
            if submission_type in range(1, 8):
                break
            else:
                raise ValueError
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 7.")

    dict_flavour_type = {
        1: "espresso",
        2: "microcentury",
        3: "longlunch",
        4: "workday",
        5: "tomorrow",
        6: "testmatch",
        7: "nextweek",
    }
    dic_gen["htc_flavor"] = dict_flavour_type[submission_type]


def ask_and_set_run_on(dic_gen: dict[str, Any]) -> None:
    """
    Prompts the user to select a submission type and sets it in the provided dictionary.

    Args:
        dic_gen (dict[str, Any]): The dictionary containing job configuration.
    """
    while True:
        try:
            submission_type = input(
                f"What type of submission do you want to use for job {dic_gen['file']}?"
                " 1: local, 2: htc, 3: htc_docker, 4: slurm, 5: slurm_docker. Default is local."
            )
            submission_type = 1 if submission_type == "" else int(submission_type)
            if submission_type in range(1, 6):
                break
            else:
                raise ValueError
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 5.")

    dict_submission_type = {
        1: "local",
        2: "htc",
        3: "htc_docker",
        4: "slurm",
        5: "slurm_docker",
    }
    dic_gen["submission_type"] = dict_submission_type[submission_type]


def ask_keep_setting(job_name: str) -> bool:
    """
    Prompts the user to decide whether to keep the same settings for identical jobs.

    Returns:
        bool: True if the user wants to keep the same settings, False otherwise.
    """
    keep_setting = input(
        f"Do you want to keep the same setting for all jobs of the type {job_name} ? (y/n)."
        f"Default is y."
    )
    while keep_setting not in ["", "y", "n"]:
        keep_setting = input("Invalid input. Please enter y, n or skip question.")
    if keep_setting == "":
        keep_setting = "y"
    return keep_setting == "y"


def ask_skip_configured_jobs() -> bool:
    """
    Prompts the user to decide whether to skip already configured jobs.

    Returns:
        bool: True if the user wants to skip already configured jobs, False otherwise.
    """
    skip_configured_jobs = input(
        "Some jobs to submit seem to be configured already. Do you want to skip them? (y/n). "
        "Default is y."
    )
    while skip_configured_jobs not in ["", "y", "n"]:
        skip_configured_jobs = input("Invalid input. Please enter y, n or skip question.")
    if skip_configured_jobs == "":
        skip_configured_jobs = "y"
    return skip_configured_jobs == "y"
