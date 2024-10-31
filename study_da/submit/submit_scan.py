"""This module contains the SubmitScan class, which is used to submit jobs either locally or
on a cluster."""

# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import logging
import os
import time
from typing import Any, Optional

# Third party imports
from filelock import SoftFileLock

from study_da.utils import load_dic_from_path, write_dic_to_path

# Local imports
from ..utils import nested_get, nested_set
from .cluster_submission import ClusterSubmission
from .config_jobs import ConfigJobs
from .dependency_graph import DependencyGraph
from .generate_run import generate_run_file


# ==================================================================================================
# --- Class
# ==================================================================================================
class SubmitScan:
    def __init__(
        self,
        path_tree: str,
        path_python_environment: str = "",
        path_python_environment_container: str = "",
        path_container_image: Optional[str] = None,
    ) -> None:
        """
        Initializes the SubmitScan class.

        Args:
            path_tree (str): The path to the tree structure.
            path_python_environment (str): The path to the Python environment. Defaults to "".
            path_python_environment_container (str, optional): The path to the Python environment
                in the container. Defaults to "".
            path_container_image (Optional[str], optional): The path to the container image.
                Defaults to None.
        """
        # Path to study files
        self.path_tree = path_tree

        # Absolute path to the tree
        self.abs_path_tree = os.path.abspath(path_tree)

        # Name of the study folder
        self.study_name = os.path.dirname(path_tree)

        # Absolute path to the study folder (get from the path_tree)
        self.abs_path = os.path.abspath(self.study_name).split(f"/{self.study_name}")[0]

        # Container image (Docker or Singularity, if any)
        # Turn to absolute path if it is not already
        if path_container_image is None:
            self.path_container_image = None
        elif not os.path.isabs(path_container_image):
            self.path_container_image = os.path.abspath(path_container_image)
        else:
            self.path_container_image = path_container_image

        # Python environment for the container
        self.path_python_environment_container = path_python_environment_container

        # Ensure that the container image is set if the python environment is set
        if self.path_container_image and not self.path_python_environment_container:
            raise ValueError(
                "The path to the python environment in the container must be set if the container"
                "image is set."
            )

        # Add /bin/activate to the path_python_environment if needed
        if not self.path_python_environment_container.endswith("/bin/activate"):
            self.path_python_environment_container += "/bin/activate"

        # Ensure the path to the python environment is not "" if the container image is not set
        if not self.path_container_image and not path_python_environment:
            raise ValueError(
                "The path to the python environment must be set if the container image is not set."
            )

        # Path to the python environment, activate with `source path_python_environment`
        # Turn to absolute path if it is not already
        if not os.path.isabs(path_python_environment):
            self.path_python_environment = os.path.abspath(path_python_environment)
        else:
            self.path_python_environment = path_python_environment

        # Add /bin/activate to the path_python_environment if needed
        if "bin/activate" not in self.path_python_environment:
            self.path_python_environment += "/bin/activate"

        # Lock file to avoid concurrent access (softlock as several platforms are used)
        self.lock = SoftFileLock(f"{self.path_tree}.lock", timeout=60)

    # dic_tree as a property so that it is reloaded every time it is accessed
    @property
    def dic_tree(self) -> dict:
        """
        Loads the dictionary tree from the path.

        Returns:
            dict: The loaded dictionary tree.
        """
        logging.info(f"Loading tree from {self.path_tree}")
        return load_dic_from_path(self.path_tree)[0]

    # Setter for the dic_tree property
    @dic_tree.setter
    def dic_tree(self, value: dict) -> None:
        """
        Writes the dictionary tree to the path.

        Args:
            value (dict): The dictionary tree to write.
        """
        logging.info(f"Writing tree to {self.path_tree}")
        write_dic_to_path(value, self.path_tree)

    def configure_jobs(
        self,
        force_configure: bool = False,
        dic_config_jobs: Optional[dict[str, dict[str, Any]]] = None,
    ) -> None:
        """
        Configures the jobs by modifying the tree structure and creating the run files for each job.

        Args:
            force_configure (bool, optional): Whether to force reconfiguration. Defaults to False.
            dic_config_jobs (Optional[dict[str, dict[str, Any]]], optional): A dictionary containing
                the configuration of the jobs. Defaults to None.
        """
        # Lock since we are modifying the tree
        logging.info("Acquiring lock to configure jobs")
        with self.lock:
            # Get the tree
            dic_tree = self.dic_tree

            # Ensure jobs have not been configured already
            if ("configured" in dic_tree and dic_tree["configured"]) and not force_configure:
                logging.warning("Jobs have already been configured. Skipping.")
                return

            # Configure the jobs (add generation and job keys, set status to "To finish")
            dic_tree = ConfigJobs(dic_tree).find_and_configure_jobs(dic_config_jobs)

            # Add the python environment, container image and absolute path of the study to the tree
            dic_tree["python_environment"] = self.path_python_environment
            dic_tree["container_image"] = self.path_container_image
            dic_tree["absolute_path"] = self.abs_path
            dic_tree["status"] = "to_finish"
            dic_tree["configured"] = True

            # Explicitly set the dic_tree property to force rewrite
            self.dic_tree = dic_tree

        logging.info("Jobs have been configured. Lock released.")

    def get_all_jobs(self) -> dict:
        """
        Retrieves all jobs from the configuration, without modifying the tree.

        Returns:
            dict: A dictionary containing all jobs.
        """
        # Get a copy of the tree as it's safer
        with self.lock:
            dic_tree = self.dic_tree
        return ConfigJobs(dic_tree).find_all_jobs()

    def generate_run_files(
        self,
        dic_tree: dict[str, Any],
        l_jobs: list[str],
        dic_additional_commands_per_gen: dict[int, str],
        dic_dependencies_per_gen: dict[int, list[str]],
        dic_copy_back_per_gen: dict[int, dict[str, bool]],
        name_config: str,
    ) -> dict:
        """
        Generates run files for the specified jobs.

        Args:
            dic_tree (dict): The dictionary tree structure.
            l_jobs (list[str]): List of jobs to submit.
            dic_additional_commands_per_gen (dict[int, str], optional): Additional commands per
                generation. Defaults to {}.
            dic_dependencies_per_gen (dict[int, list[str]], optional): Dependencies per generation.
                Only used when doing a HTC submission.
            dic_copy_back_per_gen (Optional[dict[int, dict[str, bool]]], optional): A dictionary
                containing the files to copy back per generation. Accepted keys are "parquet",
                "yaml", "txt", "json", "zip" and "all".
            name_config (str, optional): The name of the configuration file for the study.

        Returns:
            dict: The updated dictionary tree structure.
        """

        logging.info("Generating run files for the jobs to submit")
        # Generate the run files for the jobs to submit
        dic_all_jobs = self.get_all_jobs()
        for job in l_jobs:
            l_keys = dic_all_jobs[job]["l_keys"]
            job_name = os.path.basename(job)
            relative_job_folder = os.path.dirname(job)
            absolute_job_folder = f"{self.abs_path}/{relative_job_folder}"
            generation_number = dic_all_jobs[job]["gen"]
            submission_type = nested_get(dic_tree, l_keys + ["submission_type"])
            singularity = "docker" in submission_type
            path_python_environment = (
                self.path_python_environment_container
                if singularity
                else self.path_python_environment
            )

            # Ensure that the run file does not already exist
            if "path_run" in nested_get(dic_tree, l_keys):
                path_run_curr = nested_get(dic_tree, l_keys + ["path_run"])
                if path_run_curr is not None and os.path.exists(path_run_curr):
                    logging.info(f"Run file already exists for job {job}. Skipping.")
                    continue

            # Build l_dependencies and add to the kwargs
            l_dependencies = dic_dependencies_per_gen.get(generation_number, [])

            # Get arguments of current generation
            dic_args = dic_copy_back_per_gen.get(generation_number, {})

            # Mutate the keys
            dic_args = {f"copy_back_{key}": value for key, value in dic_args.items()}

            # Build kwargs for the run file
            kwargs_htc = {
                "l_dependencies": l_dependencies,
                "name_config": name_config,
            } | dic_args

            run_str = generate_run_file(
                absolute_job_folder,
                job_name,
                path_python_environment,
                htc="htc" in submission_type,
                additionnal_command=dic_additional_commands_per_gen.get(generation_number, ""),
                **kwargs_htc,
            )
            # Write the run file
            path_run_job = f"{absolute_job_folder}/run.sh"
            with open(path_run_job, "w") as f:
                f.write(run_str)

            # Record the path to the run file in the tree
            nested_set(dic_tree, l_keys + ["path_run"], path_run_job)

        return dic_tree

    def check_and_update_all_jobs_status(self) -> tuple[dict[str, Any], str]:
        """
        Checks the status of all jobs and updates their status in the job dictionary.

        This method iterates through all jobs, checks if a ".finished" or a ".failed" file exists in
        the job's folder, and updates the job's status accordingly. If at least one job is not
        finished or failed, the overall status is set to "to_finish". If all jobs are finished or
        failed, the overall status is set to "finished".

        Returns:
            tuple[dict[str, Any], str]: A tuple containing:
            - A dictionary with all jobs and their updated statuses.
            - A string representing the final status ("to_finish" or "finished").
        """
        dic_all_jobs = self.get_all_jobs()
        at_least_one_job_to_finish = False
        final_status = "to_finish"
        with self.lock:
            # Get dic tree once to avoid reloading it for every job
            dic_tree = self.dic_tree

            # First pass to update the state of the tree
            for job in dic_all_jobs:
                # Skip jobs that are already finished, failed or unsubmittable
                if nested_get(dic_tree, dic_all_jobs[job]["l_keys"] + ["status"]) in [
                    "finished",
                    "failed",
                    "unsubmittable",
                ]:
                    continue

                # Check the state of the others
                relative_job_folder = os.path.dirname(job)
                absolute_job_folder = f"{self.abs_path}/{relative_job_folder}"
                if os.path.exists(f"{absolute_job_folder}/.finished"):
                    nested_set(dic_tree, dic_all_jobs[job]["l_keys"] + ["status"], "finished")
                # Check if the job failed otherwise (not to resubmit it again)
                elif os.path.exists(f"{absolute_job_folder}/.failed"):
                    nested_set(dic_tree, dic_all_jobs[job]["l_keys"] + ["status"], "failed")
                # else:
                #     at_least_one_job_to_finish = True

            # Second pass to update the state of the tree with unreachable jobs
            dependency_graph = DependencyGraph(dic_tree, dic_all_jobs)
            for job in dic_all_jobs:
                # Get all failed dependencies across the tree
                l_dep_failed = dependency_graph.get_failed_dependency(job)
                if len(l_dep_failed) > 0:
                    nested_set(dic_tree, dic_all_jobs[job]["l_keys"] + ["status"], "unsubmittable")
                elif nested_get(dic_tree, dic_all_jobs[job]["l_keys"] + ["status"]) == "to_submit":
                    at_least_one_job_to_finish = True

            if not at_least_one_job_to_finish:
                # No more jobs to submit so finished
                dic_tree["status"] = final_status = "finished"
                # Last pass to check if all jobs are properly finished
                for job in dic_all_jobs:
                    if nested_get(dic_tree, dic_all_jobs[job]["l_keys"] + ["status"]) != "finished":
                        dic_tree["status"] = final_status = "finished with issues"
                        break

            # Update dic_tree from cluster_submission
            self.dic_tree = dic_tree

        return dic_all_jobs, final_status

    def submit(
        self,
        one_generation_at_a_time: bool = False,
        dic_additional_commands_per_gen: Optional[dict[int, str]] = None,
        dic_dependencies_per_gen: Optional[dict[int, list[str]]] = None,
        dic_copy_back_per_gen: Optional[dict[int, dict[str, bool]]] = None,
        name_config: str = "config.yaml",
    ) -> str:
        """
        Submits the jobs to the cluster. Note that copying back large files (e.g. json colliders)
        can trigger a throttling mechanism in AFS.

        The following arguments are only used for HTC jobs submission:
        - dic_additional_commands_per_gen
        - dic_dependencies_per_gen
        - dic_copy_back_per_gen
        - name_config

        Args:
            one_generation_at_a_time (bool, optional): Whether to submit one full generation at a
                time. Defaults to False.
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
            str: The final status of the jobs.
        """
        # Handle mutable default arguments
        if dic_additional_commands_per_gen is None:
            dic_additional_commands_per_gen = {}
        if dic_dependencies_per_gen is None:
            dic_dependencies_per_gen = {}
        if dic_copy_back_per_gen is None:
            dic_copy_back_per_gen = {}

        # Update the status of all jobs before submitting
        dic_all_jobs, final_status = self.check_and_update_all_jobs_status()
        if final_status == "finished":
            print("All jobs are finished. No need to submit.")
            return final_status
        elif final_status == "finished with issues":
            print("All jobs are finished but some did not run properly.")
            return final_status

        logging.info("Acquiring lock to submit jobs")
        with self.lock:
            # Get dic tree once to avoid reloading it for every job
            dic_tree = self.dic_tree

            # Submit the jobs
            self._submit(
                dic_tree,
                dic_all_jobs,
                one_generation_at_a_time,
                dic_additional_commands_per_gen,
                dic_dependencies_per_gen,
                dic_copy_back_per_gen,
                name_config,
            )

            # Update dic_tree from cluster_submission
            self.dic_tree = dic_tree
        logging.info("Jobs have been submitted. Lock released.")
        return final_status

    def _submit(
        self,
        dic_tree: dict[str, Any],
        dic_all_jobs: dict[str, dict[str, Any]],
        one_generation_at_a_time: bool,
        dic_additional_commands_per_gen: dict[int, str],
        dic_dependencies_per_gen: dict[int, list[str]],
        dic_copy_back_per_gen: dict[int, dict[str, bool]],
        name_config: str,
    ) -> None:
        """
        Submits the jobs to the cluster.

        Args:
            dic_tree (dict[str, Any]): The dictionary tree structure.
            dic_all_jobs (dict[str, dict[str,Any]]): A dictionary containing all jobs.
            one_generation_at_a_time (bool): Whether to submit one full generation at a time.
            dic_additional_commands_per_gen (dict[int, str], optional): Additional commands per
                generation.

            The following arguments are only used for HTC jobs submission:

            dic_dependencies_per_gen (dict[int, list[str]], optional): Dependencies per generation.
                Only used when doing a HTC submission. Defaults to None.
            dic_copy_back_per_gen (Optional[dict[int, dict[str, bool]]], optional): A dictionary
                containing the files to copy back per generation.
            name_config (str, optional): The name of the configuration file for the study.
        """
        # Collect dict of list of unfinished jobs for every tree branch and every gen
        dic_to_submit_by_gen = {}
        dic_summary_by_gen = {}
        dependency_graph = DependencyGraph(dic_tree, dic_all_jobs)
        for job in dic_all_jobs:
            dic_to_submit_by_gen, dic_summary_by_gen = self._check_job_submit_status(
                job,
                dic_tree,
                dic_all_jobs,
                dic_to_submit_by_gen,
                dic_summary_by_gen,
                dependency_graph,
            )

        # Only keep the topmost generation if one_generation_at_a_time is True
        if one_generation_at_a_time:
            logging.info(
                "Cropping list of jobs to submit to ensure only one generation is submitted at "
                "a time."
            )
            max_gen = max(dic_to_submit_by_gen.keys())
            dic_to_submit_by_gen = {max_gen: dic_to_submit_by_gen[max_gen]}

        # Convert dic_to_submit_by_gen to contain all requested information
        l_jobs_to_submit = [job for dic_gen in dic_to_submit_by_gen.values() for job in dic_gen]

        # Generate run files for the jobs to submit
        # ! Run files are generated at submit and not at configuration as the configuration
        # ! files are created at the end of each generation
        dic_tree = self.generate_run_files(
            dic_tree,
            l_jobs_to_submit,
            dic_additional_commands_per_gen,
            dic_dependencies_per_gen=dic_dependencies_per_gen,
            dic_copy_back_per_gen=dic_copy_back_per_gen,
            name_config=name_config,
        )

        # Create the ClusterSubmission object
        path_submission_file = f"{self.abs_path}/{self.study_name}/submission/submission_file.sub"
        cluster_submission = ClusterSubmission(
            self.study_name,
            l_jobs_to_submit,
            dic_all_jobs,
            dic_tree,
            path_submission_file,
            self.abs_path,
        )

        # Write and submit the submission files
        logging.info("Writing and submitting submission files")
        dic_submission_files = cluster_submission.write_sub_files(dic_summary_by_gen)

        # Log the state of the jobs
        self.log_jobs_state(dic_summary_by_gen)
        for submission_type, (
            list_of_jobs,
            l_submission_filenames,
        ) in dic_submission_files.items():
            cluster_submission.submit(list_of_jobs, l_submission_filenames, submission_type)

    @staticmethod
    def log_jobs_state(dic_summary_by_gen: dict[int, dict[str, int]]) -> None:
        """
        Logs the state of jobs for each generation.

        Args:
            dic_summary_by_gen (dict): A dictionary where the keys are generation numbers
                and the values are dictionaries summarizing job states.
                Each summary dictionary should contain the following keys:
                - 'to_submit_later': int, number of jobs left to submit later
                - 'running_or_queuing': int, number of jobs running or queuing
                - 'submitted_now': int, number of jobs submitted now
                - 'finished': int, number of jobs finished
                - 'failed': int, number of jobs failed
                - 'dependency_failed': int, number of jobs on hold due to failed dependencies

        Returns:
            None
        """
        print("State of the jobs:")
        for gen, dic_summary in dic_summary_by_gen.items():
            print("********************************")
            print(f"Generation {gen}")
            print(f"Jobs left to submit later: {dic_summary['to_submit_later']}")
            print(f"Jobs running or queuing: {dic_summary['running_or_queuing']}")
            print(f"Jobs submitted now: {dic_summary['submitted_now']}")
            print(f"Jobs finished: {dic_summary['finished']}")
            print(f"Jobs failed: {dic_summary['failed']}")
            print(f"Jobs on hold due to failed dependencies: {dic_summary['dependency_failed']}")
            print("********************************")

    @staticmethod
    def _check_job_submit_status(
        job: str,
        dic_tree: dict[str, Any],
        dic_all_jobs: dict[str, dict[str, Any]],
        dic_to_submit_by_gen: dict[int, list[str]],
        dic_summary_by_gen: dict[int, dict[str, int]],
        dependency_graph: DependencyGraph,
    ) -> tuple[dict[int, list[str]], dict[int, dict[str, int]]]:
        """
        Checks the status and dependencies of a job and updates the submission and summary
        dictionaries.

        Args:
            job (str): The job identifier.
            dic_tree (dict[str, Any]): The dictionary tree structure.
            dic_all_jobs (dict[str, dict[str,Any]]): A dictionary containing all jobs.
            dic_to_submit_by_gen (dict[int, list[str]]): A dictionary where keys are generation
                numbers and values are lists of jobs to submit for each generation.
            dic_summary_by_gen (dict[int, dict[str, int]]): A dictionary where keys are generation
                numbers and values are dictionaries summarizing job states.
            dependency_graph (DependencyGraph): An object to check job dependencies.

        Returns:
            tuple[dict[int, list[str]], dict[int, dict[str, int]]]: Updated dictionaries for jobs to
                submit and job summaries.
        """
        gen = dic_all_jobs[job]["gen"]
        if gen not in dic_to_submit_by_gen:
            dic_to_submit_by_gen[gen] = []
            dic_summary_by_gen[gen] = {
                "finished": 0,
                "failed": 0,
                "dependency_failed": 0,
                "running_or_queuing": 0,
                "submitted_now": 0,
                "to_submit_later": 0,
            }
        logging.info(f"Checking job {job} dependencies and status in tree")
        l_dep = dependency_graph.get_unfinished_dependency(job)
        l_dep_failed = dependency_graph.get_failed_dependency(job)

        # Job will be on hold as it has failed dependencies
        if len(l_dep_failed) > 0:
            logging.warning(
                f"Job {job} has failed dependencies: {l_dep_failed}, it won't be submitted."
            )
            dic_summary_by_gen[gen]["dependency_failed"] += 1

        # Jobs is waiting for dependencies to finish
        elif len(l_dep) > 0:
            dic_summary_by_gen[gen]["to_submit_later"] += 1

        # Job dependencies are ok
        elif len(l_dep) == 0:
            # But job has failed already
            if nested_get(dic_tree, dic_all_jobs[job]["l_keys"] + ["status"]) == "failed":
                dic_summary_by_gen[gen]["failed"] += 1

            # Or job has finished already
            elif nested_get(dic_tree, dic_all_jobs[job]["l_keys"] + ["status"]) == "finished":
                dic_summary_by_gen[gen]["finished"] += 1

            # Else everything is ok, added to the submit dict
            else:
                logging.info(f"Job {job} is added for submission.")
                dic_to_submit_by_gen[gen].append(job)
                # We'll determine which jobs actually have to be submitted and which jobs
                # are running at the end of the function, after querying the cluster or the local pc

        return dic_to_submit_by_gen, dic_summary_by_gen

    def keep_submit_until_done(
        self,
        one_generation_at_a_time: bool = False,
        wait_time: float = 30,
        dic_additional_commands_per_gen: Optional[dict[int, str]] = None,
        dic_dependencies_per_gen: Optional[dict[int, list[str]]] = None,
        dic_copy_back_per_gen: Optional[dict[int, dict[str, bool]]] = None,
        name_config: str = "config.yaml",
    ) -> None:
        """
        Keeps submitting jobs until all jobs are finished or failed.

        The following arguments are only used for HTC jobs submission:
        - dic_additional_commands_per_gen
        - dic_dependencies_per_gen
        - dic_copy_back_per_gen
        - name_config

        Args:
            one_generation_at_a_time (bool, optional): Whether to submit one full generation at a
                time. Defaults to False.
            wait_time (float, optional): The wait time between submissions in minutes.
                Defaults to 30.
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
        # Handle mutable default arguments
        if dic_additional_commands_per_gen is None:
            dic_additional_commands_per_gen = {}
        if dic_dependencies_per_gen is None:
            dic_dependencies_per_gen = {}

        if wait_time < 1 / 20:
            logging.warning("Wait time should be at least 10 seconds to prevent locking errors.")
            logging.warning("Setting wait time to 10 seconds.")
            wait_time = 10 / 60

        # I don't need to lock the tree here since the status cheking is read only and
        # the lock is acquired in the submit method for the submission
        while self.submit(
            one_generation_at_a_time,
            dic_additional_commands_per_gen,
            dic_dependencies_per_gen,
            dic_copy_back_per_gen,
            name_config,
        ) not in ["finished", "finished with issues"]:
            # Wait for a certain amount of time before checking again
            logging.info(f"Waiting {wait_time} minutes before checking again.")
            time.sleep(wait_time * 60)
