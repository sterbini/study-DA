# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import logging

# Third party imports
import numpy as np

# ==================================================================================================
# --- Functions to create study plots
# ==================================================================================================


# Function to convert floats to scientific latex format
def latex_float(f, precision=3):
    float_str = "{0:.{1}g}".format(f, precision)

    # In case the float is an integer, don't use scientific notation
    if "e" not in float_str:
        return float_str

    # Otherwise, split the float into base and exponent
    base, exponent = float_str.split("e")
    return r"${0} \times 10^{{{1}}}$".format(base, int(exponent))


def get_title_from_configuration(
    conf_mad,
    conf_collider=None,
    type_crossing=None,
    betx=None,
    bety=None,
    Nb=True,
    levelling="",
    CC=False,
    display_intensity=True,
    PU=True,
    display_xing=True,
    display_tune=False,
    ignore_lumi_1_5=True,
    display_chroma=True,
    display_emit=True,
):
    # LHC version
    LHC_version = "HL-LHC v1.6"

    # Energy
    energy_value = float(conf_mad["beam_config"]["lhcb1"]["beam_energy_tot"]) / 1000
    energy = f"$E = {{{energy_value:.1f}}}$ $TeV$"

    if conf_collider is not None:
        # Levelling
        levelling = levelling
        if levelling != "":
            levelling += " ."

        # Bunch number
        bunch_number_value = conf_collider["config_beambeam"]["mask_with_filling_pattern"][
            "i_bunch_b1"
        ]
        bunch_number = f"Bunch {bunch_number_value}"

        # Crab cavities
        if CC:
            if "on_crab1" in conf_collider["config_knobs_and_tuning"]["knob_settings"]:
                if (
                    conf_collider["config_knobs_and_tuning"]["knob_settings"]["on_crab1"]
                    is not None
                ):
                    CC_value = conf_collider["config_knobs_and_tuning"]["knob_settings"]["on_crab1"]
                    crab_cavities = f"$CC = {{{CC_value:.1f}}}$ $\mu rad$. "  # type: ignore
                else:
                    crab_cavities = "CC OFF. "
            else:
                crab_cavities = "NO CC. "
        else:
            crab_cavities = ""

        # Bunch intensity
        if Nb:
            try:
                bunch_intensity_value = conf_collider["config_beambeam"][
                    "num_particles_per_bunch_after_optimization"
                ]
            except Exception:
                bunch_intensity_value = conf_collider["config_beambeam"]["num_particles_per_bunch"]
            bunch_intensity = f"$N_b \simeq ${latex_float(float(bunch_intensity_value))} ppb, "  # type: ignore
        else:
            bunch_intensity = ""

        try:
            luminosity_value_1 = conf_collider["config_beambeam"][
                "luminosity_ip1_after_optimization"
            ]
            luminosity_value_5 = conf_collider["config_beambeam"][
                "luminosity_ip5_after_optimization"
            ]
            luminosity_value_1_5 = np.mean([luminosity_value_1, luminosity_value_5])
            luminosity_value_2 = conf_collider["config_beambeam"][
                "luminosity_ip2_after_optimization"
            ]
            luminosity_value_8 = conf_collider["config_beambeam"][
                "luminosity_ip8_after_optimization"
            ]
        except:  # noqa: E722
            print("Luminosity not found in config, setting to None")
            luminosity_value_1_5 = None
            luminosity_value_2 = None
            luminosity_value_8 = None
        if luminosity_value_1_5 is not None:
            luminosity_1_5 = (
                f"$L_{{1/5}} = ${latex_float(float(luminosity_value_1_5))}" + "cm$^{-2}$s$^{-1}$, "
            )
            luminosity_2 = (
                f"$L_{{2}} = ${latex_float(float(luminosity_value_2))}" + "cm$^{-2}$s$^{-1}$, "
            )
            luminosity_8 = (
                f"$L_{{8}} = ${latex_float(float(luminosity_value_8))}" + "cm$^{-2}$s$^{-1}$"
            )
        else:
            luminosity_1_5 = ""
            luminosity_2 = ""
            luminosity_8 = ""
        if ignore_lumi_1_5:
            luminosity_1_5 = ""

        if PU:
            try:
                PU_value_1 = conf_collider["config_beambeam"]["Pile-up_ip1_5_after_optimization"]
                PU_value_5 = conf_collider["config_beambeam"]["Pile-up_ip1_5_after_optimization"]
            except:  # noqa: E722
                try:
                    PU_value_1 = conf_collider["config_beambeam"]["Pile-up_ip1_after_optimization"]
                    PU_value_5 = conf_collider["config_beambeam"]["Pile-up_ip5_after_optimization"]
                except:  # noqa: E722
                    PU_value_1 = None
                    PU_value_5 = None

            try:
                PU_value_2 = conf_collider["config_beambeam"]["Pile-up_ip2_after_optimization"]
                PU_value_8 = conf_collider["config_beambeam"]["Pile-up_ip8_after_optimization"]
            except:  # noqa: E722
                PU_value_2 = None
                PU_value_8 = None
            if PU_value_1 is not None:
                PU_1_5 = f"$PU_{{1/5}} = ${latex_float(float(PU_value_1))}, "
                PU_2 = f"$PU_{{2}} = ${latex_float(float(PU_value_2))}, "
                PU_8 = f"$PU_{{8}} = ${latex_float(float(PU_value_8))}" + ""
            else:
                PU_1_5 = ""
                PU_2 = ""
                PU_8 = ""
        else:
            PU_1_5 = ""
            PU_2 = ""
            PU_8 = ""

        # Beta star # ! Manually encoded for now
        bet1 = r"$\beta^{*}_{x,1}$"
        bet2 = r"$\beta^{*}_{y,1}$"
        beta = bet1 + f"$= {{{betx}}}$" + " m, " + bet2 + f"$= {{{bety}}}$" + " m"

        # Crossing angle at IP1/5
        if "flathv" in conf_mad["optics_file"] or type_crossing == "flathv":
            phi_1 = r"$\Phi/2_{1(H)}$"
            phi_5 = r"$\Phi/2_{5(V)}$"
        elif "flatvh" in conf_mad["optics_file"] or type_crossing == "flatvh":
            phi_1 = r"$\Phi/2_{1(V)}$"
            phi_5 = r"$\Phi/2_{5(H)}$"
        else:
            phi_1 = r"$\Phi/2_{1(H)}$"
            phi_5 = r"$\Phi/2_{5(V)}$"
        # else:
        #     raise ValueError("Optics configuration not automatized yet")
        xing_value_IP1 = conf_collider["config_knobs_and_tuning"]["knob_settings"]["on_x1"]
        xing_IP1 = phi_1 + f"$= {{{xing_value_IP1:.0f}}}$" + " $\mu rad$, "

        xing_value_IP5 = conf_collider["config_knobs_and_tuning"]["knob_settings"]["on_x5"]
        xing_IP5 = phi_5 + f"$= {{{xing_value_IP5:.0f}}}$" + " $\mu rad$, "

        if not display_xing:
            xing_IP1 = ""
            xing_IP5 = ""

        # Bunch length
        bunch_length_value = conf_collider["config_beambeam"]["sigma_z"] * 100
        bunch_length = f"$\sigma_{{z}} = {{{bunch_length_value}}}$ $cm$"

        # Crosing angle at IP8
        xing_value_IP8h = conf_collider["config_knobs_and_tuning"]["knob_settings"]["on_x8h"]
        xing_value_IP8v = conf_collider["config_knobs_and_tuning"]["knob_settings"]["on_x8v"]
        if xing_value_IP8v != 0 and xing_value_IP8h == 0:
            xing_IP8 = r"$\Phi/2_{8,V}$" + f"$= {{{xing_value_IP8v:.0f}}}$ $\mu rad$"
        elif xing_value_IP8v == 0 and xing_value_IP8h != 0:
            xing_IP8 = r"$\Phi/2_{8,H}$" + f"$= {{{xing_value_IP8h:.0f}}}$ $\mu rad$"
        else:
            raise ValueError("Optics configuration not automatized yet")

        # Crosing angle at IP2
        try:
            xing_value_IP2h = conf_collider["config_knobs_and_tuning"]["knob_settings"]["on_x2h"]
            xing_value_IP2v = conf_collider["config_knobs_and_tuning"]["knob_settings"]["on_x2v"]
        except:  # noqa: E722
            xing_value_IP2h = 0
            xing_value_IP2v = conf_collider["config_knobs_and_tuning"]["knob_settings"]["on_x2"]
        if xing_value_IP2v != 0 and xing_value_IP2h == 0:
            xing_IP2 = r"$\Phi/2_{2,V}$" + f"$= {{{xing_value_IP2v:.0f}}}$ $\mu rad$"
        elif xing_value_IP8v == 0 and xing_value_IP8h != 0:
            xing_IP2 = r"$\Phi/2_{2,H}$" + f"$= {{{xing_value_IP2h:.0f}}}$ $\mu rad$"
        else:
            raise ValueError("Optics configuration not automatized yet")

        # Polarity IP 2 and 8
        polarity_value_IP2 = conf_collider["config_knobs_and_tuning"]["knob_settings"][
            "on_alice_normalized"
        ]
        polarity_value_IP8 = conf_collider["config_knobs_and_tuning"]["knob_settings"][
            "on_lhcb_normalized"
        ]
        polarity = f"$polarity$ $IP_{{2/8}} = {{{polarity_value_IP2}}}/{{{polarity_value_IP8}}}$"

        # Normalized emittance
        emittance_value = round(conf_collider["config_beambeam"]["nemitt_x"] / 1e-6, 2)
        emittance = f"$\epsilon_{{n}} = {{{emittance_value}}}$ $\mu m$"
        if not display_emit:
            emittance = ""

        # Chromaticity
        chroma_value = conf_collider["config_knobs_and_tuning"]["dqx"]["lhcb1"]
        chroma = r"$Q'$" + f"$= {{{chroma_value}}}$"

        if not display_chroma:
            chroma = ""

        # Intensity
        if display_intensity:
            intensity_value = conf_collider["config_knobs_and_tuning"]["knob_settings"]["i_oct_b1"]
            intensity = f"$I_{{MO}} = {{{intensity_value}}}$ $A$, "
        else:
            intensity = ""

        # Linear coupling
        coupling_value = conf_collider["config_knobs_and_tuning"]["delta_cmr"]
        coupling = f"$C^- = {{{coupling_value}}}$"

        # Filling scheme
        filling_scheme_value = conf_collider["config_beambeam"]["mask_with_filling_pattern"][
            "pattern_fname"
        ].split("filling_scheme/")[1]
        if "12inj" in filling_scheme_value:
            filling_scheme_value = filling_scheme_value.split("12inj")[0] + "12inj"
        filling_scheme = f"{filling_scheme_value}"

        # Tune
        if display_tune:
            tune_h_value = conf_collider["config_knobs_and_tuning"]["qx"]["lhcb1"]
            tune_v_value = conf_collider["config_knobs_and_tuning"]["qy"]["lhcb1"]
            qx = f"$Q_x = {{{tune_h_value}}}$, "
            qy = f"$Q_y = {{{tune_v_value}}}$, "
        else:
            qx = ""
            qy = ""

        # Final title
        title = (
            LHC_version
            + ". "
            + energy
            + ". "
            + levelling
            + crab_cavities
            + bunch_intensity
            + "\n"
            + luminosity_1_5
            + luminosity_2
            + luminosity_8
            + "\n"
            + PU_1_5
            # + PU_2
            # + PU_8
            + beta
            + ", "
            + polarity
            + "\n"
            + qx
            + qy
            + xing_IP1
            + xing_IP5
            + xing_IP2
            + ", "
            + xing_IP8
            + "\n"
            + bunch_length
            + ", "
            + emittance
            + ", "
            + chroma
            + ", "
            + intensity
            + coupling
            + "\n"
            + filling_scheme
            + ". "
            + bunch_number
            + "."
        )
    else:
        title = LHC_version + ". " + energy + ". "
    return title
