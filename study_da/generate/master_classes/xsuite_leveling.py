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
def compute_PU(luminosity: float, num_colliding_bunches: int, T_rev0: float, cross_section: float):
    """
    Compute the Pile-Up (PU) value.

    Args:
        luminosity (float): The luminosity of the collider.
        num_colliding_bunches (int): The number of colliding bunches.
        T_rev0 (float): The revolution time of the collider.
        cross_section (float): The cross-section value.

    Returns:
        float: The computed Pile-Up (PU) value.
    """
    return luminosity / num_colliding_bunches * cross_section * T_rev0


def luminosity_leveling_ip1_5(
    collider: xt.Multiline,
    config_lumi_leveling_ip1_5: dict,
    config_beambeam=dict,
    crab: bool = False,
    cross_section: float = 81e-27,
):
    """
    Perform luminosity leveling for interaction points IP1 and IP5.

    Args:
        collider (dict): Dictionary containing collider objects for beams 'lhcb1' and 'lhcb2'.
        config_lumi_leveling_ip1_5 (dict): Configuration dictionary for luminosity leveling at IP1
            and IP5. Must contain 'num_colliding_bunches' and 'constraints' with 'max_intensity'
            and 'max_PU'.
        config_beambeam (dict): Configuration dictionary for beam-beam parameters. Must contain
            'nemitt_x', 'nemitt_y', and 'sigma_z'.
        crab (bool): Flag to indicate if crab cavities are used. Default to False.
        cross_section (float): Cross-section value in square meters. Default to 81e-27.

    Returns:
        float: Optimized bunch intensity for leveling in IP1 and IP5.

    Raises:
        Warning: If the optimization for leveling in IP1/5 fails, a warning is logged.
    """
    # Get Twiss
    twiss_b1 = collider["lhcb1"].twiss()
    twiss_b2 = collider["lhcb2"].twiss()

    # Get the number of colliding bunches in IP1/5
    n_colliding_IP1_5 = config_lumi_leveling_ip1_5["num_colliding_bunches"]

    # Get max intensity in IP1/5
    max_intensity_IP1_5 = float(config_lumi_leveling_ip1_5["constraints"]["max_intensity"])

    def _compute_lumi(bunch_intensity):
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
        luminosity = _compute_lumi(bunch_intensity)

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
        logging.info(
            f"Optimization for leveling in IP 1/5 succeeded with I={res.x:.2e} particles per bunch"
        )
    return res.x
