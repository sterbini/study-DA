"""This class is used to build a Xsuite collider from a madx sequence and optics."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import json
import logging

# Import third-party modules
import numpy as np
import xmask as xm
import xmask.lhc as xlhc
import xtrack as xt

# Import user-defined modules and functions
from .hllhc13 import apply_crab_fix
from .hllhc13 import generate_orbit_correction_setup as gen_corr_hllhc13
from .hllhc16 import generate_orbit_correction_setup as gen_corr_hllhc16
from .runIII import generate_orbit_correction_setup as gen_corr_runIII
from .runIII_ions import generate_orbit_correction_setup as gen_corr_runIII_ions
from .scheme_utils import get_worst_bunch, load_and_check_filling_scheme
from .xsuite_leveling import luminosity_leveling, luminosity_leveling_ip1_5

# ==================================================================================================
# --- Class definition
# ==================================================================================================


class XsuiteCollider:
    def __init__(
        self, configuration: dict, ver_hllhc_optics: float, ver_lhc_run: float, ions: bool
    ):
        # Configuration variables
        self.config_beambeam: dict = configuration["config_beambeam"]
        self.config_knobs_and_tuning: dict = configuration["config_knobs_and_tuning"]
        self.config_lumi_leveling: dict = configuration["config_lumi_leveling"]

        # self.config_lumi_leveling_ip1_5 will be None if not present in the configuration
        self.config_lumi_leveling_ip1_5 = configuration.get("config_lumi_leveling_ip1_5")

        # Optics version (needed to select the appropriate optics specific functions)
        self.ver_hllhc_optics: float = ver_hllhc_optics
        self.ver_lhc_run: float = ver_lhc_run
        self.ions: bool = ions
        self._dict_orbit_correction: dict | None = None

    @property
    def dict_orbit_correction(self) -> dict:
        if self._dict_orbit_correction is None:
            # Check that version is well defined
            if self.ver_hllhc_optics is not None and self.ver_lhc_run is not None:
                raise ValueError("Only one of ver_hllhc_optics and ver_lhc_run can be defined")

            # Get the appropriate optics_specific_tools
            if self.ver_hllhc_optics is not None:
                match self.ver_hllhc_optics:
                    case 1.6:
                        self._dict_orbit_correction = gen_corr_hllhc16()
                    case 1.3:
                        self._dict_orbit_correction = gen_corr_hllhc13()
                    case _:
                        raise ValueError("No optics specific tools for this configuration")
            elif self.ver_lhc_run == 3.0:
                self._dict_orbit_correction = (
                    gen_corr_runIII_ions() if self.ions else gen_corr_runIII()
                )
            else:
                raise ValueError("No optics specific tools for the provided configuration")

        return self._dict_orbit_correction

    def install_beam_beam_wrapper(self, collider: xt.Multiline) -> None:
        # Install beam-beam lenses (inactive and not configured)
        collider.install_beambeam_interactions(
            clockwise_line="lhcb1",
            anticlockwise_line="lhcb2",
            ip_names=["ip1", "ip2", "ip5", "ip8"],
            delay_at_ips_slots=[0, 891, 0, 2670],
            num_long_range_encounters_per_side=self.config_beambeam[
                "num_long_range_encounters_per_side"
            ],
            num_slices_head_on=self.config_beambeam["num_slices_head_on"],
            harmonic_number=35640,
            bunch_spacing_buckets=self.config_beambeam["bunch_spacing_buckets"],
            sigmaz=self.config_beambeam["sigma_z"],
        )

    def set_knobs(self, collider: xt.Multiline) -> None:
        # Set all knobs (crossing angles, dispersion correction, rf, crab cavities,
        # experimental magnets, etc.)
        for kk, vv in self.config_knobs_and_tuning["knob_settings"].items():
            collider.vars[kk] = vv

        # Crab fix (if needed)
        if self.ver_hllhc_optics is not None and self.ver_hllhc_optics == 1.3:
            apply_crab_fix(collider, self.config_knobs_and_tuning)

    def match_tune_and_chroma(
        self, collider: xt.Multiline, match_linear_coupling_to_zero: bool = True
    ):
        for line_name in ["lhcb1", "lhcb2"]:
            knob_names = self.config_knobs_and_tuning["knob_names"][line_name]

            targets = {
                "qx": self.config_knobs_and_tuning["qx"][line_name],
                "qy": self.config_knobs_and_tuning["qy"][line_name],
                "dqx": self.config_knobs_and_tuning["dqx"][line_name],
                "dqy": self.config_knobs_and_tuning["dqy"][line_name],
            }

            xm.machine_tuning(
                line=collider[line_name],
                enable_closed_orbit_correction=True,
                enable_linear_coupling_correction=match_linear_coupling_to_zero,
                enable_tune_correction=True,
                enable_chromaticity_correction=True,
                knob_names=knob_names,
                targets=targets,
                line_co_ref=collider[f"{line_name}_co_ref"],
                co_corr_config=self.dict_orbit_correction[line_name],
            )

    def set_filling_and_bunch_tracked(self, ask_worst_bunch=False):
        # Get the filling scheme path
        filling_scheme_path = self.config_beambeam["mask_with_filling_pattern"]["pattern_fname"]

        # Load and check filling scheme, potentially convert it
        filling_scheme_path = load_and_check_filling_scheme(filling_scheme_path)

        # Correct filling scheme in config, as it might have been converted
        self.config_beambeam["mask_with_filling_pattern"]["pattern_fname"] = filling_scheme_path

        # Get number of LR to consider
        n_LR = self.config_beambeam["num_long_range_encounters_per_side"]["ip1"]

        # If the bunch number is None, the bunch with the largest number of long-range interactions is used
        if self.config_beambeam["mask_with_filling_pattern"]["i_bunch_b1"] is None:
            # Case the bunch number has not been provided
            worst_bunch_b1 = get_worst_bunch(
                filling_scheme_path, numberOfLRToConsider=n_LR, beam="beam_1"
            )
            if ask_worst_bunch:
                while self.config_beambeam["mask_with_filling_pattern"]["i_bunch_b1"] is None:
                    bool_inp = input(
                        "The bunch number for beam 1 has not been provided. Do you want to use the bunch"
                        " with the largest number of long-range interactions? It is the bunch number "
                        + str(worst_bunch_b1)
                        + " (y/n): "
                    )
                    if bool_inp == "y":
                        self.config_beambeam["mask_with_filling_pattern"]["i_bunch_b1"] = (
                            worst_bunch_b1
                        )
                    elif bool_inp == "n":
                        self.config_beambeam["mask_with_filling_pattern"]["i_bunch_b1"] = int(
                            input("Please enter the bunch number for beam 1: ")
                        )
            else:
                self.config_beambeam["mask_with_filling_pattern"]["i_bunch_b1"] = worst_bunch_b1

        if self.config_beambeam["mask_with_filling_pattern"]["i_bunch_b2"] is None:
            worst_bunch_b2 = get_worst_bunch(
                filling_scheme_path, numberOfLRToConsider=n_LR, beam="beam_2"
            )
            # For beam 2, just select the worst bunch by default
            self.config_beambeam["mask_with_filling_pattern"]["i_bunch_b2"] = worst_bunch_b2

        return self.config_beambeam

    def compute_collision_from_scheme(self):
        # Get the filling scheme path (in json or csv format)
        filling_scheme_path = self.config_beambeam["mask_with_filling_pattern"]["pattern_fname"]

        # Load the filling scheme
        if not filling_scheme_path.endswith(".json"):
            raise ValueError(
                f"Unknown filling scheme file format: {filling_scheme_path}. It you provided a csv"
                " file, it should have been automatically convert when running the script"
                " 001_make_folders.py. Something went wrong."
            )

        with open(filling_scheme_path, "r") as fid:
            filling_scheme = json.load(fid)

        # Extract booleans beam arrays
        array_b1 = np.array(filling_scheme["beam1"])
        array_b2 = np.array(filling_scheme["beam2"])

        # Assert that the arrays have the required length, and do the convolution
        assert len(array_b1) == len(array_b2) == 3564
        n_collisions_ip1_and_5 = array_b1 @ array_b2
        n_collisions_ip2 = np.roll(array_b1, 891) @ array_b2
        n_collisions_ip8 = np.roll(array_b1, 2670) @ array_b2

        return n_collisions_ip1_and_5, n_collisions_ip2, n_collisions_ip8

    def level_all_by_separation(
        self,
        n_collisions_ip2,
        n_collisions_ip8,
        collider,
        n_collisions_ip1_and_5,
        crab,
    ) -> None:
        # Update the number of bunches in the configuration file
        self.config_lumi_leveling["ip1"]["num_colliding_bunches"] = int(n_collisions_ip1_and_5)
        self.config_lumi_leveling["ip5"]["num_colliding_bunches"] = int(n_collisions_ip1_and_5)
        self.config_lumi_leveling["ip2"]["num_colliding_bunches"] = int(n_collisions_ip2)
        self.config_lumi_leveling["ip8"]["num_colliding_bunches"] = int(n_collisions_ip8)

        # Level by separation
        try:
            luminosity_leveling(
                collider,
                config_lumi_leveling=self.config_lumi_leveling,
                config_beambeam=self.config_beambeam,
                crab=crab,
            )
        except Exception:
            print("Leveling failed..continuing")

        self.update_knob(collider, self.config_lumi_leveling["ip1"], "on_sep1")
        self.update_knob(collider, self.config_lumi_leveling["ip2"], "on_sep2")
        self.update_knob(collider, self.config_lumi_leveling["ip2"], "on_sep2h")
        self.update_knob(collider, self.config_lumi_leveling["ip2"], "on_sep2v")
        self.update_knob(collider, self.config_lumi_leveling["ip5"], "on_sep5")
        self.update_knob(collider, self.config_lumi_leveling["ip8"], "on_sep8")
        self.update_knob(collider, self.config_lumi_leveling["ip8"], "on_sep8h")
        self.update_knob(collider, self.config_lumi_leveling["ip8"], "on_sep8v")

    def level_ip1_5_by_bunch_intensity(
        self,
        collider,
        n_collisions_ip1_and_5,
        crab,
    ):
        # Initial intensity
        bunch_intensity = self.config_beambeam["num_particles_per_bunch"]

        # First level luminosity in IP 1/5 changing the intensity
        if (
            self.config_lumi_leveling_ip1_5 is not None
            and not self.config_lumi_leveling_ip1_5["skip_leveling"]
        ):
            logging.info("Leveling luminosity in IP 1/5 varying the intensity")
            # Update the number of bunches in the configuration file
            self.config_lumi_leveling_ip1_5["num_colliding_bunches"] = int(n_collisions_ip1_and_5)

            # Do the levelling
            try:
                bunch_intensity = luminosity_leveling_ip1_5(
                    collider,
                    self.config_lumi_leveling_ip1_5,
                    self.config_beambeam,
                    crab=crab,
                    cross_section=self.config_beambeam["cross_section"],
                )
            except ValueError:
                print("There was a problem during the luminosity leveling in IP1/5... Ignoring it.")

        # Update the configuration
        self.config_beambeam["final_num_particles_per_bunch"] = float(bunch_intensity)

    def level_ip2_8_by_separation(
        self,
        n_collisions_ip2,
        n_collisions_ip8,
        collider,
        crab,
    ):
        # Update the number of bunches in the configuration file
        self.config_lumi_leveling["ip2"]["num_colliding_bunches"] = int(n_collisions_ip2)
        self.config_lumi_leveling["ip8"]["num_colliding_bunches"] = int(n_collisions_ip8)

        # Set up the constraints for lumi optimization in IP8
        additional_targets_lumi = []
        if "constraints" in self.config_lumi_leveling["ip8"]:
            for constraint in self.config_lumi_leveling["ip8"]["constraints"]:
                obs, beam, sign, val, at = constraint.split("_")
                if sign == "<":
                    ineq = xt.LessThan(float(val))
                elif sign == ">":
                    ineq = xt.GreaterThan(float(val))
                else:
                    raise ValueError(
                        f"Unsupported sign for luminosity optimization constraint: {sign}"
                    )
                target = xt.Target(obs, ineq, at=at, line=beam, tol=1e-6)
                additional_targets_lumi.append(target)

        # Then level luminosity in IP 2/8 changing the separation
        collider = luminosity_leveling(
            collider,
            config_lumi_leveling=self.config_lumi_leveling,
            config_beambeam=self.config_beambeam,
            additional_targets_lumi=additional_targets_lumi,
            crab=crab,
        )

        # Update configuration
        self.update_knob(collider, self.config_lumi_leveling["ip2"], "on_sep2")
        self.update_knob(collider, self.config_lumi_leveling["ip2"], "on_sep2h")
        self.update_knob(collider, self.config_lumi_leveling["ip2"], "on_sep2v")
        self.update_knob(collider, self.config_lumi_leveling["ip8"], "on_sep8")
        self.update_knob(collider, self.config_lumi_leveling["ip8"], "on_sep8h")
        self.update_knob(collider, self.config_lumi_leveling["ip8"], "on_sep8v")

    @staticmethod
    def update_knob(collider, dictionnary, knob_name):
        if knob_name in collider.vars.keys():
            dictionnary[f"final_{knob_name}"] = collider.vars[knob_name]._value
