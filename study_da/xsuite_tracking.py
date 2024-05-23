"""This class is used to build a Xsuite collider from a madx sequence and optics."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging
import os
import shutil

# Import third-party modules
import xobjects as xo
import xtrack as xt

# ==================================================================================================
# --- Class definition
# ==================================================================================================


class XsuiteTracking:
    def __init__(self, configuration: dict):
        self.context_str = configuration["context"]
        self._context = None

    @property
    def context(self):
        if self._context is None:
            match self.context_str:
                case "cupy":
                    self._context = xo.ContextCupy()
                case "opencl":
                    self._context = xo.ContextPyopencl()
                case "cpu":
                    self._context = xo.ContextCpu()
                case _:
                    logging.warning("Context not recognized, using cpu")
                    self._context = xo.ContextCpu()
        return self._context
