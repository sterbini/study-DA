"""This class is used to build a Xsuite collider from a madx sequence and optics."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging
import time
from typing import Any

# Import third-party modules
import numpy as np
import pandas as pd
import xobjects as xo
import xpart as xp
import xtrack as xt

# ==================================================================================================
# --- Class definition
# ==================================================================================================


class XsuiteTracking:
    """
    XsuiteTracking class for managing particle tracking simulations.

    Attributes:
        context_str (str): The context for the simulation (e.g., "cupy", "opencl", "cpu").
        device_number (int): The device number for GPU contexts.
        _context (xo.Context): The context object for the simulation.
        beam (str): The beam configuration.
        particle_file (str): The file path to the particle data.
        delta_max (float): The maximum delta value for particles.
        n_turns (int): The number of turns for the simulation.
        nemitt_x (float): The normalized emittance in the x direction.
        nemitt_y (float): The normalized emittance in the y direction.

    Methods:
        context: Get the context object for the simulation.
        prepare_particle_distribution_for_tracking: Prepare the particle distribution for tracking.
        track: Track the particles in the collider.
    """

    def __init__(self, configuration: dict, nemitt_x: float, nemitt_y: float) -> None:
        """
        Initialize the tracking configuration.

        Args:
            configuration (dict): A dictionary containing the configuration parameters.
                Expected keys:
                - "context": str, context string for the simulation.
                - "device_number": int, device number for the simulation.
                - "beam": str, beam type for the simulation.
                - "particle_file": str, path to the particle file.
                - "delta_max": float, maximum delta value for the simulation.
                - "n_turns": int, number of turns for the simulation.
            nemitt_x (float): Normalized emittance in the x-plane.
            nemitt_y (float): Normalized emittance in the y-plane.
        """
        # Context parameters
        self.context_str: str = configuration["context"]
        self.device_number: int = configuration["device_number"]
        self._context = None

        # Simulation parameters
        self.beam: str = configuration["beam"]
        self.particle_file: str = configuration["particle_file"]
        self.particle_folder: str = configuration["particle_folder"]
        self.particle_path: str = f"{self.particle_folder}/{self.particle_file}"
        self.delta_max: float = configuration["delta_max"]
        self.n_turns: int = configuration["n_turns"]

        # Beambeam parameters
        self.nemitt_x: float = nemitt_x
        self.nemitt_y: float = nemitt_y

    @property
    def context(self) -> Any:
        """
        Returns the context for the current instance. If the context is not already set,
        it initializes the context based on the `context_str` attribute. The context can
        be one of the following:

        - "cupy": Uses `xo.ContextCupy`. If `device_number` is specified, it initializes
            the context with the given device number.
        - "opencl": Uses `xo.ContextPyopencl`.
        - "cpu": Uses `xo.ContextCpu`.
        - Any other value: Logs a warning and defaults to `xo.ContextCpu`.

        If `device_number` is specified but the context is not "cupy", a warning is logged
        indicating that the device number will be ignored.

        Returns:
            Any: The initialized context.
        """
        if self._context is None:
            if self.device_number is not None and self.context_str not in ["cupy"]:
                logging.warning("Device number will be ignored since context is not cupy")
            match self.context_str:
                case "cupy":
                    if self.device_number is not None:
                        self._context = xo.ContextCupy(device=self.device_number)
                    else:
                        self._context = xo.ContextCupy()
                case "opencl":
                    self._context = xo.ContextPyopencl()
                case "cpu":
                    self._context = xo.ContextCpu()
                case _:
                    logging.warning("Context not recognized, using cpu")
                    self._context = xo.ContextCpu()
        return self._context

    def prepare_particle_distribution_for_tracking(
        self, collider: xt.Multiline
    ) -> tuple[xp.Particles, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare a particle distribution for tracking in the collider.

        This method reads particle data from a parquet file, processes the data to
        generate normalized amplitudes and angles, and then builds particles for
        tracking in the collider. If the context is set to use GPU, the collider
        trackers are reset and rebuilt accordingly.

        Args:
            collider (xt.Multiline): The collider object containing the beam and
                tracking information.

        Returns:
            tuple: A tuple containing:
                - xp.Particles: The particles ready for tracking.
                - np.ndarray: Array of particle IDs.
                - np.ndarray: Array of normalized amplitudes in the xy-plane.
                - np.ndarray: Array of angles in the xy-plane in radians.
        """
        # Reset the tracker to go to GPU if needed
        if self.context_str in ["cupy", "opencl"]:
            collider.discard_trackers()
            collider.build_trackers(_context=self.context)

        particle_df = pd.read_parquet(self.particle_path)

        r_vect = particle_df["normalized amplitude in xy-plane"].values
        theta_vect = particle_df["angle in xy-plane [deg]"].values * np.pi / 180  # type: ignore # [rad]

        A1_in_sigma = r_vect * np.cos(theta_vect)
        A2_in_sigma = r_vect * np.sin(theta_vect)

        particles = collider[self.beam].build_particles(
            x_norm=A1_in_sigma,
            y_norm=A2_in_sigma,
            delta=self.delta_max,
            scale_with_transverse_norm_emitt=(
                self.nemitt_x,
                self.nemitt_y,
            ),
            _context=self.context,
        )

        particle_id = particle_df.particle_id.values
        return particles, particle_id, r_vect, theta_vect

    def track(self, collider: xt.Multiline, particles: xp.Particles) -> dict:
        """
        Tracks particles through a collider for a specified number of turns and logs the elapsed time.

        Args:
            collider (xt.Multiline): The collider object containing the beamline to be tracked.
            particles (xp.Particles): The particles to be tracked.

        Returns:
            dict: A dictionary representation of the tracked particles.
        """
        # Optimize line for tracking
        collider[self.beam].optimize_for_tracking()

        # Track
        num_turns = self.n_turns
        a = time.time()
        collider[self.beam].track(particles, turn_by_turn_monitor=False, num_turns=num_turns)
        b = time.time()

        logging.info(f"Elapsed time: {b-a} s")
        logging.info(
            f"Elapsed time per particle per turn: {(b-a)/particles._capacity/num_turns*1e6} us"
        )

        return particles.to_dict()
