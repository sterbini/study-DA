"""This class is used to build a Xsuite collider from a madx sequence and optics."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging
import time

# Import third-party modules
import numpy as np
import pandas as pd
import xobjects as xo

# ==================================================================================================
# --- Class definition
# ==================================================================================================


class XsuiteTracking:
    def __init__(self, configuration: dict, nemitt_x, nemitt_y):
        # Context parameters
        self.context_str = configuration["context"]
        self.device_number = configuration["device_number"]
        self._context = None

        # Simulation parameters
        self.beam = configuration["beam"]
        self.particle_file = configuration["particle_file"]
        self.delta_max = configuration["delta_max"]
        self.n_turns = configuration["n_turns"]

        # Beambeam parameters
        self.nemitt_x = nemitt_x
        self.nemitt_y = nemitt_y

    @property
    def context(self):
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

    def prepare_particle_distribution_for_tracking(self, collider):
        # Reset the tracker to go to GPU if needed
        if self.context_str in ["cupy", "opencl"]:
            collider.discard_trackers()
            collider.build_trackers(_context=self.context)

        particle_df = pd.read_parquet(self.particle_file)

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

    def track(self, collider, particles):
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
