"""This class is used to build a Xsuite collider from a madx sequence and optics."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import os
import shutil

# Import third-party modules
import xmask as xm
import xtrack as xt

# Import user-defined modules
from .hllhc13.orbit_correction import (
    generate_orbit_correction_setup as gen_corr_hllhc13,
)
from .hllhc16.orbit_correction import (
    generate_orbit_correction_setup as gen_corr_hllhc16,
)
from .runIII.orbit_correction import (  # type: ignore
    generate_orbit_correction_setup as gen_corr_runIII,
)
from .runIII_ions.orbit_correction import (  # type: ignore
    generate_orbit_correction_setup as gen_corr_runIII_ions,
)

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
