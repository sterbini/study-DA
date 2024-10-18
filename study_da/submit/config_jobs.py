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

# Local imports
from .ask_user_config import (
    ask_and_set_context,
    ask_and_set_htc_flavour,
    ask_and_set_run_on,
    ask_keep_setting,
    ask_skip_configured_jobs,
)


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

        # Variables to store the jobs and their configuration
        self.dic_all_jobs: dict[str, Any] = {}

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
        self.skip_configured_jobs = None
        self._log_and_find("Finding and configuring jobs in the tree", False)
        return self.dic_tree

    def find_all_jobs(self) -> dict:
        """
        Finds all jobs in the tree.

        Returns:
            dict: A dictionary containing all jobs and their details.
        """
        if not self.all_jobs_found:
            self._log_and_find("Finding all jobs in the tree", True)
        else:
            logging.info("All jobs have already been found. Returning the existing dictionary.")

        return self.dic_all_jobs

    def _log_and_find(self, log_str, find_only):
        logging.info(log_str)
        self._find_and_configure_jobs_recursion(self.dic_tree, depth=-1, find_only=find_only)
        self.all_jobs_found = True
