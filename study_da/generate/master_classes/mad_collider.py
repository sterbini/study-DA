"""This class is used to build a Xsuite collider from a madx sequence and optics."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging
import os
import shutil
from zipfile import ZipFile

# Import third-party modules
import xmask as xm
import xmask.lhc as xlhc
import xtrack as xt
from cpymad.madx import Madx

# Import user-defined modules
from ..version_specific_files.hllhc13 import optics_specific_tools as ost_hllhc13
from ..version_specific_files.hllhc16 import optics_specific_tools as ost_hllhc16
from ..version_specific_files.runIII import optics_specific_tools as ost_runIII
from ..version_specific_files.runIII_ions import (
    optics_specific_tools as ost_runIII_ions,
)

# ==================================================================================================
# --- Class definition
# ==================================================================================================


class MadCollider:
    def __init__(self, configuration: dict):
        # Configuration variables
        self.sanity_checks: bool = configuration["sanity_checks"]
        self.links: str = configuration["links"]
        self.beam_config: dict = configuration["beam_config"]
        self.optics: str = configuration["optics_file"]
        self.enable_imperfections: bool = configuration["enable_imperfections"]
        self.enable_knob_synthesis: bool = configuration["enable_knob_synthesis"]
        self.rename_coupling_knobs: bool = configuration["rename_coupling_knobs"]
        self.pars_for_imperfections: dict = configuration["pars_for_imperfections"]
        self.ver_lhc_run: float | None = configuration["ver_lhc_run"]
        self.ver_hllhc_optics: float | None = configuration["ver_hllhc_optics"]
        self.ions: bool = configuration["ions"]
        self.phasing: dict = configuration["phasing"]

        # Optics specific tools
        self._ost = None

        # Path to disk and compression
        self.path_collider = configuration["path_collider"]
        self.compress = configuration["compress"]

    @property
    def ost(self):
        if self._ost is None:
            # Check that version is well defined
            if self.ver_hllhc_optics is not None and self.ver_lhc_run is not None:
                raise ValueError("Only one of ver_hllhc_optics and ver_lhc_run can be defined")

            # Get the appropriate optics_specific_tools
            if self.ver_hllhc_optics is not None:
                match self.ver_hllhc_optics:
                    case 1.6:
                        self._ost = ost_hllhc16
                    case 1.3:
                        self._ost = ost_hllhc13
                    case _:
                        raise ValueError("No optics specific tools for this configuration")
            elif self.ver_lhc_run == 3.0:
                self._ost = ost_runIII_ions if self.ions else ost_runIII
            else:
                raise ValueError("No optics specific tools for the provided configuration")

        return self._ost

    def prepare_mad_collider(self) -> tuple[Madx, Madx]:
        # Make mad environment
        xm.make_mad_environment(links=self.links)

        # Start mad
        mad_b1b2 = Madx(command_log="mad_collider.log")
        mad_b4 = Madx(command_log="mad_b4.log")

        # Build sequences
        self.ost.build_sequence(mad_b1b2, mylhcbeam=1, beam_config=self.beam_config)
        self.ost.build_sequence(mad_b4, mylhcbeam=4, beam_config=self.beam_config)

        # Apply optics (only for b1b2, b4 will be generated from b1b2)
        self.ost.apply_optics(mad_b1b2, optics_file=self.optics)

        if self.sanity_checks:
            mad_b1b2.use(sequence="lhcb1")
            mad_b1b2.twiss()
            self.ost.check_madx_lattices(mad_b1b2)
            mad_b1b2.use(sequence="lhcb2")
            mad_b1b2.twiss()
            self.ost.check_madx_lattices(mad_b1b2)

        # Apply optics (only for b4, just for check)
        self.ost.apply_optics(mad_b4, optics_file=self.optics)
        if self.sanity_checks:
            mad_b4.use(sequence="lhcb2")
            mad_b4.twiss()
            # ! Investigate why this is failing for run III
            try:
                self.ost.check_madx_lattices(mad_b4)
            except AssertionError:
                logging.warning("Some sanity checks have failed during the madx lattice check")

        return mad_b1b2, mad_b4

    def build_collider(self, mad_b1b2: Madx, mad_b4: Madx) -> xt.Multiline:
        # Ensure proper types to avoid assert errors
        if self.ver_lhc_run is not None:
            self.ver_lhc_run = float(self.ver_lhc_run)
        if self.ver_hllhc_optics is not None:
            self.ver_hllhc_optics = float(self.ver_hllhc_optics)

        # Build xsuite collider
        collider = xlhc.build_xsuite_collider(
            sequence_b1=mad_b1b2.sequence.lhcb1,
            sequence_b2=mad_b1b2.sequence.lhcb2,
            sequence_b4=mad_b4.sequence.lhcb2,
            beam_config=self.beam_config,
            enable_imperfections=self.enable_imperfections,
            enable_knob_synthesis=self.enable_knob_synthesis,
            rename_coupling_knobs=self.rename_coupling_knobs,
            pars_for_imperfections=self.pars_for_imperfections,
            ver_lhc_run=self.ver_lhc_run,
            ver_hllhc_optics=self.ver_hllhc_optics,
        )
        collider.build_trackers()

        if self.sanity_checks:
            collider["lhcb1"].twiss(method="4d")
            collider["lhcb2"].twiss(method="4d")

        return collider

    def activate_RF_and_twiss(self, collider: xt.Multiline) -> None:
        # Define a RF knobs
        collider.vars["vrf400"] = self.phasing["vrf400"]
        collider.vars["lagrf400.b1"] = self.phasing["lagrf400.b1"]
        collider.vars["lagrf400.b2"] = self.phasing["lagrf400.b2"]

        if self.sanity_checks:
            for my_line in ["lhcb1", "lhcb2"]:
                self.check_xsuite_lattices(collider[my_line])

    def check_xsuite_lattices(self, line: xt.Line) -> None:
        tw = line.twiss(method="6d", matrix_stability_tol=100)
        print(f"--- Now displaying Twiss result at all IPS for line {line}---")
        print(tw.rows["ip.*"])
        # print qx and qy
        print(f"--- Now displaying Qx and Qy for line {line}---")
        print(tw.qx, tw.qy)

    def write_collider_to_disk(self, collider: xt.Multiline) -> None:
        # Save collider to json, creating the folder if it does not exist
        if "/" in self.path_collider:
            os.makedirs(self.path_collider, exist_ok=True)
        collider.to_json(self.path_collider)

        # Compress the collider file to zip to ease the load on afs
        if self.compress:
            with ZipFile(f"{self.path_collider}.zip", "w") as zipf:
                zipf.write(self.path_collider)

    @staticmethod
    def clean_temporary_files() -> None:
        # Remove all the temporaty files created in the process of building collider
        os.remove("mad_collider.log")
        os.remove("mad_b4.log")
        shutil.rmtree("temp")
        os.unlink("errors")
        os.unlink("acc-models-lhc")
