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

    @property
    def radial_list(self):
        return np.linspace(self.r_min, self.r_max, self.n_r, endpoint=False)

    @property
    def angular_list(self):
        return np.linspace(0, 90, self.n_angles + 2)[1:-1]

    def return_distribution_as_list(
        self, lower_crop: float | None = None, upper_crop: float | None = None, split: bool = True
    ) -> list:
        # Define particle distribution as a cartesian product of the radial and angular lists
        particle_list = np.array(
            [
                (particle_id, ii[1], ii[0])
                for particle_id, ii in enumerate(
                    itertools.product(self.angular_list, self.radial_list)
                )
            ]
        )

        # Split distribution into several chunks for parallelization
        particle_list = [list(x) for x in np.array_split(particle_list, self.n_split)]

        # Return distribution
        return particle_list
