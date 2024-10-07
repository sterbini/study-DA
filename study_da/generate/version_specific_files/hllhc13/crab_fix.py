# ==================================================================================================
# --- Imports
# ==================================================================================================
# Local imports
import xtrack as xt


# ==================================================================================================
# --- Functions
# ==================================================================================================
def apply_crab_fix(collider: xt.Multiline, config_knobs_and_tuning: dict) -> None:
    """Apply crab fix beam 2 crabs for HLLHC13

    Args:
        collider (xt.Multiline): The Xtrack collider object
        config_knobs_and_tuning (dict): The configuration of the knobs and tuning from the
            configuration file.

    Returns:
        None
    """
    if "on_crab5" in config_knobs_and_tuning["knob_settings"]:
        collider.vars["avcrab_r5b2"] = -collider.vars["avcrab_r5b2"]._get_value()
        collider.vars["ahcrab_r5b2"] = -collider.vars["ahcrab_r5b2"]._get_value()
        collider.vars["avcrab_l5b2"] = -collider.vars["avcrab_l5b2"]._get_value()
        collider.vars["ahcrab_l5b2"] = -collider.vars["ahcrab_l5b2"]._get_value()
