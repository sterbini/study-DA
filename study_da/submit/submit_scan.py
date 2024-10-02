# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import logging
import os
import time
from typing import Self

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
        self: Self,
        path_tree: str,
        path_python_environment: str,
        path_python_environment_container: str = "",
        path_container_image: str | None = None,
    ):
        # Path to study files
        self.path_tree = path_tree

        # Absolute path to the tree
        self.abs_path_tree = os.path.abspath(path_tree)

        # Name of the study folder
        self.study_name = os.path.dirname(path_tree)

        # Absolute path to the study folder (get from the path_tree)
        self.abs_path = os.path.abspath(self.study_name).split(f"/{self.study_name}")[0]

        # Path to the python environment, activate with `source path_python_environment`
        # Turn to abolute path if it is not already
        if not os.path.isabs(path_python_environment):
            self.path_python_environment = os.path.abspath(path_python_environment)
        else:
            self.path_python_environment = path_python_environment

        # Add /bin/activate to the path_python_environment if needed
        if not self.path_python_environment.endswith("/bin/activate"):
            self.path_python_environment += "/bin/activate"

        # Container image (Docker or Singularity, if any)
        # Turn to abolute path if it is not already
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
                "The path to the python environment in the container must be set if the container image is set."
            )

        # Add /bin/activate to the path_python_environment if needed
        if not self.path_python_environment_container.endswith("/bin/activate"):
            self.path_python_environment_container += "/bin/activate"

        # Lock file to avoid concurrent access (softlock as several platforms are used)
        self.lock = SoftFileLock(f"{self.path_tree}.lock", timeout=30)

    # dic_tree as a property so that it is reloaded every time it is accessed
    @property
    def dic_tree(self: Self):
        return load_dic_from_path(self.path_tree)[0]

    # Setter for the dic_tree property
    @dic_tree.setter
    def dic_tree(self: Self, value: dict):
        write_dic_to_path(value, self.path_tree)

    # Property for the same reason
    def configure_jobs(self: Self):
        # Lock since we are modifying the tree
        with self.lock:
            dic_tree = ConfigJobs(self.dic_tree).find_and_configure_jobs()

            # Add the python environment, container image and absolute path of the study to the tree
            dic_tree["python_environment"] = self.path_python_environment
            dic_tree["container_image"] = self.path_container_image
            dic_tree["absolute_path"] = self.abs_path
            dic_tree["status"] = "To finish"

            # Explicitly set the dic_tree property to force rewrite
            self.dic_tree = dic_tree

    def get_all_jobs(self: Self):
        return ConfigJobs(self.dic_tree).find_all_jobs()

    def generate_run_files(
        self: Self,
        dic_tree: dict,
        l_jobs_to_submit: list[str],
        dic_additional_commands_per_gen: dict[int, str] = {},
        dic_dependencies_per_gen: dict[int, list[str]] = {},
        name_config: str = "config.yaml",
    ):
        dic_all_jobs = self.get_all_jobs()
        for job in l_jobs_to_submit:
            l_keys = dic_all_jobs[job]["l_keys"]
            job_name = job.split("/")[-1]
            relative_job_folder = "/".join(job.split("/")[:-1])
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
                logging.warning(f"Run file already exists for job {job}. Skipping.")
                continue

            run_str = generate_run_file(
                absolute_job_folder,
                job_name,
                path_python_environment,
                generation_number,
                self.abs_path_tree,
                l_keys,
                htc="htc" in submission_type,
                additionnal_command=dic_additional_commands_per_gen[generation_number],
                l_dependencies=dic_dependencies_per_gen[generation_number],
                name_config=name_config,
            )
            # Write the run file
            path_run_job = f"{absolute_job_folder}/run.sh"
            with open(path_run_job, "w") as f:
                f.write(run_str)

            # Record the path to the run file in the tree
            nested_set(dic_tree, l_keys + ["path_run"], path_run_job)

        return dic_tree

    def submit(
        self: Self,
        one_generation_at_a_time: bool = False,
        dic_additional_commands_per_gen: dict[int, str] = {},
        dic_dependencies_per_gen: dict[int, list[str]] = {},
        name_config: str = "config.yaml",
    ):
        dic_all_jobs = self.get_all_jobs()

        with self.lock:
            # Get dic tree once to avoid reloading it for every job
            dic_tree = self.dic_tree

            # Collect dict of list of unfinished jobs for every tree branch and every gen
            dic_to_submit_by_gen = {}
            for job in dic_all_jobs:
                l_dep = DependencyGraph(dic_tree, dic_all_jobs).get_unfinished_dependency(job)
                # If job parents are finished and job is not finished, submit it
                if (
                    len(l_dep) == 0
                    and nested_get(self.dic_tree, dic_all_jobs[job]["l_keys"] + ["status"])
                    != "finished"
                ):
                    gen = dic_all_jobs[job]["gen"]
                    if gen not in dic_to_submit_by_gen:
                        dic_to_submit_by_gen[gen] = []
                    dic_to_submit_by_gen[gen].append(job)

            # Only keep the topmost generation if one_generation_at_a_time is True
            if one_generation_at_a_time:
                max_gen = max(dic_to_submit_by_gen.keys())
                dic_to_submit_by_gen = {max_gen: dic_to_submit_by_gen[max_gen]}

            # Convert dic_to_submit_by_gen to contain all requested information
            l_jobs_to_submit = [job for dic_gen in dic_to_submit_by_gen.values() for job in dic_gen]

            # Generate the run files if not already done
            dic_tree = self.generate_run_files(
                dic_tree,
                l_jobs_to_submit,
                dic_additional_commands_per_gen,
                dic_dependencies_per_gen,
                name_config,
            )

            # Write to the tree if no more jobs are to be submitted
            if not l_jobs_to_submit:
                dic_tree["status"] = "finished"
                print("All jobs are done.")

            path_submission_file = (
                f"{self.abs_path}/{self.study_name}/submission/submission_file.sub"
            )
            cluster_submission = ClusterSubmission(
                self.study_name,
                l_jobs_to_submit,
                dic_all_jobs,
                dic_tree,
                path_submission_file,
                self.abs_path,
            )

            # Write and submit the submission files
            dic_submission_files = cluster_submission.write_sub_files()
            for submission_type, (
                list_of_jobs,
                l_submission_filenames,
            ) in dic_submission_files.items():
                cluster_submission.submit(list_of_jobs, l_submission_filenames, submission_type)

            # Update dic_tree from cluster_submission
            self.dic_tree = cluster_submission.dic_tree

    def keep_submit_until_done(
        self: Self, one_generation_at_a_time: bool = False, wait_time: float = 30
    ):
        if wait_time < 1 / 20:
            logging.warning("Wait time should be at least 10 seconds to prevent locking errors.")
            logging.warning("Setting wait time to 10 seconds.")
            wait_time = 10 / 60

        while self.dic_tree["status"] != "finished":
            self.submit(one_generation_at_a_time)
            # Wait for a certain amount of time before checking again
            time.sleep(wait_time * 60)
