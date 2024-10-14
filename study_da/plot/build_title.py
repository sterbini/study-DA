# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import logging

# Third party imports
import numpy as np

# ==================================================================================================
# --- Functions to compute latex string for the plot title
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


def get_LHC_version_str(dataframe_data):
    if "ver_hllhc_optics" in dataframe_data.columns:
        LHC_version_value = dataframe_data["ver_hllhc_optics"].unique()[0]
        return f"HL-LHC v{LHC_version_value}"
    elif "ver_lhc_run" in dataframe_data.columns:
        LHC_version_value = dataframe_data["ver_lhc_run"].unique()[0]
        return f"LHC Run {LHC_version_value}"
    else:
        logging.warning("LHC version not found in the dataframe")
        return ""


def get_energy_str(dataframe_data):
    if "beam_energy_tot_b1" in dataframe_data.columns:
        energy_value = dataframe_data["beam_energy_tot_b1"].unique()[0] / 1000
        return f"$E = {{{energy_value:.1f}}}$ $TeV$"
    else:
        logging.warning("Energy not found in the dataframe")
        return ""


def get_bunch_index_str(dataframe_data):
    if "i_bunch_b1" in dataframe_data.columns:
        bunch_index_value = dataframe_data["i_bunch_b1"].unique()[0]
        return f"Bunch {bunch_index_value}"
    else:
        logging.warning("Bunch index not found in the dataframe")
        return ""


def get_CC_crossing_str(dataframe_data):
    if "on_crab1" in dataframe_data.columns:
        CC_crossing_value = dataframe_data["on_crab1"].unique()[0]
        return f"$CC = {{{CC_crossing_value:.1f}}}$ $\mu rad$"
    else:
        logging.warning("CC crossing not found in the dataframe")
        return ""


def get_bunch_intensity_str(dataframe_data):
    if "final_num_particles_per_bunch" in dataframe_data.columns:
        bunch_intensity_value = dataframe_data["final_num_particles_per_bunch"].unique()[0]
        return f"$N_b \simeq ${latex_float(float(bunch_intensity_value))} ppb"
    elif "num_particles_per_bunch" in dataframe_data.columns:
        logging.warning(
            "final_num_particles_per_bunch not found in the dataframe. Using num_particles_per_bunch instead."
        )
        bunch_intensity_value = dataframe_data["num_particles_per_bunch"].unique()[0]
        return f"$N_b \simeq ${latex_float(float(bunch_intensity_value))} ppb"
    else:
        logging.warning("Bunch intensity not found in the dataframe")
        return ""


def get_beta_str(dataframe_data, betx_value, bety_value):
    betx_str = r"$\beta^{*}_{x,1}$"
    bety_str = r"$\beta^{*}_{y,1}$"
    return f"{betx_str}$= {{{betx_value}}}$ m, {bety_str}" + f"$= {{{bety_value}}}$" + " m"


def _get_plane_crossing_IP_1_5_str(dataframe_data, type_crossing):
    optics_file = dataframe_data["optics_file"].unique()[0]

    if "flatvh" in optics_file or type_crossing == "flatvh":
        phi_1_str = r"$\Phi/2_{1(V)}$"
        phi_5_str = r"$\Phi/2_{5(H)}$"

    # Crossing angle at IP1/5
    elif "flathv" in optics_file or type_crossing == "flathv":
        phi_1_str = r"$\Phi/2_{1(H)}$"
        phi_5_str = r"$\Phi/2_{5(V)}$"
    else:
        logging.warning(
            "Type of crossing not found in the dataframe and not provided. Using flathv."
        )
        phi_1_str = r"$\Phi/2_{1(H)}$"
        phi_5_str = r"$\Phi/2_{5(V)}$"

    return phi_1_str, phi_5_str


def _get_crossing_value_IP_1_5(dataframe_data, ip=1):
    if f"final_on_x{ip}" in dataframe_data.columns:
        return dataframe_data[f"final_on_x{ip}"].unique()[0]
    elif f"on_x{ip}" in dataframe_data.columns:
        logging.warning(f"final_on_x{ip} not found in the dataframe. Using on_x{ip} instead.")
        return dataframe_data[f"on_x{ip}"].unique()[0]
    else:
        logging.warning(f"Crossing angle at IP{ip} not found in the dataframe")
        return np.nan


def get_crossing_IP_1_5_str(dataframe_data, type_crossing):
    # Get crossing plane at IP1/5
    phi_1_str, phi_5_str = _get_plane_crossing_IP_1_5_str(dataframe_data, type_crossing)

    # Get crossing angle values at IP1 and IP5
    xing_value_IP1 = _get_crossing_value_IP_1_5(dataframe_data, ip=1)
    xing_value_IP5 = _get_crossing_value_IP_1_5(dataframe_data, ip=5)

    # Get corresponding strings
    xing_IP1_str = f"{phi_1_str}$= {{{xing_value_IP1:.0f}}}$" + " $\mu rad$"
    xing_IP5_str = f"{phi_5_str}$= {{{xing_value_IP5:.0f}}}$" + " $\mu rad$"

    return xing_IP1_str, xing_IP5_str


def get_crossing_IP_2_8_str(dataframe_data):
    # First collect crossing angle values
    dic_xing_values = {}
    for ip in [2, 8]:
        dic_xing_values[ip] = {}
        for type_angle in ["", "h", "v"]:
            if f"on_x{ip}{type_angle}_final" in dataframe_data.columns:
                xing_value = dataframe_data[f"on_x{ip}{type_angle}_final"].unique()[0]
            elif f"on_x{ip}{type_angle}" in dataframe_data.columns:
                logging.warning(
                    f"on_x{ip}{type_angle}_final not found in the dataframe. Using on_x{ip}{type_angle} instead."
                )
                xing_value = dataframe_data[f"on_x{ip}{type_angle}"].unique()[0]
            else:
                xing_value = 0
            dic_xing_values[ip][type_angle] = xing_value

    # Then create the strings
    l_xing_IP_str = []
    for ip in [2, 8]:
        if dic_xing_values[ip]["h"] != 0 and dic_xing_values[ip]["v"] == 0:
            xing_IP_str = (
                r"$\Phi/2_{"
                + f"{ip},H"
                + r"}$"
                + f"$= {{{dic_xing_values[ip]['h']:.0f}}}$ $\mu rad$"
            )
        elif dic_xing_values[ip]["h"] == 0 and dic_xing_values[ip]["v"] != 0:
            xing_IP_str = (
                r"$\Phi/2_{"
                + f"{ip},V"
                + r"}$"
                + f"$= {{{dic_xing_values[ip]['v']:.0f}}}$ $\mu rad$"
            )
        elif dic_xing_values[ip]["h"] != 0 and dic_xing_values[ip]["v"] != 0:
            logging.warning(
                f"It seems that the crossing angles at IP{ip} are not orthogonal... "
                f"Only keeping the plane with the maximum crossing angle, but you might want to double-check this."
            )
            xing_IP_str = (
                r"$\Phi/2_{"
                + f"{ip},H"
                + r"}$"
                + f"$= {{{dic_xing_values[ip]['h']:.0f}}}$ $\mu rad$"
                if dic_xing_values[ip]["h"] > dic_xing_values[ip]["v"]
                else r"$\Phi/2_{"
                + f"{ip},V"
                + r"}$"
                + f"$= {{{dic_xing_values[ip]['v']:.0f}}}$ $\mu rad$"
            )
        elif dic_xing_values[ip][""] != 0:
            xing_IP_str = (
                r"$\Phi/2_{" + f"{ip}" + r"}$" + f"$= {{{dic_xing_values[ip]['']:.0f}}}$ $\mu rad$"
            )
        else:
            logging.warning(f"Crossing angle at IP{ip} seems to be 0. Maybe double-check.")
            xing_IP_str = r"$\Phi/2_{" + f"{ip}" + r"}$" + f"$= 0$ $\mu rad$"
        l_xing_IP_str.append(xing_IP_str)

    return l_xing_IP_str


def get_bunch_length_str(dataframe_data):
    if "sigma_z" in dataframe_data.columns:
        bunch_length_value = dataframe_data["sigma_z"].unique()[0] * 100
        return f"$\sigma_{{z}} = {{{bunch_length_value}}}$ $cm$"
    else:
        logging.warning("Bunch length not found in the dataframe")
        return ""


def get_polarity_IP_2_8_str(dataframe_data):
    if (
        "on_alice_normalized" in dataframe_data.columns
        and "on_lhcb_normalized" in dataframe_data.columns
    ):
        polarity_value_IP2 = dataframe_data["on_alice_normalized"].unique()[0]
        polarity_value_IP8 = dataframe_data["on_lhcb_normalized"].unique()[0]
        return f"$polarity$ $IP_{{2/8}} = {{{polarity_value_IP2}}}/{{{polarity_value_IP8}}}$"
    else:
        logging.warning("Polarity at IP2 and IP8 not found in the dataframe")
        return ""


def get_normalized_emittance_str(dataframe_data):
    if "nemitt_x" in dataframe_data.columns:
        emittance_value = dataframe_data["nemitt_x"].unique()[0] / 1e-6
        # Round to 5 digits
        emittance_value = round(emittance_value, 5)
        return f"$\epsilon_{{n}} = {{{emittance_value}}}$ $\mu m$"
    else:
        logging.warning("Emittance not found in the dataframe")
        return ""


def get_chromaticity_str(dataframe_data):
    if "dqx_b1" in dataframe_data.columns:
        chroma_value = dataframe_data["dqx_b1"].unique()[0]
        return f"$Q' = {{{chroma_value}}}$"
    else:
        logging.warning("Chromaticity not found in the dataframe")
        return ""


def get_octupole_intensity_str(dataframe_data):
    if "i_oct_b1" in dataframe_data.columns:
        octupole_intensity_value = dataframe_data["i_oct_b1"].unique()[0]
        return f"$I_{{OCT}} = {{{octupole_intensity_value}}}$ $A$"
    else:
        logging.warning("Octupole intensity not found in the dataframe")
        return ""


def get_linear_coupling_str(dataframe_data):
    if "delta_cmr" in dataframe_data.columns:
        coupling_value = dataframe_data["delta_cmr"].unique()[0]
        return f"$C^- = {{{coupling_value}}}$"
    else:
        logging.warning("Linear coupling not found in the dataframe")
        return ""


def get_filling_scheme_str(dataframe_data):
    if "pattern_fname" in dataframe_data.columns:
        filling_scheme_value = dataframe_data["pattern_fname"].unique()[0]
        # Only keep the last part of the path, which is the filling scheme
        filling_scheme_value = filling_scheme_value.split("/")[-1]
        # Clean
        if "12inj" in filling_scheme_value:
            filling_scheme_value = filling_scheme_value.split("12inj")[0] + "12inj"
        return f"{filling_scheme_value}"
    else:
        logging.warning("Filling scheme not found in the dataframe")
        return ""


def get_tune_str(dataframe_data):
    if "qx_b1" in dataframe_data.columns and "qy_b1" in dataframe_data.columns:
        tune_h_value = dataframe_data["qx_b1"].unique()[0]
        tune_v_value = dataframe_data["qy_b1"].unique()[0]
        return f"$Q_x = {tune_h_value}$, $Q_y = {tune_v_value}$"
    else:
        logging.warning("Tune not found in the dataframe")
        return ""


def get_luminosity_at_ip_str(dataframe_data, ip, beam_beam=True):
    # sourcery skip: merge-else-if-into-elif, simplify-fstring-formatting
    unit_luminosity = "cm$^{-2}$s$^{-1}$"
    if beam_beam:
        if f"luminosity_ip{ip}_with_beam_beam" in dataframe_data.columns:
            luminosity_value = dataframe_data[f"luminosity_ip{ip}_with_beam_beam"].unique()[0]
            return f"$L_{{IP{ip}}} \simeq ${latex_float(float(luminosity_value))} {unit_luminosity}"
        else:
            logging.warning(f"Luminosity at IP{ip} with beam-beam not found in the dataframe")
            return ""
    else:
        if f"luminosity_ip{ip}_without_beam_beam" in dataframe_data.columns:
            luminosity_value = dataframe_data[f"luminosity_ip{ip}_without_beam_beam"].unique()[0]
            return f"$L_{{IP{ip}}} \simeq ${latex_float(float(luminosity_value))} {unit_luminosity}"
        else:
            logging.warning(f"Luminosity at IP{ip} without beam-beam not found in the dataframe")
            return ""


def get_PU_at_IP_str(dataframe_data, ip, beam_beam=True):
    if beam_beam:
        if f"Pile-up_ip{ip}_with_beam_beam" in dataframe_data.columns:
            PU_value = dataframe_data[f"Pile-up_ip{ip}_with_beam_beam"].unique()[0]
            return f"$PU_{{IP{ip}}} \simeq ${latex_float(float(PU_value))}"
        else:
            logging.warning(f"Pile-up at IP{ip} with beam-beam not found in the dataframe")
            return ""
    else:
        if f"Pile-up_ip{ip}_without_beam_beam" in dataframe_data.columns:
            PU_value = dataframe_data[f"Pile-up_ip{ip}_without_beam_beam"].unique()[0]
            return f"$PU_{{IP{ip}}} \simeq ${latex_float(float(PU_value))}"
        else:
            logging.warning(f"Pile-up at IP{ip} without beam-beam not found in the dataframe")
            return ""


def get_title_from_configuration(
    dataframe_data,
    betx_value=np.nan,
    bety_value=np.nan,
    type_crossing="flathv",
    display_LHC_version=True,
    display_energy=True,
    display_bunch_index=True,
    display_CC_crossing=True,
    display_bunch_intensity=True,
    display_beta=True,
    display_crossing_IP_1=True,
    display_crossing_IP_2=True,
    display_crossing_IP_5=True,
    display_crossing_IP_8=True,
    display_bunch_length=True,
    display_polarity_IP_2_8=True,
    display_emittance=True,
    display_chromaticity=True,
    display_octupole_intensity=True,
    display_coupling=True,
    display_filling_scheme=True,
    display_tune=True,
    display_luminosity_1=True,
    display_luminosity_2=True,
    display_luminosity_5=True,
    display_luminosity_8=True,
    display_PU_1=True,
    display_PU_2=True,
    display_PU_5=True,
    display_PU_8=True,
):
    # Collect all the information to display
    LHC_version_str = get_LHC_version_str(dataframe_data)
    energy_str = get_energy_str(dataframe_data)
    bunch_index_str = get_bunch_index_str(dataframe_data)
    CC_crossing_str = get_CC_crossing_str(dataframe_data)
    bunch_intensity_str = get_bunch_intensity_str(dataframe_data)
    beta_str = get_beta_str(dataframe_data, betx_value, bety_value)
    xing_IP1_str, xing_IP5_str = get_crossing_IP_1_5_str(dataframe_data, type_crossing)
    xing_IP2_str, xing_IP8_str = get_crossing_IP_2_8_str(dataframe_data)
    bunch_length_str = get_bunch_length_str(dataframe_data)
    polarity_str = get_polarity_IP_2_8_str(dataframe_data)
    emittance_str = get_normalized_emittance_str(dataframe_data)
    chromaticity_str = get_chromaticity_str(dataframe_data)
    octupole_intensity_str = get_octupole_intensity_str(dataframe_data)
    coupling_str = get_linear_coupling_str(dataframe_data)
    filling_scheme_str = get_filling_scheme_str(dataframe_data)
    tune_str = get_tune_str(dataframe_data)

    # Collect luminosity and PU strings at each IP
    dic_lumi_PU_str = {
        "with_beam_beam": {"lumi": {}, "PU": {}},
        "without_beam_beam": {"lumi": {}, "PU": {}},
    }
    for beam_beam in ["with_beam_beam", "without_beam_beam"]:
        for ip in [1, 2, 5, 8]:
            dic_lumi_PU_str[beam_beam]["lumi"][ip] = get_luminosity_at_ip_str(
                dataframe_data, ip, beam_beam=True
            )
            dic_lumi_PU_str[beam_beam]["PU"][ip] = get_PU_at_IP_str(
                dataframe_data, ip, beam_beam=True
            )

    # Make the final title (order is the same as in the past)
    title = ""
    if display_LHC_version:
        title += LHC_version_str + ". "
    if display_energy:
        title += energy_str + ". "
    if display_CC_crossing:
        title += CC_crossing_str + ". "
    if display_bunch_intensity:
        title += bunch_intensity_str + ". "
    # Jump to the next line
    title += "\n"
    if display_luminosity_1:
        title += dic_lumi_PU_str["with_beam_beam"]["lumi"][1] + ". "
    if display_PU_1:
        title += dic_lumi_PU_str["with_beam_beam"]["PU"][1] + ". "
    if display_luminosity_5:
        title += dic_lumi_PU_str["with_beam_beam"]["lumi"][5] + ". "
    if display_PU_5:
        title += dic_lumi_PU_str["with_beam_beam"]["PU"][5] + ". "
    # Jump to the next line
    title += "\n"
    if display_luminosity_2:
        title += dic_lumi_PU_str["with_beam_beam"]["lumi"][2] + ". "
    if display_PU_2:
        title += dic_lumi_PU_str["with_beam_beam"]["PU"][2] + ". "
    if display_luminosity_8:
        title += dic_lumi_PU_str["with_beam_beam"]["lumi"][8] + ". "
    if display_PU_8:
        title += dic_lumi_PU_str["with_beam_beam"]["PU"][8] + ". "
    # Jump to the next line
    title += "\n"
    if display_beta:
        title += beta_str + ". "
    if display_polarity_IP_2_8:
        title += polarity_str + ". "
    if display_bunch_length:
        title += bunch_length_str + ". "
    # Jump to the next line
    title += "\n"
    if display_crossing_IP_1:
        title += xing_IP1_str + ". "
    if display_crossing_IP_5:
        title += xing_IP5_str + ". "
    if display_crossing_IP_2:
        title += xing_IP2_str + ". "
    if display_crossing_IP_8:
        title += xing_IP8_str + ". "

    # Jump to the next line
    title += "\n"
    if display_emittance:
        title += emittance_str + ". "
    if display_chromaticity:
        title += chromaticity_str + ". "
    if display_octupole_intensity:
        title += octupole_intensity_str + ". "
    if display_coupling:
        title += coupling_str + ". "
    if display_tune:
        title += tune_str + ". "
    # Jump to the next line
    title += "\n"
    if display_filling_scheme:
        title += filling_scheme_str + ". "
    if display_bunch_index:
        title += bunch_index_str + ". "

    return title
