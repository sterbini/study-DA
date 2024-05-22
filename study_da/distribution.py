"""This class is used to define and write to disk the particles distribution."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import itertools

# Import third-party modules
import numpy as np

# Import user-defined modules


# ==================================================================================================
# --- Class definition
# ==================================================================================================


class Distribution:
    def __init__(self, configuration: dict):
        # Variables used to define the distribution
        self.r_min: int = configuration["r_min"]
        self.r_max: int = configuration["r_max"]
        self.n_r: int = configuration["n_r"]
        self.n_angles: int = configuration["n_angles"]

        # Variables to split the distribution for parallelization
        self.n_split: int = configuration["n_split"]

    def get_radial_list(self, lower_crop: float | None = None, upper_crop: float | None = None):
        radial_list = np.linspace(self.r_min, self.r_max, self.n_r, endpoint=False)
        if upper_crop:
            radial_list = radial_list[radial_list <= 7.5]
        if lower_crop:
            radial_list = radial_list[radial_list >= 2.5]
        return radial_list

    def get_angular_list(self):
        return np.linspace(0, 90, self.n_angles + 2)[1:-1]

    def return_distribution_as_list(
        self, split: bool = True, lower_crop: float | None = None, upper_crop: float | None = None
    ) -> list:
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

        # Split the distribution to parallelize the computation
        if split:
            return list(np.array_split(l_particles, self.n_split))

        return [l_particles]
