"""This modules contains functions used for luminosity leveling."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging

# Import third-party modules
import xtrack as xt
from scipy.optimize import minimize_scalar


# ==================================================================================================
# --- Functions used for leveling
# ==================================================================================================
def compute_PU(luminosity, num_colliding_bunches, T_rev0, cross_section):
    return luminosity / num_colliding_bunches * cross_section * T_rev0


def luminosity_leveling_ip1_5(
    collider,
    config_lumi_leveling_ip1_5,
    config_beambeam,
    crab=False,
    cross_section=81e-27,
):
    # Get Twiss
    twiss_b1 = collider["lhcb1"].twiss()
    twiss_b2 = collider["lhcb2"].twiss()

    # Get the number of colliding bunches in IP1/5
    n_colliding_IP1_5 = config_lumi_leveling_ip1_5["num_colliding_bunches"]

    # Get max intensity in IP1/5
    max_intensity_IP1_5 = float(config_lumi_leveling_ip1_5["constraints"]["max_intensity"])

    def compute_lumi(bunch_intensity):
        luminosity = xt.lumi.luminosity_from_twiss(  # type: ignore
            n_colliding_bunches=n_colliding_IP1_5,
            num_particles_per_bunch=bunch_intensity,
            ip_name="ip1",
            nemitt_x=config_beambeam["nemitt_x"],
            nemitt_y=config_beambeam["nemitt_y"],
            sigma_z=config_beambeam["sigma_z"],
            twiss_b1=twiss_b1,
            twiss_b2=twiss_b2,
            crab=crab,
        )
        return luminosity

    def f(bunch_intensity):
        luminosity = compute_lumi(bunch_intensity)

        max_PU_IP_1_5 = config_lumi_leveling_ip1_5["constraints"]["max_PU"]

        target_luminosity_IP_1_5 = config_lumi_leveling_ip1_5["luminosity"]
        PU = compute_PU(
            luminosity,
            n_colliding_IP1_5,
            twiss_b1["T_rev0"],
            cross_section,
        )

        penalty_PU = max(0, (PU - max_PU_IP_1_5) * 1e35)  # in units of 1e-35
        penalty_excess_lumi = max(
            0, (luminosity - target_luminosity_IP_1_5) * 10
        )  # in units of 1e-35 if luminosity is in units of 1e34

        return abs(luminosity - target_luminosity_IP_1_5) + penalty_PU + penalty_excess_lumi

    # Do the optimization
    res = minimize_scalar(
        f,
        bounds=(
            1e10,
            max_intensity_IP1_5,
        ),
        method="bounded",
        options={"xatol": 1e7},
    )
    if not res.success:
        logging.warning("Optimization for leveling in IP 1/5 failed. Please check the constraints.")
    else:
        print(
            f"Optimization for leveling in IP 1/5 succeeded with I={res.x:.2e} particles per bunch"
        )
    return res.x
