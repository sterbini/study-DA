"""This class is used to define and write to disk the particles distribution."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import itertools
import os

# Import third-party modules
import numpy as np
import pandas as pd

# Import user-defined modules


# ==================================================================================================
# --- Class definition
# ==================================================================================================


class ParticlesDistribution:
    """
    ParticlesDistribution class to generate and manage particle distributions.

    Attributes:
        r_min (int): Minimum radial distance.
        r_max (int): Maximum radial distance.
        n_r (int): Number of radial points.
        n_angles (int): Number of angular points.
        n_split (int): Number of splits for parallelization.
        path_distribution_folder (str): Path to the folder where distributions will be saved.

    Methods:
        __init__(configuration: dict):
            Initializes the ParticlesDistribution with the given configuration.

        get_radial_list(lower_crop: float | None = None, upper_crop: float | None = None)
            -> np.ndarray:
            Generates a list of radial distances, optionally cropped.

        get_angular_list() -> np.ndarray:
            Generates a list of angular values.

        return_distribution_as_list(split: bool = True, lower_crop: float | None = None,
            upper_crop: float | None) -> list[np.ndarray]:
            Returns the particle distribution as a list of numpy arrays, optionally split for
            parallelization.

        write_particle_distribution_to_disk(ll_particles: list[np.ndarray]) -> list[str]:
            Writes the particle distribution to disk in Parquet format and returns the list of file
            paths.
    """

    def __init__(self, configuration: dict):
        """
        Initialize the particle distribution with the given configuration.

        Args:
            configuration (dict): A dictionary containing the configuration parameters.
                - r_min (int): Minimum radius value.
                - r_max (int): Maximum radius value.
                - n_r (int): Number of radius points.
                - n_angles (int): Number of angle points.
                - n_split (int): Number of splits for parallelization.
                - path_distribution_folder (str): Path to the folder where the distribution will be
                    saved.
        """
        # Variables used to define the distribution
        self.r_min: int = configuration["r_min"]
        self.r_max: int = configuration["r_max"]
        self.n_r: int = configuration["n_r"]
        self.n_angles: int = configuration["n_angles"]

        # Variables to split the distribution for parallelization
        self.n_split: int = configuration["n_split"]

        # Variable to write the distribution to disk
        self.path_distribution_folder: str = configuration["path_distribution_folder"]

    def get_radial_list(
        self, lower_crop: float | None = None, upper_crop: float | None = None
    ) -> np.ndarray:
        """
        Generate a list of radial distances within specified bounds.

        Args:
            lower_crop (float | None): The lower bound to crop the radial distances.
                If None, no lower cropping is applied. Defaults to None.
            upper_crop (float | None): The upper bound to crop the radial distances.
                If None, no upper cropping is applied. Defaults to None.

        Returns:
            np.ndarray: An array of radial distances within the specified bounds.
        """
        radial_list = np.linspace(self.r_min, self.r_max, self.n_r, endpoint=False)
        if upper_crop:
            radial_list = radial_list[radial_list <= 7.5]
        if lower_crop:
            radial_list = radial_list[radial_list >= 2.5]
        return radial_list

    def get_angular_list(self):
        """
        Generate a list of angular values.

        This method creates a list of angular values ranging from 0 to 90 degrees,
        excluding the first and last values. The number of angles generated is
        determined by the instance variable `self.n_angles`.

        Returns:
            numpy.ndarray: An array of angular values.
        """
        return np.linspace(0, 90, self.n_angles + 2)[1:-1]

    def return_distribution_as_list(
        self, split: bool = True, lower_crop: float | None = None, upper_crop: float | None = None
    ) -> list[np.ndarray]:
        """
        Returns the particle distribution as a list of numpy arrays.

        This method generates a particle distribution by creating a Cartesian product
        of radial and angular lists. The resulting distribution can be optionally split
        into multiple parts for parallel computation.

        Args:
            split (bool): If True, the distribution is split into multiple parts.
                Defaults to True.
            lower_crop (float | None): The lower bound for cropping the radial list.
                If None, no lower cropping is applied. Defaults to None.
            upper_crop (float | None): The upper bound for cropping the radial list.
                If None, no upper cropping is applied. Defaults to None.

        Returns:
            list[np.ndarray]: A list of numpy arrays representing the particle distribution.
                If `split` is True, the list contains multiple arrays for parallel computation.
                Otherwise, the list contains a single array.
        """
        # Get radial list and angular list
        radial_list = self.get_radial_list(lower_crop=lower_crop, upper_crop=upper_crop)
        angular_list = self.get_angular_list()

        # Define particle distribution as a cartesian product of the radial and angular lists
        l_particles = np.array(
            [
                (particle_id, ii[1], ii[0])
                for particle_id, ii in enumerate(itertools.product(angular_list, radial_list))
            ]
        )

        # Potentially split the distribution to parallelize the computation
        if split:
            return list(np.array_split(l_particles, self.n_split))

        return [l_particles]

    def write_particle_distribution_to_disk(
        self, ll_particles: list[list[np.ndarray]]
    ) -> list[str]:
        """
        Writes a list of particle distributions to disk in Parquet format.

        Args:
            ll_particles (list[list[np.ndarray]]): A list of particle distributions,
            where each distribution is a list containing particle data.

        Returns:
            list[str]: A list of file paths where the particle distributions
            have been saved.

        The method creates a directory specified by `self.path_distribution_folder`
        if it does not already exist. Each particle distribution is saved as a
        Parquet file in this directory. The files are named sequentially using
        a zero-padded index (e.g., '00.parquet', '01.parquet', etc.).
        """
        # Define folder to store the distributions
        os.makedirs(self.path_distribution_folder, exist_ok=True)

        # Write the distribution to disk
        l_path_files = []
        for idx_chunk, l_particles in enumerate(ll_particles):
            path_file = f"{self.path_distribution_folder}/{idx_chunk:02}.parquet"
            pd.DataFrame(
                l_particles,
                columns=[
                    "particle_id",
                    "normalized amplitude in xy-plane",
                    "angle in xy-plane [deg]",
                ],
            ).to_parquet(path_file)
            l_path_files.append(path_file)

        return l_path_files
