"""This class is used to build a Xsuite collider from a madx sequence and optics."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import os
import shutil

# Import third-party modules
import xmask as xm
import xmask.lhc as xlhc
import xtrack as xt
from cpymad.madx import Madx

from .hllhc13 import optics_specific_tools as ost_hllhc13
from .hllhc16 import optics_specific_tools as ost_hllhc16

# Import user-defined modules
from .runIII import optics_specific_tools as ost_runIII
from .runIII_ions import optics_specific_tools as ost_runIII_ions

# ==================================================================================================
# --- Class definition
# ==================================================================================================


class MadCollider:
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
                if (
                    "particle_charge" in self.beam_config["lhcb1"]
                    and self.beam_config["lhcb1"]["particle_charge"] == 82
                ):
                    self._ost = ost_runIII_ions
                else:
                    self._ost = ost_runIII
            else:
                raise ValueError("No optics specific tools for the provided configuration")

        return self._ost

    def prepare_mad_collider(self, sanity_checks: bool = True) -> tuple[Madx, Madx]:
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

        if sanity_checks:
            mad_b1b2.use(sequence="lhcb1")
            mad_b1b2.twiss()
            self.ost.check_madx_lattices(mad_b1b2)
            mad_b1b2.use(sequence="lhcb2")
            mad_b1b2.twiss()
            self.ost.check_madx_lattices(mad_b1b2)

        # Apply optics (only for b4, just for check)
        self.ost.apply_optics(mad_b4, optics_file=self.optics)
        if sanity_checks:
            mad_b4.use(sequence="lhcb2")
            mad_b4.twiss()
            self.ost.check_madx_lattices(mad_b1b2)

        return mad_b1b2, mad_b4

    def build_collider(
        self, mad_b1b2: Madx, mad_b4: Madx, sanity_checks: bool = True
    ) -> xt.Multiline:
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

        if sanity_checks:
            collider["lhcb1"].twiss(method="4d")
            collider["lhcb2"].twiss(method="4d")

        return collider

    def activate_RF_and_twiss(
        self, collider: xt.Multiline, sanity_checks: bool = True
    ) -> xt.Multiline:
        # Define a RF knobs
        collider.vars["vrf400"] = self.phasing["vrf400"]
        collider.vars["lagrf400.b1"] = self.phasing["lagrf400.b1"]
        collider.vars["lagrf400.b2"] = self.phasing["lagrf400.b2"]

        if sanity_checks:
            for my_line in ["lhcb1", "lhcb2"]:
                self.check_xsuite_lattices(collider[my_line])

        return collider

    def check_xsuite_lattices(self, line):
        tw = line.twiss(method="6d", matrix_stability_tol=100)
        print(f"--- Now displaying Twiss result at all IPS for line {line}---")
        print(tw[:, "ip.*"])
        # print qx and qy
        print(f"--- Now displaying Qx and Qy for line {line}---")
        print(tw.qx, tw.qy)

    @staticmethod
    def clean_temporary_files():
        # Remove all the temporaty files created in the process of building collider
        os.remove("mad_collider.log")
        os.remove("mad_b4.log")
        shutil.rmtree("temp")
        os.unlink("errors")
        os.unlink("acc-models-lhc")
