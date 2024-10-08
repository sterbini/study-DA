"""This module contains the classes for the submission statements for the different cluster
systems."""
# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports


# ==================================================================================================
# --- Class for job submission
# ==================================================================================================
class SubmissionStatement:
    """
    A master class to represent a submission statement for job scheduling.

    Attributes:
        sub_filename (str): The name of the submission file.
        path_job_folder (str): The path to the job folder, ensuring no trailing slash.
        request_GPUs (int): The number of GPUs requested based on the context.
        slurm_queue_statement (str): The SLURM queue statement based on the context.

    Methods:
        __init__(sub_filename: str, path_job_folder: str, context: str | None):
            Initializes the SubmissionStatement with the given filename, job folder path, and
            context.
    """

    def __init__(self, sub_filename: str, path_job_folder: str, context: str | None):
        """
        Initialize the submission statement configuration.

        Args:
            sub_filename (str): The name of the submission file.
            path_job_folder (str): The path to the job folder. Trailing slash will be removed if
                present.
            context (str | None): The context for GPU configuration. If 'cupy' or 'opencl', GPU
                will be requested.

        Attributes:
            sub_filename (str): The name of the submission file.
            path_job_folder (str): The path to the job folder without trailing slash.
            request_GPUs (int): Number of GPUs requested. 1 if context is 'cupy' or 'opencl',
                otherwise 0.
            slurm_queue_statement (str): SLURM queue statement. Empty if context is 'cupy' or
                'opencl', otherwise set to '#SBATCH --partition=slurm_hpc_acc'.
        """
        self.sub_filename: str = sub_filename
        self.path_job_folder: str = (
            path_job_folder[:-1] if path_job_folder[-1] == "/" else path_job_folder
        )

        # GPU configuration
        if context in {"cupy", "opencl"}:
            self.request_GPUs: int = 1
            self.slurm_queue_statement: str = ""
        else:
            self.request_GPUs: int = 0
            self.slurm_queue_statement: str = "#SBATCH --partition=slurm_hpc_acc"


class LocalPC(SubmissionStatement):
    """
    A class to represent a local PC submission statement.

    Attributes:
        head (str): The header of the submission script.
        body (str): The body of the submission script.
        tail (str): The tail of the submission script.
        submit_command (str): The command to submit the job.

    Methods:
        __init__(sub_filename, path_job_folder, context=None): Initializes the LocalPC submission
            statement.
        get_submit_command(sub_filename): Returns the command to submit the job.
    """

    def __init__(self, sub_filename: str, path_job_folder: str, context: str | None = None):
        """
        Initializes the LocalPC submission statement.

        Args:
            sub_filename (str): The name of the submission file.
            path_job_folder (str): The path to the job folder.
            context (str, optional): The context for the submission. Defaults to None.
        """
        super().__init__(sub_filename, path_job_folder, context)

        self.head: str = "# Running on local pc"
        self.body: str = f"bash {self.path_job_folder}/run.sh &"
        self.tail: str = "# Local pc"
        self.submit_command: str = self.get_submit_command(sub_filename)

    @staticmethod
    def get_submit_command(sub_filename: str) -> str:
        """
        Returns the command to submit the job.

        Args:
            sub_filename (str): The name of the submission file.

        Returns:
            str: The command to submit the job.
        """
        return f"bash {sub_filename}"


class Slurm(SubmissionStatement):
    """
    A class to represent a SLURM submission statement.

    Attributes:
        head (str): The header of the submission script.
        body (str): The body of the submission script.
        tail (str): The tail of the submission script.
        submit_command (str): The command to submit the job.

    Methods:
        __init__(sub_filename, path_job_folder, context): Initializes the SLURM submission statement.
        get_submit_command(sub_filename): Returns the command to submit the job.
    """

    def __init__(self, sub_filename: str, path_job_folder: str, context: str | None):
        """
        Initializes the SLURM submission statement.

        Args:
            sub_filename (str): The name of the submission file.
            path_job_folder (str): The path to the job folder.
            context (str): The context for the submission.
        """
        super().__init__(sub_filename, path_job_folder, context)

        self.head: str = "# Running on SLURM "
        if self.slurm_queue_statement != "":
            queue_statement = self.slurm_queue_statement.split(" ")[1]
        else:
            queue_statement = self.slurm_queue_statement
        self.body: str = (
            f"sbatch --ntasks=2 {queue_statement} "
            f"--output=output.txt --error=error.txt "
            f"--gres=gpu:{self.request_GPUs} {self.path_job_folder}/run.sh"
        )
        self.tail: str = "# SLURM"
        self.submit_command: str = self.get_submit_command(sub_filename)

    @staticmethod
    def get_submit_command(sub_filename: str) -> str:
        """
        Returns the command to submit the job.

        Args:
            sub_filename (str): The name of the submission file.

        Returns:
            str: The command to submit the job.
        """
        return f"bash {sub_filename}"


class SlurmDocker(SubmissionStatement):
    """
    A class to represent a SLURM submission statement using Docker.

    Attributes:
        head (str): The header of the submission script.
        body (str): The body of the submission script.
        tail (str): The tail of the submission script.
        submit_command (str): The command to submit the job.

    Methods:
        __init__(sub_filename, path_job_folder, context, path_image, fix=False): Initializes the
            SLURM Docker submission statement.
        get_submit_command(sub_filename): Returns the command to submit the job.
    """

    def __init__(
        self,
        sub_filename: str,
        path_job_folder: str,
        context: str,
        path_image: str,  # type: ignore
        fix: bool = False,
    ):
        """
        Initializes the SLURM Docker submission statement.

        Args:
            sub_filename (str): The name of the submission file.
            path_job_folder (str): The path to the job folder.
            context (str): The context for the submission.
            path_image (str): The path to the Docker image.
            fix (bool, optional): A flag to apply a fix for INFN. Defaults to False.
        """
        super().__init__(sub_filename, path_job_folder, context)

        # ! Ugly fix, will need to be removed when INFN is fixed
        if fix:
            to_replace = "/storage-hpc/gpfs_data/HPC/home_recovery"
            replacement = "/home/HPC"
            self.path_job_folder: str = self.path_job_folder.replace(to_replace, replacement)
            path_image: str = path_image.replace(to_replace, replacement)
            self.sub_filename: str = self.sub_filename.replace(to_replace, replacement)
            self.str_fixed_run: str = (
                f"sed -i 's/{to_replace}/{replacement}/' {self.path_job_folder}/run.sh\n"
            )

        self.head: str = (
            "#!/bin/bash\n"
            + "# This is a SLURM submission file using Docker\n"
            + self.slurm_queue_statement
            + "\n"
            + f"#SBATCH --output={self.path_job_folder}/output.txt\n"
            + f"#SBATCH --error={self.path_job_folder}/error.txt\n"
            + "#SBATCH --ntasks=2\n"
            + f"#SBATCH --gres=gpu:{self.request_GPUs}"
        )
        self.body: str = f"singularity exec {path_image} {self.path_job_folder}/run.sh"
        self.tail: str = "# SLURM Docker"
        self.submit_command: str = self.get_submit_command(sub_filename)

    @staticmethod
    def get_submit_command(sub_filename: str) -> str:
        """
        Returns the command to submit the job.

        Args:
            sub_filename (str): The name of the submission file.

        Returns:
            str: The command to submit the job.
        """
        return f"sbatch {sub_filename}"


class HTC(SubmissionStatement):
    """
    A class to represent an HTCondor submission statement.

    Attributes:
        head (str): The header of the submission script.
        body (str): The body of the submission script.
        tail (str): The tail of the submission script.
        submit_command (str): The command to submit the job.

    Methods:
        __init__(sub_filename, path_job_folder, context, htc_flavor='espresso'):
            Initializes the HTCondor submission statement.
        get_submit_command(sub_filename): Returns the command to submit the job.
    """

    def __init__(
        self, sub_filename: str, path_job_folder: str, context: str, htc_flavor: str = "espresso"
    ):
        """
        Initializes the HTCondor submission statement.

        Args:
            sub_filename (str): The name of the submission file.
            path_job_folder (str): The path to the job folder.
            context (str): The context for the submission.
            htc_flavor (str, optional): The flavor of the HTCondor job. Defaults to "espresso".
        """
        super().__init__(sub_filename, path_job_folder, context)

        self.head: str = (
            "# This is a HTCondor submission file\n"
            + "error  = error.txt\n"
            + "output = output.txt\n"
            + "log  = log.txt"
        )
        self.body: str = (
            f"initialdir = {self.path_job_folder}\n"
            + f"executable = {self.path_job_folder}/run.sh\n"
            + f"request_GPUs = {self.request_GPUs}\n"
            + f"+JobFlavour  = {htc_flavor}\n"
            + "queue"
        )
        self.tail: str = "# HTC"
        self.submit_command: str = self.get_submit_command(sub_filename)

    @staticmethod
    def get_submit_command(sub_filename: str) -> str:
        """
        Returns the command to submit the job.

        Args:
            sub_filename (str): The name of the submission file.

        Returns:
            str: The command to submit the job.
        """
        return f"condor_submit {sub_filename}"


class HTCDocker(SubmissionStatement):
    """
    A class to represent an HTCondor submission statement using Docker.

    Attributes:
        head (str): The header of the submission script.
        body (str): The body of the submission script.
        tail (str): The tail of the submission script.
        submit_command (str): The command to submit the job.

    Methods:
        __init__(sub_filename, path_job_folder, context, path_image, htc_flavor='espresso'):
            Initializes the HTCondor Docker submission statement.
        get_submit_command(sub_filename): Returns the command to submit the job.
    """

    def __init__(
        self,
        sub_filename: str,
        path_job_folder: str,
        context: str,
        path_image: str,
        htc_flavor: str = "espresso",
    ):
        """
        Initializes the HTCondor Docker submission statement.

        Args:
            sub_filename (str): The name of the submission file.
            path_job_folder (str): The path to the job folder.
            context (str): The context for the submission.
            path_image (str): The path to the Docker image.
            htc_flavor (str, optional): The flavor of the HTCondor job. Defaults to "espresso".
        """
        super().__init__(sub_filename, path_job_folder, context)

        self.head: str = (
            "# This is a HTCondor submission file using Docker\n"
            + "error  = error.txt\n"
            + "output = output.txt\n"
            + "log  = log.txt\n"
            + "universe = vanilla\n"
            + "+SingularityImage ="
            + f' "{path_image}"'
        )
        self.body: str = (
            f"initialdir = {self.path_job_folder}\n"
            + f"executable = {self.path_job_folder}/run.sh\n"
            + f"request_GPUs = {self.request_GPUs}\n"
            + f"+JobFlavour  = {htc_flavor}\n"
            + "queue"
        )
        self.tail: str = "# HTC Docker"
        self.submit_command: str = self.get_submit_command(sub_filename)

    @staticmethod
    def get_submit_command(sub_filename: str) -> str:
        """
        Returns the command to submit the job.

        Args:
            sub_filename (str): The name of the submission file.

        Returns:
            str: The command to submit the job.
        """
        return f"condor_submit {sub_filename}"
