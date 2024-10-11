"""
This module contains the ConfigJobs class that allows to configure jobs in the tree file.
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import copy
import logging
from typing import Any, Optional


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


# ==================================================================================================
# --- Class
# ==================================================================================================
class ConfigJobs:
    """
    A class to configure jobs in the tree file.

    Attributes:
        dic_tree (dict): The dictionary representing the job tree.

    Methods:
        _find_and_configure_jobs_recursion(dic_gen, depth=0, l_keys=None, find_only=False):
            Recursively finds and configures jobs.
        find_and_configure_jobs(): Finds and configures all jobs in the tree.
        find_all_jobs(): Finds all jobs in the tree.
    """

    def __init__(self, dic_tree: dict):
        """
        Initializes the ConfigJobs class.

        Args:
            dic_tree (dict): The dictionary representing the job tree.

        """
        self.dic_tree: dict = dic_tree

        # Flag set to True if self.find_all_jobs() has been called at least once
        self.all_jobs_found: bool = False

    def _find_and_configure_jobs_recursion(
        self,
        dic_gen: dict[str, Any],
        depth: int = 0,
        l_keys: list[str] | None = None,
        find_only: bool = False,
    ) -> None:
        """
        Recursively finds and configures jobs in the tree.

        Args:
            dic_gen (dict[str, Any]): The dictionary representing the current level of the job tree.
            depth (int, optional): The current depth in the tree. Defaults to 0.
            l_keys (list[str], optional): The list of keys representing the path in the tree.
                Defaults to None.
            find_only (bool, optional): If True, only finds jobs without configuring them.
                Defaults to False.

        Raises:
            AttributeError: If required attributes are not set before calling this method.
        """
        if l_keys is None:
            l_keys = []

        if not hasattr(self, "dic_all_jobs"):
            raise AttributeError("dic_all_jobs should be set before calling this method")

        # Recursively look for job key in the tree, keeping track of the depth
        # of the job in the tree
        # Browse a list of keys rather than than the keys() generator not to create mutation errors
        for key in list(dic_gen.keys()):
            value = dic_gen[key]
            if isinstance(value, dict):
                self._find_and_configure_jobs_recursion(
                    dic_gen=value, depth=depth + 1, l_keys=l_keys + [key], find_only=find_only
                )
            elif key == "file":
                # Add job the the list of all jobs
                # In theory, the list of keys can be obtained from the job path
                # but it's safer to keep it in the dict
                self.dic_all_jobs[value] = {
                    "gen": depth,
                    "l_keys": copy.copy(l_keys),
                }

                # Stop the browsing if we only want to find the jobs
                if find_only:
                    return

                # Otherwise ensure that the job can be configured
                if not hasattr(self, "dic_config_jobs") or not hasattr(
                    self, "skip_configured_jobs"
                ):
                    raise AttributeError(
                        "dic_config_jobs and skip_configured_jobs should be set before calling"
                        "this method"
                    )

                # Put path_run to None if it exists
                if "path_run" in dic_gen:
                    logging.warning(
                        f"Job {value} has a path_run attribute. It will be set to None."
                    )
                    dic_gen["path_run"] = None

                # If all is fine so far, get job name and configure
                job_name = value.split("/")[-1]

                # Ensure configuration is not already set
                if "submission_type" in dic_gen:
                    if self.skip_configured_jobs is None:
                        self.skip_configured_jobs = ask_skip_configured_jobs()
                    if self.skip_configured_jobs:
                        return

                # If it's the first time we find the job, ask for context and run_on
                # Note that a job can be configured and not be in self.dic_config_jobs
                # self.dic_config_jobs contains the archetypical main jobs (one per gen), not all jobs
                if job_name not in self.dic_config_jobs:
                    self._get_context_and_run_on(depth, value, dic_gen, job_name)
                else:
                    # Check that the config for the current job is ok
                    self.check_config_jobs(job_name)

                    # Merge the configuration of the job with the existing one
                    dic_gen |= self.dic_config_jobs[job_name]

    def check_config_jobs(self, job_name: str) -> None:
        """
        Check the configuration of a job and ensure that it is properly set.
        Useful when the dic_config_jobs is provided externally.

        Args:
            job_name (str): The name of the job to be configured.
            dic_gen (dict[str, str]): The dictionary containing job configuration.

        Returns:
            dict: The updated job configuration.
        """

        # Ensure flavour is set for htc jobs
        if (
            self.dic_config_jobs[job_name]["submission_type"] in ["htc", "htc_docker"]
            and "htc_flavor" not in self.dic_config_jobs[job_name]
        ):
            raise ValueError(
                f"Job {job_name} is not properly configured. Please set the htc_flavor."
            )

        # Set status to to_submit if not already set
        if "status" not in self.dic_config_jobs[job_name]:
            self.dic_config_jobs[job_name]["status"] = "to_submit"

    def _get_context_and_run_on(self, depth: int, value: str, dic_gen: dict, job_name: str) -> None:
        """
        Sets the context and run-on parameters for a job, updates the job configuration,
        and stores it in the job dictionary if the user chooses to keep the settings.

        Args:
            depth (int): The depth level of the job in the hierarchy.
            value (str): The value associated with the job.
            dic_gen (dict): A dictionary containing general job configuration parameters.
            job_name (str): The name of the job to be configured.

        Returns:
            None
        """
        logging.info(f"Found job at depth {depth}: {value}")
        # Set context and run_on
        ask_and_set_context(dic_gen)
        ask_and_set_run_on(dic_gen)
        if dic_gen["submission_type"] in ["htc", "htc_docker"]:
            ask_and_set_htc_flavour(dic_gen)
        else:
            dic_gen["htc_flavor"] = None
        dic_gen["status"] = "to_submit"

        # Compute all jobs to see if there are at least two jobs in the current generation
        self.find_all_jobs()
        # Ensure there are more than one job of the same type to ask the user
        # sourcery skip: merge-nested-ifs
        if [x["gen"] == depth for x in self.dic_all_jobs.values()].count(True) > 1:
            # Ask the user if they want to keep the settings for all jobs of the same type
            if ask_keep_setting(job_name):
                self.dic_config_jobs[job_name] = {
                    "context": dic_gen["context"],
                    "submission_type": dic_gen["submission_type"],
                    "status": dic_gen["status"],
                    "htc_flavor": dic_gen["htc_flavor"],
                }

    def find_and_configure_jobs(
        self, dic_config_jobs: Optional[dict[str, dict[str, Any]]] = None
    ) -> dict:
        """
        Finds and configures all jobs in the tree.

        Args:
            dic_config_jobs (dict[str, dict[str, Any]], optional): A dictionary containing the
                configuration of the jobs. Defaults to None.

        Returns:
            dict: The updated job tree with configurations.
        """
        # Variables to store the jobs and their configuration
        self.dic_config_jobs = dic_config_jobs if dic_config_jobs is not None else {}
        self.dic_all_jobs = {}
        self.skip_configured_jobs = None

        logging.info("Finding and configuring jobs in the tree")
        self._find_and_configure_jobs_recursion(self.dic_tree, depth=-1, find_only=False)

        return self.dic_tree

    def find_all_jobs(self) -> dict:
        """
        Finds all jobs in the tree.

        Returns:
            dict: A dictionary containing all jobs and their details.
        """
        if not self.all_jobs_found:
            # Variables to store the jobs and their configuration
            self.dic_all_jobs = {}

            # Find all jobs and associated generation
            logging.info("Finding all jobs in the tree")
            self._find_and_configure_jobs_recursion(self.dic_tree, depth=-1, find_only=True)

            # Write the jobs as found
            self.all_jobs_found = True
        else:
            logging.info("All jobs have already been found. Returning the existing dictionary.")

        return self.dic_all_jobs
