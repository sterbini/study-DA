"""This class is used to build a Xsuite collider from a madx sequence and optics."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import os

# Import third-party modules
import xmask as xm
from cpymad.madx import Madx

# Import user-defined modules


# ==================================================================================================
# --- Class definition
# ==================================================================================================


class MadCollider:
    def __init__(self, configuration: dict):
        # Variables used to define the distribution
        self.links: str = configuration["links"]


    def start_mad(self):
        # Make mad environment
        xm.make_mad_environment(links=self.links)
        
        # Start mad
        mad_b1b2 = Madx(command_log="mad_collider.log")
        mad_b4 = Madx(command_log="mad_b4.log")
        return mad_b1b2, mad_b4

    def build_collider_from_mad(self, sanity_checks=True):

        # Start mad
        mad_b1b2, mad_b4 = self.start_mad()

        # Build sequences
        ost.build_sequence(mad_b1b2, mylhcbeam=1)
        ost.build_sequence(mad_b4, mylhcbeam=4)

        # Apply optics (only for b1b2, b4 will be generated from b1b2)
        ost.apply_optics(mad_b1b2, optics_file=self.configuration["optics_file"])

        if sanity_checks:
            mad_b1b2.use(sequence="lhcb1")
            mad_b1b2.twiss()
            ost.check_madx_lattices(mad_b1b2)
            mad_b1b2.use(sequence="lhcb2")
            mad_b1b2.twiss()
            ost.check_madx_lattices(mad_b1b2)

        # Apply optics (only for b4, just for check)
        ost.apply_optics(mad_b4, optics_file=self.configuration["optics_file"])
        if sanity_checks:
            mad_b4.use(sequence="lhcb2")
            mad_b4.twiss()
            ost.check_madx_lattices(mad_b1b2)

        # Build xsuite collider
        collider = xlhc.build_xsuite_collider(
            sequence_b1=mad_b1b2.sequence.lhcb1,
            sequence_b2=mad_b1b2.sequence.lhcb2,
            sequence_b4=mad_b4.sequence.lhcb2,
            beam_config=self.configuration["beam_config"],
            enable_imperfections=self.configuration["enable_imperfections"],
            enable_knob_synthesis=self.configuration["enable_knob_synthesis"],
            rename_coupling_knobs=self.configuration["rename_coupling_knobs"],
            pars_for_imperfections=self.configuration["pars_for_imperfections"],
            ver_lhc_run=self.configuration["ver_lhc_run"],
            ver_hllhc_optics=self.configuration["ver_hllhc_optics"],
        )
        collider.build_trackers()

        if sanity_checks:
            collider["lhcb1"].twiss(method="4d")
            collider["lhcb2"].twiss(method="4d")
        # Return collider
        return collider


    def activate_RF_and_twiss(collider, self.configuration, sanity_checks=True):
        # Define a RF system (values are not so immportant as they're defined later)
        print("--- Now Computing Twiss assuming:")
        if self.configuration["ver_hllhc_optics"] == 1.6:
            dic_rf = {"vrf400": 16.0, "lagrf400.b1": 0.5, "lagrf400.b2": 0.5}
            for knob, val in dic_rf.items():
                print(f"    {knob} = {val}")
        elif self.configuration["ver_lhc_run"] == 3.0:
            dic_rf = {"vrf400": 12.0, "lagrf400.b1": 0.5, "lagrf400.b2": 0.0}
            for knob, val in dic_rf.items():
                print(f"    {knob} = {val}")
        else:
            raise ValueError("No RF settings for this optics")
        print("---")

        # Rebuild tracker if needed
        try:
            collider.build_trackers()
        except Exception:
            print("Skipping rebuilding tracker")

        for knob, val in dic_rf.items():
            collider.vars[knob] = val

        if sanity_checks:
            for my_line in ["lhcb1", "lhcb2"]:
                ost.check_xsuite_lattices(collider[my_line])

        return collider


    def clean():
        # Remove all the temporaty files created in the process of building collider
        os.remove("mad_collider.log")
        os.remove("mad_b4.log")
        shutil.rmtree("temp")
        os.unlink("errors")
        os.unlink("acc-models-lhc")
