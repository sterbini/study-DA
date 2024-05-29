"""This modules contains functions used for luminosity leveling."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging

# Import third-party modules
import xtrack as xt
from scipy.constants import c as clight
from scipy.optimize import minimize_scalar

# ==================================================================================================
# --- Functions used for leveling
# ==================================================================================================

# TODO : Add type hints


def luminosity_leveling(
    collider, config_lumi_leveling, config_beambeam, additional_targets_lumi=None, crab=False
):
    if additional_targets_lumi is None:
        additional_targets_lumi = []
    for ip_name in config_lumi_leveling.keys():
        print(f"\n --- Leveling in {ip_name} ---")

        config_this_ip = config_lumi_leveling[ip_name]
        bump_range = config_this_ip["bump_range"]

        assert config_this_ip[
            "preserve_angles_at_ip"
        ], "Only preserve_angles_at_ip=True is supported for now"
        assert config_this_ip[
            "preserve_bump_closure"
        ], "Only preserve_bump_closure=True is supported for now"

        beta0_b1 = collider.lhcb1.particle_ref.beta0[0]
        f_rev = 1 / (collider.lhcb1.get_length() / (beta0_b1 * clight))

        targets = []
        if "luminosity" in config_this_ip.keys():
            targets.append(
                xt.TargetLuminosity(
                    ip_name=ip_name,
                    luminosity=config_this_ip["luminosity"],
                    crab=crab,
                    tol=1e30,  # 0.01 * config_this_ip["luminosity"],
                    f_rev=f_rev,
                    num_colliding_bunches=config_this_ip["num_colliding_bunches"],
                    num_particles_per_bunch=config_beambeam["num_particles_per_bunch"],
                    sigma_z=config_beambeam["sigma_z"],
                    nemitt_x=config_beambeam["nemitt_x"],
                    nemitt_y=config_beambeam["nemitt_y"],
                    log=True,
                )
            )

            # Added this line for constraints
            targets.extend(additional_targets_lumi)
        elif "separation_in_sigmas" in config_this_ip.keys():
            targets.append(
                xt.TargetSeparation(
                    ip_name=ip_name,
                    separation_norm=config_this_ip["separation_in_sigmas"],
                    tol=1e-4,  # in sigmas
                    plane=config_this_ip["plane"],
                    nemitt_x=config_beambeam["nemitt_x"],
                    nemitt_y=config_beambeam["nemitt_y"],
                )
            )
        else:
            raise ValueError("Either `luminosity` or `separation_in_sigmas` must be specified")

        if config_this_ip["impose_separation_orthogonal_to_crossing"]:
            targets.append(xt.TargetSeparationOrthogonalToCrossing(ip_name="ip8"))
        vary = [xt.VaryList(config_this_ip["knobs"], step=1e-4)]
        # Target and knobs to rematch the crossing angles and close the bumps
        for line_name in ["lhcb1", "lhcb2"]:
            targets += [
                # Preserve crossing angle
                xt.TargetList(
                    ["px", "py"], at=ip_name, line=line_name, value="preserve", tol=1e-7, scale=1e3
                ),
                # Close the bumps
                xt.TargetList(
                    ["x", "y"],
                    at=bump_range[line_name][-1],
                    line=line_name,
                    value="preserve",
                    tol=1e-5,
                    scale=1,
                ),
                xt.TargetList(
                    ["px", "py"],
                    at=bump_range[line_name][-1],
                    line=line_name,
                    value="preserve",
                    tol=1e-5,
                    scale=1e3,
                ),
            ]

        vary.append(xt.VaryList(config_this_ip["corrector_knob_names"], step=1e-7))

        # Match
        tw0 = collider.twiss(lines=["lhcb1", "lhcb2"])
        collider.match(
            lines=["lhcb1", "lhcb2"],
            start=[bump_range["lhcb1"][0], bump_range["lhcb2"][0]],
            end=[bump_range["lhcb1"][-1], bump_range["lhcb2"][-1]],
            init=tw0,
            init_at=xt.START,
            targets=targets,
            vary=vary,
        )

    return collider


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
