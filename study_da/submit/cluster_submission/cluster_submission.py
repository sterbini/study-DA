"""Module for submitting jobs on a cluster (or locally)."""

# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import logging
import os
import subprocess
from pathlib import Path

import psutil

# Third party imports
from study_da.utils import nested_get

# Local imports
from .submission_statements import HTC, HTCDocker, LocalPC, Slurm, SlurmDocker


# ==================================================================================================
# --- Class for job submission
# ==================================================================================================
class ClusterSubmission:
    """
    A class to handle the submission of jobs to various cluster systems such as local PC, HTC, and
    Slurm.

    Attributes:
        study_name (str): The name of the study.
        l_jobs_to_submit (list[str]): A list of jobs to submit.
        dic_all_jobs (dict): A dictionary containing all jobs.
        dic_tree (dict): A dictionary representing the job tree.
        path_submission_file (str): The path to the submission file.
        abs_path_study (str): The absolute path to the study.
        dic_submission (dict): A dictionary mapping submission types to their corresponding classes.

    Methods:
        dic_id_to_path_job() -> dict | None:
            Getter for the dictionary mapping job IDs to their paths.
        dic_id_to_path_job(dic_id_to_path_job: dict[int, str]):
            Setter for the dictionary mapping job IDs to their paths.
        _update_dic_id_to_path_job(running_jobs: list[str], queuing_jobs: list[str]) -> None:
            Updates the dictionary mapping job IDs to their paths based on the current running and
            queuing jobs.
        _check_submission_type() -> tuple[bool, bool, bool]:
            Checks the submission type for the jobs and ensures that HTC and Slurm submissions are
            not mixed.
        _get_state_jobs(verbose: bool = True) -> tuple[list[str], list[str]]:
            Gets the current state of the jobs (running and queuing).
        _test_job(job: str, path_job: str, running_jobs: list[str], queuing_jobs: list[str]) -> bool:
            Tests if a job is completed, running, or queuing.
        _return_htc_flavour(job: str) -> str:
            Returns the HTC flavor for a given job.
        _return_abs_path_job(job: str) -> tuple[str, str]:
            Returns the absolute path of a job.
        _write_sub_files_slurm_docker(sub_filename: str, running_jobs: list[str],
            queuing_jobs: list[str], list_of_jobs: list[str]) -> tuple[list[str], list[str]]:
            Writes submission files for Slurm Docker jobs.
        _get_Sub(job: str, submission_type: str, sub_filename: str, abs_path_job: str,
            context: str) -> LocalPC | HTC | HTCDocker | Slurm | SlurmDocker:
            Returns the appropriate submission object based on the submission type.
        _write_sub_file(sub_filename: str, running_jobs: list[str], queuing_jobs: list[str],
            list_of_jobs: list[str], submission_type: str) -> tuple[list[str], list[str]]:
            Writes a submission file for the given jobs.
        _write_sub_files(sub_filename: str, running_jobs: list[str], queuing_jobs: list[str],
            list_of_jobs: list[str], submission_type: str) -> tuple[list[str], list[str]]:
            Writes submission files for the given jobs based on the submission type.
        write_sub_files() -> dict:
            Writes submission files for all jobs to be submitted and returns a dictionary of
            submission files.
        _update_job_status_from_hpc_output(submit_command: str, submission_type: str,
            dic_id_to_path_job_temp: dict, list_of_jobs: list[str], idx_submission: int = 0)
                -> tuple[dict, int]:
            Updates the job status from the HPC output.
        submit(list_of_jobs: list[str], l_submission_filenames: list[str], submission_type: str)
            -> None:
            Submits the jobs to the appropriate cluster system.
        _get_local_jobs() -> list[str]:
            Gets the list of local jobs.
        _get_condor_jobs(status: str, force_query_individually: bool = False) -> list[str]:
            Gets the list of Condor jobs based on the status.
        _get_slurm_jobs(status: str, force_query_individually: bool = False) -> list[str]:
            Gets the list of Slurm jobs based on the status.
        querying_jobs(check_local: bool, check_htc: bool, check_slurm: bool,
            status: str = "running") -> list[str]:
            Queries the jobs based on the submission type and status.
    """

    def __init__(
        self,
        study_name: str,
        l_jobs_to_submit: list[str],
        dic_all_jobs: dict,
        dic_tree: dict,
        path_submission_file: str,
        abs_path_study: str,
    ):
        self.study_name: str = study_name
        self.l_jobs_to_submit: list[str] = l_jobs_to_submit
        self.dic_all_jobs: dict = dic_all_jobs
        self.dic_tree: dict = dic_tree
        self.path_submission_file: str = path_submission_file
        self.abs_path_study: str = abs_path_study
        self.dic_submission: dict = {
            "local": LocalPC,
            "htc": HTC,
            "htc_docker": HTCDocker,
            "slurm": Slurm,
            "slurm_docker": SlurmDocker,
        }
        """
        Initialize the ClusterSubmission class.

        Args:
            study_name (str): The name of the study.
            l_jobs_to_submit (list[str]): A list of job names to submit.
            dic_all_jobs (dict): A dictionary containing all jobs.
            dic_tree (dict): A dictionary representing the job tree structure.
            path_submission_file (str): The path to the submission file.
            abs_path_study (str): The absolute path to the study.
        """

    # Getter for dic_id_to_path_job
    @property
    def dic_id_to_path_job(self) -> dict | None:
        """
        Generates a dictionary mapping job IDs to their respective job paths.

        This method iterates over the list of jobs to submit and constructs a dictionary
        where the keys are job IDs and the values are the absolute paths to the jobs.
        If no job IDs are found, the method returns None.

        Args:
            None

        Returns:
            dict | None: A dictionary mapping job IDs to job paths, or None if no job IDs are found.
        """
        dic_id_to_path_job = {}
        found_at_least_one = False
        for job in self.l_jobs_to_submit:
            l_keys = self.dic_all_jobs[job]["l_keys"]
            subdic_job = nested_get(self.dic_tree, l_keys)
            if "id_sub" in subdic_job:
                dic_id_to_path_job[subdic_job["id_sub"]] = self._return_abs_path_job(job)[0]
                found_at_least_one = True

        return dic_id_to_path_job if found_at_least_one else None

    # Setter for dic_id_to_path_job
    @dic_id_to_path_job.setter
    def dic_id_to_path_job(self, dic_id_to_path_job: dict[int, str]):
        """
        Updates the internal job submission tree with job IDs and their corresponding paths.

        Args:
            dic_id_to_path_job (dict[int, str]): A dictionary mapping job IDs (integers) to their
            respective paths (strings).

        Raises:
            AssertionError: If dic_id_to_path_job is not a dictionary.

        Notes:
            - Ensures all job IDs are integers.
            - Updates the internal job submission tree by adding or removing job IDs based on the
                provided dictionary.
            - If a job's path is found in the dictionary, its ID is updated in the tree.
            - If a job's ID is not found in the dictionary, it is removed from the tree.
        """
        assert isinstance(dic_id_to_path_job, dict)
        # Ensure all ids are integers
        dic_id_to_path_job = {
            int(id_job): path_job for id_job, path_job in dic_id_to_path_job.items()
        }
        dic_job_to_id = {path_job: int(id_job) for id_job, path_job in dic_id_to_path_job.items()}

        # Update the tree
        for job in self.l_jobs_to_submit:
            path_job = self._return_abs_path_job(job)[0]
            l_keys = self.dic_all_jobs[job]["l_keys"]
            subdic_job = nested_get(self.dic_tree, l_keys)
            if "id_sub" in subdic_job and int(subdic_job["id_sub"]) not in dic_id_to_path_job:
                del subdic_job["id_sub"]
            elif "id_sub" not in subdic_job and path_job in dic_job_to_id:
                subdic_job["id_sub"] = dic_job_to_id[path_job]
            # Else all is consistent

    def _update_dic_id_to_path_job(self, running_jobs: list[str], queuing_jobs: list[str]) -> None:
        """
        Updates the dictionary `dic_id_to_path_job` by removing jobs that are no longer running or
        queuing.

        Args:
            running_jobs (list[str]): A list of job identifiers that are currently running.
            queuing_jobs (list[str]): A list of job identifiers that are currently queuing.

        Returns:
            None
        """
        # Look for jobs in the dictionnary that are not running or queuing anymore
        set_current_jobs = set(running_jobs + queuing_jobs)
        if self.dic_id_to_path_job is not None:
            dic_id_to_path_job = self.dic_id_to_path_job
            for id_job, job in self.dic_id_to_path_job.items():
                if job not in set_current_jobs:
                    del dic_id_to_path_job[id_job]

            # Update dic_id_to_path_job
            self.dic_id_to_path_job = dic_id_to_path_job

    def _check_submission_type(self) -> tuple[bool, bool, bool]:
        """
        Checks the types of job submissions in the current batch and ensures that
        there is no mixing of HTC and Slurm submission types.

        Args:
            None

        Returns:
            tuple[bool, bool, bool]: A tuple containing three boolean values indicating
            whether there are local, HTC, and Slurm submissions respectively.

        Raises:
            ValueError: If both HTC and Slurm submission types are found in the jobs to submit.
        """
        check_local = False
        check_htc = False
        check_slurm = False
        for job in self.l_jobs_to_submit:
            l_keys = self.dic_all_jobs[job]["l_keys"]
            submission_type = nested_get(self.dic_tree, l_keys + ["submission_type"])
            if submission_type == "local":
                check_local = True
            elif submission_type in ["htc", "htc_docker"]:
                check_htc = True
            elif submission_type in ["slurm", "slurm_docker"]:
                check_slurm = True

        if check_htc and check_slurm:
            raise ValueError("Error: Mixing htc and slurm submission is not allowed")

        return check_local, check_htc, check_slurm

    def _get_state_jobs(self, verbose: bool = True) -> tuple[list[str], list[str]]:
        """
        Retrieves the state of jobs (running and queuing) based on the submission type.

        This method first determines the submission type (local, HTC, or Slurm) and then queries
        the jobs accordingly. It updates the internal dictionary mapping job IDs to their paths
        and optionally prints the running and queuing jobs.

        Args:
            verbose (bool): If True, prints the running and queuing jobs. Default is True.

        Returns:
            tuple[list[str], list[str]]: A tuple containing two lists:
                - The first list contains the IDs of running jobs.
                - The second list contains the IDs of queuing jobs.
        """
        # First check whether the jobs are submitted on local, htc or slurm
        check_local, check_htc, check_slurm = self._check_submission_type()

        # Then query accordingly
        running_jobs = self.querying_jobs(check_local, check_htc, check_slurm, status="running")
        queuing_jobs = self.querying_jobs(check_local, check_htc, check_slurm, status="queuing")
        self._update_dic_id_to_path_job(running_jobs, queuing_jobs)
        if verbose:
            logging.info("Running: \n" + "\n".join(running_jobs))
            logging.info("queuing: \n" + "\n".join(queuing_jobs))
        return running_jobs, queuing_jobs

    def _test_job(
        self, job: str, path_job: str, running_jobs: list[str], queuing_jobs: list[str]
    ) -> bool:
        """
        Tests the status of a job and determines if it needs to be (re)submitted.

        Args:
            job (str): The job identifier.
            path_job (str): The path to the job.
            running_jobs (list[str]): A list of currently running jobs.
            queuing_jobs (list[str]): A list of currently queuing jobs.

        Returns:
            bool: True if the job must be (re)submitted, False otherwise.
        """
        # Test if job is completed
        l_keys = self.dic_all_jobs[job]["l_keys"]
        completed = nested_get(self.dic_tree, l_keys + ["status"]) == "finished"
        if completed:
            logging.info(f"{path_job} is already completed.")

        # Test if job is running
        elif path_job in running_jobs:
            logging.info(f"{path_job} is already running.")

        # Test if job is queuing
        elif path_job in queuing_jobs:
            logging.info(f"{path_job} is already queuing.")

        # True if job must be (re)submitted
        else:
            return True
        return False

    def _return_htc_flavour(self, job: str) -> str:
        """
        Retrieve the HTC flavor for a given job.

        Args:
            job (str): The job identifier.

        Returns:
            str: The HTC flavor associated with the job.
        """
        l_keys = self.dic_all_jobs[job]["l_keys"]
        return nested_get(self.dic_tree, l_keys + ["htc_flavor"])

    def _return_abs_path_job(self, job: str) -> tuple[str, str]:
        """
        Generate the relative and absolute paths for a given job.

        Args:
            job (str): The job string containing the path to the job file.

        Returns:
            tuple[str, str]: A tuple containing:
            - path_job (str): The relative path to the job directory.
            - abs_path_job (str): The absolute path to the job directory.
        """
        # Get corresponding path job (remove the python file name)
        path_job = "/".join(job.split("/")[:-1]) + "/"
        abs_path_job = f"{self.abs_path_study}/{path_job}"
        return path_job, abs_path_job

    def _write_sub_files_slurm_docker(
        self,
        sub_filename: str,
        running_jobs: list[str],
        queuing_jobs: list[str],
        list_of_jobs: list[str],
    ) -> tuple[list[str], list[str]]:
        """
        Generates SLURM submission files for Docker jobs and writes them to disk.

        This method iterates over a list of jobs, checks their status (running, queuing, or
        completed), and writes the corresponding SLURM submission files for Docker jobs. The
        submission files are written to disk with a specific naming convention.

        Args:
            sub_filename (str): The base name for the submission files.
            running_jobs (list[str]): A list of job identifiers that are currently running.
            queuing_jobs (list[str]): A list of job identifiers that are currently queuing.
            list_of_jobs (list[str]): A list of job identifiers to process.

        Returns:
            tuple[list[str], list[str]]: A tuple containing two lists:
            - A list of filenames for the generated submission files.
            - A list of job identifiers that were updated.
        """
        l_filenames = []
        list_of_jobs_updated = []
        for idx_job, job in enumerate(list_of_jobs):
            path_job, abs_path_job = self._return_abs_path_job(job)

            # Test if job is running, queuing or completed
            if self._test_job(job, path_job, running_jobs, queuing_jobs):
                filename_sub = f"{sub_filename.split('.sub')[0]}_{idx_job}.sub"

                # Get job context
                l_keys = self.dic_all_jobs[job]["l_keys"]
                context = nested_get(self.dic_tree, l_keys + ["context"])

                # Write the submission files
                # ! Careful, I implemented a fix for path due to the temporary home recovery folder
                logging.info(f'Writing submission file for node "{abs_path_job}"')
                fix = True
                Sub = self.dic_submission["slurm_docker"](
                    filename_sub, abs_path_job, context, self.dic_tree["container_image"], fix=fix
                )
                with open(filename_sub, "w") as fid:
                    fid.write(Sub.head + "\n")
                    if fix:
                        fid.write(Sub.str_fixed_run + "\n")
                    fid.write(Sub.body + "\n")
                    fid.write(Sub.tail + "\n")

                l_filenames.append(filename_sub)
                list_of_jobs_updated.append(job)
        return l_filenames, list_of_jobs_updated

    def _get_Sub(
        self, job: str, submission_type: str, sub_filename: str, abs_path_job: str, context: str
    ) -> LocalPC | HTC | HTCDocker | Slurm | SlurmDocker:
        """
        Generate a submission object based on the specified submission type.

        Args:
            job (str): The job identifier.
            submission_type (str): The type of submission (e.g., "slurm", "htc", "htc_docker",
                "slurm_docker", "local").
            sub_filename (str): The submission filename.
            abs_path_job (str): The absolute path to the job.
            context (str): The context for the submission.

        Returns:
            LocalPC | HTC | HTCDocker | Slurm | SlurmDocker: An instance of the appropriate
                submission class.

        Raises:
            ValueError: If the submission type is not valid or if the container_image is not defined
                in the tree for docker submissions.
        """
        match submission_type:
            case "slurm":
                return self.dic_submission[submission_type](sub_filename, abs_path_job, context)
            case "htc":
                return self.dic_submission[submission_type](
                    sub_filename, abs_path_job, context, self._return_htc_flavour(job)
                )
            case w if w in ["htc_docker", "slurm_docker"]:
                # Path to singularity image
                if (
                    "container_image" in self.dic_tree
                    and self.dic_tree["container_image"] is not None
                ):
                    self.path_image = self.dic_tree["container_image"]
                else:
                    raise ValueError(
                        "Error: container_image is not defined in the tree. Please define it in the"
                        " config.yaml file."
                    )

                if submission_type == "htc_docker":
                    return self.dic_submission[submission_type](
                        sub_filename,
                        abs_path_job,
                        context,
                        self.path_image,
                        self._return_htc_flavour(job),
                    )
                else:
                    return self.dic_submission[submission_type](
                        sub_filename, abs_path_job, context, self.path_image
                    )
            case "local":
                return self.dic_submission[submission_type](sub_filename, abs_path_job)
            case _:
                raise ValueError(f"Error: {submission_type} is not a valid submission mode")

    def _write_sub_file(
        self,
        sub_filename: str,
        running_jobs: list[str],
        queuing_jobs: list[str],
        list_of_jobs: list[str],
        submission_type: str,
    ) -> tuple[list[str], list[str]]:
        """
        Writes a submission file for a list of jobs and returns the updated list of jobs.

        Args:
            sub_filename (str): The filename for the submission file.
            running_jobs (list[str]): List of currently running jobs.
            queuing_jobs (list[str]): List of currently queuing jobs.
            list_of_jobs (list[str]): List of jobs to be submitted.
            submission_type (str): The type of submission.

        Returns:
            tuple[list[str], list[str]]: A tuple containing:
            - A list with the submission filename if the file was created, otherwise an empty list.
            - An updated list of jobs that were included in the submission file.
        """
        # Flag to know if the file can be submitted (at least one job in it)
        ok_to_submit = False

        # Flat to know if the header has been written
        header_written = False

        # Create folder to the submission file if it does not exist
        os.makedirs("/".join(sub_filename.split("/")[:-1]), exist_ok=True)

        # Updated list of jobs (without unsubmitted jobs)
        list_of_jobs_updated = []

        # Write the submission file
        Sub = None
        with open(sub_filename, "w") as fid:
            for job in list_of_jobs:
                # Get corresponding path job (remove the python file name)
                path_job, abs_path_job = self._return_abs_path_job(job)

                # Test if job is running, queuing or completed
                if self._test_job(job, path_job, running_jobs, queuing_jobs):
                    logging.info(f'Writing submission command for node "{abs_path_job}"')

                    # Get context
                    l_keys = self.dic_all_jobs[job]["l_keys"]
                    context = nested_get(self.dic_tree, l_keys + ["context"])

                    # Get Submission object
                    Sub = self._get_Sub(job, submission_type, sub_filename, abs_path_job, context)

                    # Take the first job as reference for head
                    if not header_written:
                        fid.write(Sub.head + "\n")
                        header_written = True

                    # Write instruction for submission
                    fid.write(Sub.body + "\n")

                    # Append job to list_of_jobs_updated
                    list_of_jobs_updated.append(job)

            # Tail instruction
            if Sub is not None:
                fid.write(Sub.tail + "\n")
                ok_to_submit = True

        if not ok_to_submit:
            os.remove(sub_filename)

        return ([sub_filename], list_of_jobs_updated) if ok_to_submit else ([], [])

    def _write_sub_files(
        self,
        sub_filename: str,
        running_jobs: list[str],
        queuing_jobs: list[str],
        list_of_jobs: list[str],
        submission_type: str,
    ) -> tuple[list[str], list[str]]:
        """
        Writes submission files based on the specified submission type.

        Args:
            sub_filename (str): The name of the submission file to be created.
            running_jobs (list[str]): A list of currently running jobs.
            queuing_jobs (list[str]): A list of jobs that are queued.
            list_of_jobs (list[str]): A list of all jobs to be submitted.
            submission_type (str): The type of submission system being used (e.g., "slurm_docker").

        Returns:
            tuple[list[str], list[str]]: A tuple containing two lists:
                - Updated list of running jobs.
                - Updated list of queuing jobs.
        """
        # Slurm docker is a peculiar case as one submission file must be created per job
        if submission_type == "slurm_docker":
            return self._write_sub_files_slurm_docker(
                sub_filename, running_jobs, queuing_jobs, list_of_jobs
            )

        else:
            return self._write_sub_file(
                sub_filename,
                running_jobs,
                queuing_jobs,
                list_of_jobs,
                submission_type,
            )

    def write_sub_files(self) -> dict:
        """
        Generates and writes submission files for jobs based on their submission type.

        This method categorizes jobs to be submitted by their submission type, writes the
        corresponding submission files, and returns a dictionary containing the submission
        files and their associated job contexts.

        Args:
            None

        Returns:
            dict: A dictionary where keys are submission types and values are tuples containing
                a list of updated jobs and a list of submission filenames.
        """
        running_jobs, queuing_jobs = self._get_state_jobs(verbose=False)

        # Make a dict of all jobs to submit depending on the submission type
        dic_jobs_to_submit = {key: [] for key in self.dic_submission.keys()}
        for job in self.l_jobs_to_submit:
            l_keys = self.dic_all_jobs[job]["l_keys"]
            submission_type = nested_get(self.dic_tree, l_keys + ["submission_type"])
            dic_jobs_to_submit[submission_type].append(job)  # type: ignore

        # Write submission files for each submission type
        dic_submission_files = {}
        for submission_type, list_of_jobs in dic_jobs_to_submit.items():
            if len(list_of_jobs) > 0:
                # Write submission files
                l_submission_filenames, list_of_jobs_updated = self._write_sub_files(
                    self.path_submission_file,
                    running_jobs,
                    queuing_jobs,
                    list_of_jobs,
                    submission_type,
                )

                # Record submission files and context
                dic_submission_files[submission_type] = (
                    list_of_jobs_updated,
                    l_submission_filenames,
                )

        return dic_submission_files

    def _update_job_status_from_hpc_output(
        self,
        submit_command: str,
        submission_type: str,
        dic_id_to_path_job_temp: dict,
        list_of_jobs: list[str],
        idx_submission: int = 0,
    ) -> tuple[dict, int]:
        """
        Updates the job status from the HPC output.

        This method parses the output of a job submission command to update the job status
        in a dictionary mapping job IDs to their respective paths. It supports both HTC and
        SLURM submission types.

        Args:
            submit_command (str): The command used to submit the job.
            submission_type (str): The type of submission system ('htc' or 'slurm').
            dic_id_to_path_job_temp (dict): A dictionary mapping job IDs to their paths.
            list_of_jobs (list[str]): A list of job paths.
            idx_submission (int, optional): The index of the current submission. Defaults to 0.

        Returns:
            tuple[dict, int]: A tuple containing the updated dictionary and the updated index of
                submission.

        Raises:
            RuntimeError: If there is an error in the submission process.
        """
        process = subprocess.run(
            submit_command.split(" "),
            capture_output=True,
        )

        output = process.stdout.decode("utf-8")
        output_error = process.stderr.decode("utf-8")
        if "ERROR" in output_error:
            raise RuntimeError(f"Error in submission: {output_error}")
        for line in output.split("\n"):
            if "htc" in submission_type:
                if "cluster" in line:
                    cluster_id = int(line.split("cluster ")[1][:-1])
                    dic_id_to_path_job_temp[cluster_id] = self._return_abs_path_job(
                        list_of_jobs[idx_submission]
                    )[0]
                    idx_submission += 1
            elif "slurm" in submission_type:
                if "Submitted" in line:
                    job_id = int(line.split(" ")[3])
                    dic_id_to_path_job_temp[job_id] = self._return_abs_path_job(
                        list_of_jobs[idx_submission]
                    )[0]
                    idx_submission += 1

        return dic_id_to_path_job_temp, idx_submission

    def submit(
        self, list_of_jobs: list[str], l_submission_filenames: list[str], submission_type: str
    ) -> None:
        """
        Submits a list of jobs to the specified submission system.

        Args:
            list_of_jobs (list[str]): List of job identifiers to be submitted.
            l_submission_filenames (list[str]): List of filenames containing submission scripts.
            submission_type (str): Type of submission system to use. Valid options are "local",
                "htc", "slurm", "htc_docker", and "slurm_docker".

        Raises:
            ValueError: If multiple submission files are provided for a non-"slurm_docker"
                submission type.
            ValueError: If the submission type is not valid.

        Returns:
            None
        """
        # Check that the submission file(s) is/are appropriate for the submission mode
        if len(l_submission_filenames) > 1 and submission_type != "slurm_docker":
            raise ValueError(
                "Error: Multiple submission files should not be implemented for this submission"
                " mode"
            )

        # Check that at least one job is being submitted
        if not l_submission_filenames:
            logging.info("No job being submitted.")

        # Submit
        dic_id_to_path_job_temp = {}
        idx_submission = 0
        for sub_filename in l_submission_filenames:
            if submission_type == "local":
                os.system(self.dic_submission[submission_type].get_submit_command(sub_filename))
            elif submission_type in {"htc", "slurm", "htc_docker", "slurm_docker"}:
                submit_command = self.dic_submission[submission_type].get_submit_command(
                    sub_filename
                )
                dic_id_to_path_job_temp, idx_submission = self._update_job_status_from_hpc_output(
                    submit_command,
                    submission_type,
                    dic_id_to_path_job_temp,
                    list_of_jobs,
                    idx_submission,
                )
            else:
                raise ValueError(f"Error: {submission_type} is not a valid submission mode")

        # Update and write the id-job file
        if dic_id_to_path_job_temp:
            assert len(dic_id_to_path_job_temp) == len(list_of_jobs)

        # Merge with the previous id-job file
        dic_id_to_path_job = self.dic_id_to_path_job

        # Update and write on disk
        if dic_id_to_path_job is not None:
            dic_id_to_path_job.update(dic_id_to_path_job_temp)
            self.dic_id_to_path_job = dic_id_to_path_job
        elif dic_id_to_path_job_temp:
            dic_id_to_path_job = dic_id_to_path_job_temp
            self.dic_id_to_path_job = dic_id_to_path_job

        logging.info("Jobs status after submission:")
        _, _ = self._get_state_jobs(verbose=True)

    def _get_local_jobs(self) -> list[str]:
        """
        Retrieves a list of local job paths.
        This method scans the current processes to identify jobs that are running
        a script named 'run.sh'. It extracts the job paths and filters them to
        include only the paths that are relevant to the current study.

        Args:
            None

        Returns:
            list[str]: A list of job paths that are currently running and relevant
            to the study.
        """

        l_path_jobs = []
        # Warning, does not work at the moment in lxplus...
        for ps in psutil.pids():
            try:
                aux = psutil.Process(ps).cmdline()
            except Exception:
                aux = []
            if len(aux) > 1 and "run.sh" in aux[-1]:
                job = str(Path(aux[-1]).parent)

                # Only get path after name of the study
                job = job.split(self.study_name)[1]
                l_path_jobs.append(f"{self.study_name}{job}/")
        return l_path_jobs

    def _get_condor_jobs(self, status: str, force_query_individually: bool = False) -> list[str]:
        """
        Retrieve the paths of Condor jobs based on their status.

        Args:
            status (str): The status of the jobs to retrieve. Can be "running" or "queuing".
            force_query_individually (bool, optional): If True, query each job individually if the
                id-job file is missing. Defaults to False.

        Returns:
            list[str]: A list of paths to the jobs that match the specified status.

        Raises:
            ValueError: If the status provided is not "running" or "queuing".

        Notes:
            - The method relies on the `condor_q` command to retrieve job information.
            - If the id-job file is missing and `force_query_individually` is False, jobs not in
                `dic_id_to_path_job` will be ignored.
            - If `force_query_individually` is True, the method will query each job individually to
                retrieve its path.
            - Warnings are printed if jobs are found that are not in the id-job file or if the
                id-job file is missing.
        """
        l_path_jobs = []
        dic_status = {"running": 1, "queuing": 2}
        condor_output = subprocess.run(["condor_q"], capture_output=True).stdout.decode("utf-8")

        # Check which jobs are running
        first_line = True
        first_missing_job = True
        for line in condor_output.split("\n")[4:]:
            if line == "":
                break
            jobid = int(line.split("ID:")[1][1:8])
            condor_status = line.split("      ")[1:5]  # Done, Run, Idle, and potentially Hold

            # If job is running/queuing, get the path to the job
            if condor_status[dic_status[status]] == "1":
                # Get path from dic_id_to_path_job if available
                if self.dic_id_to_path_job is not None:
                    if jobid in self.dic_id_to_path_job:
                        l_path_jobs.append(self.dic_id_to_path_job[jobid])
                    elif first_missing_job:
                        logging.warning(
                            "Warning, some jobs are queuing/running and are not in the id-job"
                            " file. They may come from another study. Ignoring them."
                        )
                        first_missing_job = False

                elif force_query_individually:
                    if first_line:
                        logging.warning(
                            "Warning, some jobs are queuing/running and the id-job file is"
                            " missing... Querying them individually."
                        )
                        first_line = False
                    job_details = subprocess.run(
                        ["condor_q", "-l", f"{jobid}"], capture_output=True
                    ).stdout.decode("utf-8")
                    job = job_details.split('Cmd = "')[1].split("run.sh")[0]

                    # Only get path after master_study
                    job = job.split(self.study_name)[1]
                    l_path_jobs.append(f"{self.study_name}{job}")

                elif first_line:
                    logging.warning(
                        "Warning, some jobs are queuing/running and the id-job file is"
                        " missing... Ignoring them."
                    )
                    first_line = False

        return l_path_jobs

    def _get_slurm_jobs(self, status: str, force_query_individually: bool = False) -> list[str]:
        """
        Retrieve a list of SLURM job paths based on their status.

        This method queries SLURM to get the job IDs and their statuses for the current user.
        It then attempts to map these job IDs to their corresponding paths using an internal
        dictionary. If the dictionary is not available or does not contain the job ID, it can
        optionally query each job individually for its details.

        Args:
            status (str): The status of the jobs to retrieve. Expected values are "running" or
                "queuing".
            force_query_individually (bool, optional): If True, query each job individually for its
                details when the job ID is not found in the internal dictionary. Defaults to False.

        Returns:
            list[str]: A list of job paths corresponding to the specified status.
        """
        l_path_jobs = []
        dic_status = {"running": "RUNNING", "queuing": "PENDING"}
        username = (
            subprocess.run(["id", "-u", "-n"], capture_output=True).stdout.decode("utf-8").strip()
        )
        slurm_output = subprocess.run(
            ["squeue", "-u", f"{username}", "-t", dic_status[status]], capture_output=True
        ).stdout.decode("utf-8")

        # Get job id and details
        first_line = True
        first_missing_job = True
        for line in slurm_output.split("\n")[1:]:
            l_split = line.split()
            if len(l_split) == 0:
                break
            jobid = int(l_split[0])
            slurm_status = l_split[4]  # R or PD  # noqa: F841

            # Get path from dic_id_to_path_job if available
            if self.dic_id_to_path_job is not None:
                if jobid in self.dic_id_to_path_job:
                    l_path_jobs.append(self.dic_id_to_path_job[jobid])
                elif first_missing_job:
                    logging.warning(
                        "Warning, some jobs are queuing/running and are not in the id-job"
                        " file. They may come from another study. Ignoring them."
                    )
                    first_missing_job = False

            elif force_query_individually:
                if first_line:
                    logging.warning(
                        "Warning, some jobs are queuing/running and the id-job file is"
                        " missing... Querying them individually."
                    )
                    first_line = False
                job_details = subprocess.run(
                    ["scontrol", "show", "jobid", "-dd", f"{jobid}"], capture_output=True
                ).stdout.decode("utf-8")
                job = (
                    job_details.split("Command=")[1].split("run.sh")[0]
                    if "run.sh" in job_details
                    else job_details.split("StdOut=")[1].split("output.txt")[0]
                )
                # Only get path after study_name
                job = job.split(self.study_name)[1]
                l_path_jobs.append(f"{self.study_name}{job}")

            elif first_line:
                logging.warning(
                    "Warning, some jobs are queuing/running and the id-job file is"
                    " missing... Ignoring them."
                )
                first_line = False

        return l_path_jobs

    def querying_jobs(
        self, check_local: bool, check_htc: bool, check_slurm: bool, status: str = "running"
    ) -> list[str]:
        """
        Queries jobs from different job management systems based on the provided flags and status.

        Args:
            check_local (bool): If True, check for local jobs.
            check_htc (bool): If True, check for HTC (High Throughput Computing) jobs.
            check_slurm (bool): If True, check for SLURM jobs.
            status (str, optional): The status of the jobs to query. Defaults to "running".

        Returns:
            list[str]: A list of job paths that match the query criteria.
        """
        # sourcery skip: remove-redundant-if, remove-redundant-pass, swap-nested-ifs
        l_path_jobs = []
        if check_local:
            if status == "running":
                l_path_jobs.extend(self._get_local_jobs())
            else:
                # Always empty return as there is no queuing in local pc
                pass

        if check_htc:
            l_path_jobs.extend(self._get_condor_jobs(status))

        if check_slurm:
            l_path_jobs.extend(self._get_slurm_jobs(status))

        return l_path_jobs
