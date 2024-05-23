"""This class is used to build a Xsuite collider from a madx sequence and optics."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import os
import shutil

# Import third-party modules
import xtrack as xt

# ==================================================================================================
# --- Class definition
# ==================================================================================================


class XsuiteCollider:
    def __init__(self, configuration: dict):
        # Configuration variables
        self.links: str = configuration["links"]
        self.beam_config: dict = configuration["beam_config"]
        self.optics: str = configuration["optics_file"]
        self.enable_imperfections: bool = configuration["enable_imperfections"]
        self.enable_knob_synthesis: bool = configuration["enable_knob_synthesis"]
        self.rename_coupling_knobs: bool = configuration["rename_coupling_knobs"]
        self.pars_for_imperfections: dict = configuration["pars_for_imperfections"]
        self.ver_lhc_run: float | None = configuration["ver_lhc_run"]
        self.ver_hllhc_optics: float | None = configuration["ver_hllhc_optics"]
        self.phasing: dict = configuration["phasing"]

        # Optics specific tools
        self._ost = None
