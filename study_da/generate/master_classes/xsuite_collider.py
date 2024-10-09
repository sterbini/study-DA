"""This class is used to build a Xsuite collider from a madx sequence and optics."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import copy
import json
import logging
import os
import pathlib
from typing import Any
from zipfile import ZipFile

# Import third-party modules
import numpy as np
import xmask as xm
import xtrack as xt

# Import user-defined modules and functions
from ..version_specific_files.hllhc13 import apply_crab_fix
from ..version_specific_files.hllhc13 import (
    generate_orbit_correction_setup as gen_corr_hllhc13,
)
from ..version_specific_files.hllhc16 import (
    generate_orbit_correction_setup as gen_corr_hllhc16,
)
from ..version_specific_files.runIII import (
    generate_orbit_correction_setup as gen_corr_runIII,
)
from ..version_specific_files.runIII_ions import (
    generate_orbit_correction_setup as gen_corr_runIII_ions,
)
from .scheme_utils import get_worst_bunch, load_and_check_filling_scheme
from .xsuite_leveling import compute_PU, luminosity_leveling_ip1_5

# ==================================================================================================
# --- Class definition
# ==================================================================================================


class XsuiteCollider:
    """
    XsuiteCollider is a class designed to handle the configuration and manipulation of a collider
    using the Xsuite library. It provides methods to load, configure, and tune the collider,
    as well as to perform luminosity leveling and beam-beam interaction setup.

    Attributes:
        collider_filepath (str): Path to the collider file.
        config_beambeam (dict): Configuration for beam-beam interactions.
        config_knobs_and_tuning (dict): Configuration for knobs and tuning.
        config_lumi_leveling (dict): Configuration for luminosity leveling.
        config_lumi_leveling_ip1_5 (dict or None): Configuration for luminosity leveling at IP1 and
            IP5.
        ver_hllhc_optics (float): Version of the HL-LHC optics.
        ver_lhc_run (float): Version of the LHC run.
        ions (bool): Flag indicating if ions are used.
        _dict_orbit_correction (dict or None): Dictionary for orbit correction.
        _crab (bool or None): Flag indicating if crab cavities are used.
        save_final_collider (bool): Flag indicating if the final collider should be saved.
        path_final_collider (str): Path to save the final collider.

    Methods:
        dict_orbit_correction: Property to get the dictionary for orbit correction.
        load_collider: Loads the collider from a file.
        install_beam_beam_wrapper: Installs beam-beam lenses in the collider.
        set_knobs: Sets the knobs for the collider.
        match_tune_and_chroma: Matches the tune and chromaticity of the collider.
        set_filling_and_bunch_tracked: Sets the filling scheme and tracks the bunch.
        compute_collision_from_scheme: Computes the number of collisions from the filling scheme.
        crab: Property to get the crab cavities status.
        level_all_by_separation: Levels all IPs by separation.
        level_ip1_5_by_bunch_intensity: Levels IP1 and IP5 by bunch intensity.
        level_ip2_8_by_separation: Levels IP2 and IP8 by separation.
        add_linear_coupling: Adds linear coupling to the collider.
        assert_tune_chroma_coupling: Asserts the tune, chromaticity, and coupling of the collider.
        configure_beam_beam: Configures the beam-beam interactions.
        record_final_luminosity: Records the final luminosity of the collider.
        write_collider_to_disk: Writes the collider configuration to disk.
        update_configuration_knob: Updates a specific knob in the collider.
        return_fingerprint: Returns a fingerprint of the collider's configuration.
    """

    def __init__(
        self,
        configuration: dict,
        collider_filepath: str,
        ver_hllhc_optics: float,
        ver_lhc_run: float,
        ions: bool,
    ):
        """
        Initialize the XsuiteCollider class with the given configuration and parameters.

        Args:
            configuration (dict): A dictionary containing various configuration settings.
                - config_beambeam (dict): Configuration for beam-beam interactions.
                - config_knobs_and_tuning (dict): Configuration for knobs and tuning.
                - config_lumi_leveling (dict): Configuration for luminosity leveling.
                - save_final_collider (bool): Flag to save the final collider to disk.
                - path_final_collider (str): Path to save the final collider.
                - config_lumi_leveling_ip1_5 (optional): Configuration for luminosity leveling at
                    IP1 and IP5.
            collider_filepath (str): Path to the collider file.
            ver_hllhc_optics (float): Version of the HL-LHC optics.
            ver_lhc_run (float): Version of the LHC run.
            ions (bool): Flag indicating if ions are used.
        """
        # Collider file path
        self.collider_filepath = collider_filepath

        # Configuration variables
        self.config_beambeam: dict[str, Any] = configuration["config_beambeam"]
        self.config_knobs_and_tuning: dict[str, Any] = configuration["config_knobs_and_tuning"]
        self.config_lumi_leveling: dict[str, Any] = configuration["config_lumi_leveling"]

        # self.config_lumi_leveling_ip1_5 will be None if not present in the configuration
        self.config_lumi_leveling_ip1_5 = configuration.get("config_lumi_leveling_ip1_5")

        # Optics version (needed to select the appropriate optics specific functions)
        self.ver_hllhc_optics: float = ver_hllhc_optics
        self.ver_lhc_run: float = ver_lhc_run
        self.ions: bool = ions
        self._dict_orbit_correction: dict | None = None

        # Crab cavities
        self._crab: bool | None = None

        # Save collider to disk
        self.save_final_collider = configuration["save_final_collider"]
        self.path_final_collider = configuration["path_final_collider"]

    @property
    def dict_orbit_correction(self) -> dict:
        """
        Generates and returns a dictionary containing orbit correction parameters.

        This method checks if the orbit correction dictionary has already been generated.
        If not, it determines the appropriate set of orbit correction parameters based on
        the version of HLLHC optics or LHC run provided.

        Returns:
            dict: A dictionary containing orbit correction parameters.

        Raises:
            ValueError: If both `ver_hllhc_optics` and `ver_lhc_run` are defined.
            ValueError: If no optics specific tools are available for the provided configuration.
        """
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

    def load_collider(self) -> xt.Multiline:
        """
        Load a collider configuration from a file.

        If the file path ends with ".zip", the file is uncompressed locally
        and the collider configuration is loaded from the uncompressed file.
        Otherwise, the collider configuration is loaded directly from the file.

        Returns:
            xt.Multiline: The loaded collider configuration.
        """
        if not self.collider_filepath.endswith(".zip"):
            return xt.Multiline.from_json(self.collider_filepath)

        # Uncompress file locally
        logging.info(f"Unzipping {self.collider_filepath}")
        with ZipFile(self.collider_filepath, "r") as zip_ref:
            zip_ref.extractall()
        return xt.Multiline.from_json(self.collider_filepath.split("/")[-1].replace(".zip", ""))

    def install_beam_beam_wrapper(self, collider: xt.Multiline) -> None:
        """
        This method installs beam-beam interactions in the collider with the specified
        parameters. The beam-beam lenses are initially inactive and not configured.

        Args:
            collider (xt.Multiline): The collider object where the beam-beam interactions
                will be installed.

        Returns:
            None
        """
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
        """
        Set all knobs for the collider, including crossing angles, dispersion correction,
        RF, crab cavities, experimental magnets, etc.

        Args:
            collider (xt.Multiline): The collider object to which the knob settings will be applied.

        Returns:
            None
        """
        # Set all knobs (crossing angles, dispersion correction, rf, crab cavities,
        # experimental magnets, etc.)
        for kk, vv in self.config_knobs_and_tuning["knob_settings"].items():
            collider.vars[kk] = vv

        # Crab fix (if needed)
        if self.ver_hllhc_optics is not None and self.ver_hllhc_optics == 1.3:
            apply_crab_fix(collider, self.config_knobs_and_tuning)

    def match_tune_and_chroma(
        self, collider: xt.Multiline, match_linear_coupling_to_zero: bool = True
    ) -> None:
        """
        This method adjusts the tune and chromaticity of the specified collider lines
        ("lhcb1" and "lhcb2") to the target values defined in the configuration. It also
        optionally matches the linear coupling to zero.

        Args:
            collider (xt.Multiline): The collider object containing the lines to be tuned.
            match_linear_coupling_to_zero (bool, optional): If True, linear coupling will be
                matched to zero. Defaults to True.

        Returns:
            None
        """
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

    def set_filling_and_bunch_tracked(self, ask_worst_bunch: bool = False) -> None:
        """
        Sets the filling scheme and determines the bunch to be tracked for beam-beam interactions.

        This method performs the following steps:
        1. Retrieves the filling scheme path from the configuration.
        2. Checks if the filling scheme path needs to be obtained from the template schemes.
        3. Loads and verifies the filling scheme, potentially converting it if necessary.
        4. Updates the configuration with the correct filling scheme path.
        5. Determines the number of long-range encounters to consider.
        6. If the bunch number for beam 1 is not provided, it identifies the bunch with the largest
        number of long-range interactions.
           - If `ask_worst_bunch` is True, prompts the user to confirm or provide a bunch number.
           - Otherwise, automatically selects the worst bunch.
        7. If the bunch number for beam 2 is not provided, it automatically selects the worst bunch.

        Args:
            ask_worst_bunch (bool): If True, prompts the user to confirm or provide the bunch number
                for beam 1. Defaults to False.

        Returns:
            None
        """
        # Get the filling scheme path
        filling_scheme_path = self.config_beambeam["mask_with_filling_pattern"]["pattern_fname"]

        # Check if the filling scheme path must be obtained from the template schemes
        scheme_folder = pathlib.Path(__file__).parent.parent.resolve().joinpath("filling_schemes")
        if filling_scheme_path in os.listdir(scheme_folder):
            filling_scheme_path = str(scheme_folder.joinpath(filling_scheme_path))
            self.config_beambeam["mask_with_filling_pattern"]["pattern_fname"] = filling_scheme_path

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
                filling_scheme_path, number_of_LR_to_consider=n_LR, beam="beam_1"
            )
            if ask_worst_bunch:
                while self.config_beambeam["mask_with_filling_pattern"]["i_bunch_b1"] is None:
                    bool_inp = input(
                        "The bunch number for beam 1 has not been provided. Do you want to use the"
                        " bunch with the largest number of long-range interactions? It is the bunch"
                        " number " + str(worst_bunch_b1) + " (y/n): "
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
                filling_scheme_path, number_of_LR_to_consider=n_LR, beam="beam_2"
            )
            # For beam 2, just select the worst bunch by default
            self.config_beambeam["mask_with_filling_pattern"]["i_bunch_b2"] = worst_bunch_b2

    def compute_collision_from_scheme(self) -> tuple[int, int, int]:
        """
        This method reads a filling scheme from a JSON file specified in the configuration, converts
        the filling scheme into boolean arrays for two beams, and calculates the number of
        collisions at IP1 & IP5, IP2, and IP8 by performing convolutions on the arrays.

        Returns:
            tuple[int, int, int]: A tuple containing the number of collisions at IP1 & IP5, IP2, and
                IP8 respectively.

        Raises:
            ValueError: If the filling scheme file is not in JSON format.
            AssertionError: If the length of the beam arrays is not 3564.
        """
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

        return int(n_collisions_ip1_and_5), int(n_collisions_ip2), int(n_collisions_ip8)

    @property
    def crab(self):
        """
        This method checks the configuration settings for the presence and value of the
        "on_crab1" knob. If the knob is present and its value is non-zero, it sets the
        `_crab` attribute to True, indicating that crab cavities are active. Otherwise,
        it sets `_crab` to False.

        Returns:
            bool: True if crab cavities are active, False otherwise.
        """
        if self._crab is None:
            # Get crab cavities
            self._crab = False
            if "on_crab1" in self.config_knobs_and_tuning["knob_settings"]:
                crab_val = float(self.config_knobs_and_tuning["knob_settings"]["on_crab1"])
                if abs(crab_val) > 0:
                    self._crab = True
        return self._crab

    def level_all_by_separation(
        self,
        n_collisions_ip2: int,
        n_collisions_ip8: int,
        collider: xt.Multiline,
        n_collisions_ip1_and_5: int,
    ) -> None:
        """
        This method updates the number of colliding bunches for IP1, IP2, IP5, and IP8 in the
        configuration file and performs luminosity leveling using the provided collider object.
        It also updates the separation knobs for the collider based on the new configuration.

        Args:
            n_collisions_ip2 (int): Number of collisions at interaction point 2.
            n_collisions_ip8 (int): Number of collisions at interaction point 8.
            collider (xt.Multiline): The collider object to be used for luminosity leveling.
            n_collisions_ip1_and_5 (int): Number of collisions at interaction points 1 and 5.

        Returns:
            None
        """
        # Update the number of bunches in the configuration file
        l_n_collisions = [
            n_collisions_ip1_and_5,
            n_collisions_ip2,
            n_collisions_ip1_and_5,
            n_collisions_ip8,
        ]
        for ip, n_collisions in zip(["ip1", "ip2", "ip5", "ip8"], l_n_collisions):
            if ip in self.config_lumi_leveling:
                self.config_lumi_leveling[ip]["num_colliding_bunches"] = n_collisions
            else:
                logging.warning(f"IP {ip} is not in the configuration")

        # ! Crabs are not handled in the following function
        xm.lhc.luminosity_leveling(  # type: ignore
            collider,
            config_lumi_leveling=self.config_lumi_leveling,
            config_beambeam=self.config_beambeam,
        )

        # Update configuration
        if "ip1" in self.config_lumi_leveling:
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip1"], "on_sep1")
        if "ip2" in self.config_lumi_leveling:
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip2"], "on_sep2")
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip2"], "on_sep2h")
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip2"], "on_sep2v")
        if "ip5" in self.config_lumi_leveling:
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip5"], "on_sep5")
        if "ip8" in self.config_lumi_leveling:
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip8"], "on_sep8")
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip8"], "on_sep8h")
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip8"], "on_sep8v")

    def level_ip1_5_by_bunch_intensity(
        self,
        collider: xt.Multiline,
        n_collisions_ip1_and_5: int,
    ) -> None:
        """
        This method modifies the bunch intensity to achieve the desired luminosity
        levels in IP 1 and 5. It updates the configuration with the new intensity values.

        Args:
            collider (xt.Multiline): The collider object containing the beam and lattice
                configuration.
            n_collisions_ip1_and_5 (int):
                The number of collisions in IP 1 and 5.

        Returns:
            None
        """
        # Initial intensity
        bunch_intensity = self.config_beambeam["num_particles_per_bunch"]

        # First level luminosity in IP 1/5 changing the intensity
        if (
            self.config_lumi_leveling_ip1_5 is not None
            and not self.config_lumi_leveling_ip1_5["skip_leveling"]
        ):
            logging.info("Leveling luminosity in IP 1/5 varying the intensity")
            # Update the number of bunches in the configuration file
            self.config_lumi_leveling_ip1_5["num_colliding_bunches"] = n_collisions_ip1_and_5

            # Do the levelling
            bunch_intensity = luminosity_leveling_ip1_5(
                collider,
                self.config_lumi_leveling_ip1_5,
                self.config_beambeam,
                crab=self.crab,
                cross_section=self.config_beambeam["cross_section"],
            )

        # Update the configuration
        self.config_beambeam["final_num_particles_per_bunch"] = float(bunch_intensity)

    def level_ip2_8_by_separation(
        self,
        n_collisions_ip2: int,
        n_collisions_ip8: int,
        collider: xt.Multiline,
    ) -> None:
        """
        This method updates the number of colliding bunches for IP2 and IP8 in the configuration
        file, performs luminosity leveling for the specified collider, and updates the separation
        knobs for both interaction points.

        Args:
            n_collisions_ip2 (int): The number of collisions at interaction point 2 (IP2).
            n_collisions_ip8 (int): The number of collisions at interaction point 8 (IP8).
            collider (xt.Multiline): The collider object for which the luminosity leveling is to be
                performed.

        Returns:
            None
        """
        # Update the number of bunches in the configuration file
        if "ip2" in self.config_lumi_leveling:
            self.config_lumi_leveling["ip2"]["num_colliding_bunches"] = n_collisions_ip2
        if "ip8" in self.config_lumi_leveling:
            self.config_lumi_leveling["ip8"]["num_colliding_bunches"] = n_collisions_ip8

        # Do levelling in IP2 and IP8
        xm.lhc.luminosity_leveling( # type: ignore
            collider,
            config_lumi_leveling=self.config_lumi_leveling,
            config_beambeam=self.config_beambeam,
        )

        # Update configuration
        if "ip2" in self.config_lumi_leveling:
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip2"], "on_sep2")
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip2"], "on_sep2h")
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip2"], "on_sep2v")
        if "ip8" in self.config_lumi_leveling:
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip8"], "on_sep8")
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip8"], "on_sep8h")
            self.update_configuration_knob(collider, self.config_lumi_leveling["ip8"], "on_sep8v")

    def add_linear_coupling(self, collider: xt.Multiline) -> None:
        """
        Adds linear coupling to the collider based on the version of the LHC run or HL-LHC optics.

        This method adjusts the collider variables to introduce linear coupling. The specific
        adjustments depend on the version of the LHC run or HL-LHC optics being used.

        Args:
            collider (xt.Multiline): The collider object to which linear coupling will be added.

        Returns:
            None

        Raises:
            ValueError: If the version of the optics or run is unknown.

        Notes:
            - For LHC Run 3.0, the `cmrs.b1_sq` and `cmrs.b2_sq` variables are adjusted.
            - For HL-LHC optics versions 1.6, 1.5, 1.4, and 1.3, the `c_minus_re_b1` and
            `c_minus_re_b2` variables are adjusted.
        """
        # Add linear coupling as the target in the tuning of the base collider was 0
        # (not possible to set it the target to 0.001 for now)
        if self.ver_lhc_run == 3.0:
            collider.vars["cmrs.b1_sq"] += self.config_knobs_and_tuning["delta_cmr"]
            collider.vars["cmrs.b2_sq"] += self.config_knobs_and_tuning["delta_cmr"]
        elif self.ver_hllhc_optics in [1.6, 1.5, 1.4, 1.3]:
            collider.vars["c_minus_re_b1"] += self.config_knobs_and_tuning["delta_cmr"]
            collider.vars["c_minus_re_b2"] += self.config_knobs_and_tuning["delta_cmr"]
        else:
            raise ValueError(
                f"Unknown version of the optics/run: {self.ver_hllhc_optics}, {self.ver_lhc_run}."
            )

    def assert_tune_chroma_coupling(self, collider: xt.Multiline) -> None:
        """
        Asserts that the tune, chromaticity, and linear coupling of the collider
        match the expected values specified in the configuration.

        Args:
            collider (xt.Multiline): The collider object containing the lines to be checked.

        Returns:
            None

        Raises:
            AssertionError: If any of the tune, chromaticity, or linear coupling values do not match
                the expected values within the specified tolerances.

        Notes:
            The function checks the following parameters for each line ("lhcb1" and "lhcb2"):
            - Horizontal tune (qx)
            - Vertical tune (qy)
            - Horizontal chromaticity (dqx)
            - Vertical chromaticity (dqy)
            - Linear coupling (c_minus)

        The expected values are retrieved from the `self.config_knobs_and_tuning` dictionary.
        """
        for line_name in ["lhcb1", "lhcb2"]:
            tw = collider[line_name].twiss()
            assert np.isclose(tw.qx, self.config_knobs_and_tuning["qx"][line_name], atol=1e-4), (
                f"tune_x is not correct for {line_name}. Expected"
                f" {self.config_knobs_and_tuning['qx'][line_name]}, got {tw.qx}"
            )
            assert np.isclose(tw.qy, self.config_knobs_and_tuning["qy"][line_name], atol=1e-4), (
                f"tune_y is not correct for {line_name}. Expected"
                f" {self.config_knobs_and_tuning['qy'][line_name]}, got {tw.qy}"
            )
            assert np.isclose(
                tw.dqx,
                self.config_knobs_and_tuning["dqx"][line_name],
                rtol=1e-2,
            ), (
                f"chromaticity_x is not correct for {line_name}. Expected"
                f" {self.config_knobs_and_tuning['dqx'][line_name]}, got {tw.dqx}"
            )
            assert np.isclose(
                tw.dqy,
                self.config_knobs_and_tuning["dqy"][line_name],
                rtol=1e-2,
            ), (
                f"chromaticity_y is not correct for {line_name}. Expected"
                f" {self.config_knobs_and_tuning['dqy'][line_name]}, got {tw.dqy}"
            )

            assert np.isclose(
                tw.c_minus,
                self.config_knobs_and_tuning["delta_cmr"],
                atol=5e-3,
            ), (
                f"linear coupling is not correct for {line_name}. Expected"
                f" {self.config_knobs_and_tuning['delta_cmr']}, got {tw.c_minus}"
            )

    def configure_beam_beam(self, collider: xt.Multiline) -> None:
        """
        Configures the beam-beam interactions for the collider.

        This method sets up the beam-beam interactions by configuring the number of particles per
        bunch, the horizontal emittance (nemitt_x), and the vertical emittance (nemitt_y) based on
        the provided configuration. Additionally, it configures the filling scheme mask and bunch
        numbers if a filling pattern is specified in the configuration.

        Args:
            collider (xt.Multiline): The collider object to configure.

        Returns:
            None
        """
        collider.configure_beambeam_interactions(
            num_particles=self.config_beambeam["num_particles_per_bunch"],
            nemitt_x=self.config_beambeam["nemitt_x"],
            nemitt_y=self.config_beambeam["nemitt_y"],
        )

        # Configure filling scheme mask and bunch numbers
        if "mask_with_filling_pattern" in self.config_beambeam and (
            "pattern_fname" in self.config_beambeam["mask_with_filling_pattern"]
            and self.config_beambeam["mask_with_filling_pattern"]["pattern_fname"] is not None
        ):
            fname = self.config_beambeam["mask_with_filling_pattern"]["pattern_fname"]
            with open(fname, "r") as fid:
                filling = json.load(fid)
            filling_pattern_cw = filling["beam1"]
            filling_pattern_acw = filling["beam2"]

            # Initialize bunch numbers with empty values
            i_bunch_cw = None
            i_bunch_acw = None

            # Only track bunch number if a filling pattern has been provided
            if "i_bunch_b1" in self.config_beambeam["mask_with_filling_pattern"]:
                i_bunch_cw = self.config_beambeam["mask_with_filling_pattern"]["i_bunch_b1"]
            if "i_bunch_b2" in self.config_beambeam["mask_with_filling_pattern"]:
                i_bunch_acw = self.config_beambeam["mask_with_filling_pattern"]["i_bunch_b2"]

            # Note that a bunch number must be provided if a filling pattern is provided
            # Apply filling pattern
            collider.apply_filling_pattern(
                filling_pattern_cw=filling_pattern_cw,
                filling_pattern_acw=filling_pattern_acw,
                i_bunch_cw=i_bunch_cw,
                i_bunch_acw=i_bunch_acw,
            )

    def record_final_luminosity(self, collider: xt.Multiline, l_n_collisions: list[int]) -> None:
        """
        Records the final luminosity and pile-up for specified interaction points (IPs)
        in the collider, both with and without beam-beam effects.

        Args:
            collider : (xt.Multiline): The collider object configured.
            l_n_collisions (list[int]): A list containing the number of colliding bunches for each
                IP.

        Returns:
            None
        """
        # Define IPs in which the luminosity will be computed
        l_ip = ["ip1", "ip2", "ip5", "ip8"]

        # Ensure that the final number of particles per bunch is defined, even
        # if the leveling has been done by separation
        if "final_num_particles_per_bunch" not in self.config_beambeam:
            self.config_beambeam["final_num_particles_per_bunch"] = self.config_beambeam[
                "num_particles_per_bunch"
            ]

        def _twiss_and_compute_lumi(collider, l_n_collisions):
            # Loop over each IP and record the luminosity
            twiss_b1 = collider["lhcb1"].twiss()
            twiss_b2 = collider["lhcb2"].twiss()
            l_lumi = []
            l_PU = []
            for n_col, ip in zip(l_n_collisions, l_ip):
                L = xt.lumi.luminosity_from_twiss(  # type: ignore
                    n_colliding_bunches=n_col,
                    num_particles_per_bunch=self.config_beambeam["final_num_particles_per_bunch"],
                    ip_name=ip,
                    nemitt_x=self.config_beambeam["nemitt_x"],
                    nemitt_y=self.config_beambeam["nemitt_y"],
                    sigma_z=self.config_beambeam["sigma_z"],
                    twiss_b1=twiss_b1,
                    twiss_b2=twiss_b2,
                    crab=self.crab,
                )
                PU = compute_PU(
                    L,
                    n_col,
                    twiss_b1["T_rev0"],
                    cross_section=self.config_beambeam["cross_section"],
                )

                l_lumi.append(L)
                l_PU.append(PU)

            return l_lumi, l_PU

        # Get the final luminosity in all IPs, without beam-beam
        collider.vars["beambeam_scale"] = 0
        l_lumi, l_PU = _twiss_and_compute_lumi(collider, l_n_collisions)

        # Update configuration
        for ip, L, PU in zip(l_ip, l_lumi, l_PU):
            self.config_beambeam[f"luminosity_{ip}_without_beam_beam"] = float(L)
            self.config_beambeam[f"Pile-up_{ip}_without_beam_beam"] = float(PU)

        # Get the final luminosity in all IPs, with beam-beam
        collider.vars["beambeam_scale"] = 1
        l_lumi, l_PU = _twiss_and_compute_lumi(collider, l_n_collisions)

        # Update configuration
        for ip, L, PU in zip(l_ip, l_lumi, l_PU):
            self.config_beambeam[f"luminosity_{ip}_with_beam_beam"] = float(L)
            self.config_beambeam[f"Pile-up_{ip}_with_beam_beam"] = float(PU)

    def write_collider_to_disk(self, collider, full_configuration):
        """
        Writes the collider object to disk in JSON format if the save_final_collider flag is set.

        Args:
            collider (Collider): The collider object to be saved.
            full_configuration (dict): The full configuration dictionary to be deep-copied into the
                collider's metadata.

        Returns:
            None
        """
        if self.save_final_collider:
            logging.info("Saving collider as json")
            collider.metadata = copy.deepcopy(full_configuration)
            collider.to_json(self.path_final_collider)

    @staticmethod
    def update_configuration_knob(
        collider: xt.Multiline, dictionnary: dict, knob_name: str
    ) -> None:
        """
        Updates the given dictionary with the final value of a specified knob from the collider.

        Args:
            collider (xt.Multiline): The collider object containing various variables.
            dictionnary (dict): The dictionary to be updated with the knob's final value.
            knob_name (str): The name of the knob whose value is to be retrieved and stored.

        Returns:
            None
        """
        if knob_name in collider.vars.keys():
            dictionnary[f"final_{knob_name}"] = float(collider.vars[knob_name]._value)

    @staticmethod
    def return_fingerprint(collider, line_name="lhcb1"):
        """
        Generate a detailed fingerprint of the specified collider line. Useful to compare two
        colliders.

        Args:
            collider (xt.Multiline): The collider object containing the line data.
            line_name (str): The name of the line to analyze within the collider. Default to "lhcb1".

        Returns:
            str:
                A formatted string containing detailed information about the collider line, including:
                - Installed element types
                - Tunes and chromaticity
                - Synchrotron tune and slip factor
                - Twiss parameters and phases at interaction points (IPs)
                - Dispersion and crab dispersion at IPs
                - Amplitude detuning coefficients
                - Non-linear chromaticity
                - Tunes and momentum compaction vs delta
        """
        line = collider[line_name]

        tw = line.twiss()
        tt = line.get_table()

        det = line.get_amplitude_detuning_coefficients(a0_sigmas=0.1, a1_sigmas=0.2, a2_sigmas=0.3)

        det_table = xt.Table(
            {
                "name": np.array(list(det.keys())),
                "value": np.array(list(det.values())),
            }
        )

        nl_chrom = line.get_non_linear_chromaticity(
            delta0_range=(-2e-4, 2e-4), num_delta=5, fit_order=3
        )

        out = ""

        out += f"Line: {line_name}\n"
        out += "\n"

        out += "Installed element types:\n"
        out += repr([nn for nn in sorted(list(set(tt.element_type))) if len(nn) > 0]) + "\n"
        out += "\n"

        out += f'Tunes:        Qx  = {tw["qx"]:.5f}       Qy = {tw["qy"]:.5f}\n'
        out += f"""Chromaticity: Q'x = {tw["dqx"]:.2f}     Q'y = """ + f'{tw["dqy"]:.2f}\n'
        out += f'c_minus:      {tw["c_minus"]:.5e}\n'
        out += "\n"

        out += f'Synchrotron tune: {tw["qs"]:5e}\n'
        out += f'Slip factor:      {tw["slip_factor"]:.5e}\n'
        out += "\n"

        out += "Twiss parameters and phases at IPs:\n"
        out += (
            tw.rows["ip.*"]
            .cols["name s betx bety alfx alfy mux muy"]
            .show(output=str, max_col_width=int(1e6), digits=8)
        )
        out += "\n\n"

        out += "Dispersion at IPs:\n"
        out += (
            tw.rows["ip.*"]
            .cols["name s dx dy dpx dpy"]
            .show(output=str, max_col_width=int(1e6), digits=8)
        )
        out += "\n\n"

        out += "Crab dispersion at IPs:\n"
        out += (
            tw.rows["ip.*"]
            .cols["name s dx_zeta dy_zeta dpx_zeta dpy_zeta"]
            .show(output=str, max_col_width=int(1e6), digits=8)
        )
        out += "\n\n"

        out += "Amplitude detuning coefficients:\n"
        out += det_table.show(output=str, max_col_width=int(1e6), digits=6)
        out += "\n\n"

        out += "Non-linear chromaticity:\n"
        out += f'dnqx = {list(nl_chrom["dnqx"])}\n'
        out += f'dnqy = {list(nl_chrom["dnqy"])}\n'
        out += "\n\n"

        out += "Tunes and momentum compaction vs delta:\n"
        out += nl_chrom.show(output=str, max_col_width=int(1e6), digits=6)
        out += "\n\n"

        return out
