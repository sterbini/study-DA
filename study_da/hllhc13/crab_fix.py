import xtrack as xt


def apply_crab_fix(collider: xt.Multiline, config_knobs_and_tuning: dict) -> None:
    # Fix knobs for beam 2 crabs
    if "on_crab5" in config_knobs_and_tuning["knob_settings"]:
        collider.vars["avcrab_r5b2"] = -collider.vars["avcrab_r5b2"]._get_value()
        collider.vars["ahcrab_r5b2"] = -collider.vars["ahcrab_r5b2"]._get_value()
        collider.vars["avcrab_l5b2"] = -collider.vars["avcrab_l5b2"]._get_value()
        collider.vars["ahcrab_l5b2"] = -collider.vars["ahcrab_l5b2"]._get_value()
