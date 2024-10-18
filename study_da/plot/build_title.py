"""This module provides functions to compute LaTeX strings for plot titles based on data from a
pandas DataFrame. The functions extract various parameters such as crossing type, LHC version,
energy, bunch index, crab cavity crossing angle, bunch intensity, beta functions, crossing angles
at different interaction points (IPs), bunch length, polarity, normalized emittance, chromaticity,
octupole intensity, linear coupling, filling scheme, tune, luminosity, and pile-up.

Functions:
    latex_float(f: float, precision: int = 3) -> str:

    get_crossing_type(dataframe_data: pd.DataFrame) -> str:

    get_LHC_version_str(dataframe_data: pd.DataFrame) -> str:

    get_energy_str(dataframe_data: pd.DataFrame) -> str:

    get_bunch_index_str(dataframe_data: pd.DataFrame) -> str:

    get_CC_crossing_str(dataframe_data: pd.DataFrame) -> str:

    get_bunch_intensity_str(dataframe_data: pd.DataFrame) -> str:

    get_beta_str(betx_value: float, bety_value: float) -> str:

    _get_plane_crossing_IP_1_5_str(dataframe_data: pd.DataFrame, type_crossing: str) -> tuple[str, str]:

    _get_crossing_value_IP_1_5(dataframe_data: pd.DataFrame, ip: int) -> float:

    get_crossing_IP_1_5_str(dataframe_data: pd.DataFrame, type_crossing: str) -> tuple[str, str]:

    get_crossing_IP_2_8_str(dataframe_data: pd.DataFrame) -> list[str]:

    get_bunch_length_str(dataframe_data: pd.DataFrame) -> str:

    get_polarity_IP_2_8_str(dataframe_data: pd.DataFrame) -> str:

    get_normalized_emittance_str(dataframe_data: pd.DataFrame) -> str:

    get_chromaticity_str(dataframe_data: pd.DataFrame) -> str:

    get_octupole_intensity_str(dataframe_data: pd.DataFrame) -> str:

    get_linear_coupling_str(dataframe_data: pd.DataFrame) -> str:

    get_filling_scheme_str(dataframe_data: pd.DataFrame) -> str:

    get_tune_str(dataframe_data: pd.DataFrame) -> str:

    get_luminosity_at_ip_str(dataframe_data: pd.DataFrame, ip: int, beam_beam=True) -> str:

    get_PU_at_IP_str(dataframe_data: pd.DataFrame, ip: int, beam_beam=True) -> str:

    get_title_from_configuration( # See function docstring below for arguments) -> str:
"""

# --- Imports
# ==================================================================================================
# Standard library imports
import logging
from typing import Optional

# Third party imports
import numpy as np
import pandas as pd

# ==================================================================================================
# --- Functions to compute latex string for the plot title
# ==================================================================================================


# Function to convert floats to scientific latex format
def latex_float(f: float, precision: int = 3) -> str:
    """
    Converts a float to a scientific LaTeX format string.

    Args:
        f (float): The float to convert.
        precision (int, optional): The precision of the float. Defaults to 3.

    Returns:
        str: The float in scientific LaTeX format.
    """
    float_str = "{0:.{1}g}".format(f, precision)

    # In case the float is an integer, don't use scientific notation
    if "e" not in float_str:
        return float_str

    # Otherwise, split the float into base and exponent
    base, exponent = float_str.split("e")
    return r"${0} \times 10^{{{1}}}$".format(base, int(exponent))


def get_crossing_type(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the crossing type from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing crossing type information.

    Returns:
        str: The crossing type string.
    """
    if "optics_file" in dataframe_data.columns:
        optics_file = dataframe_data["optics_file"].unique()[0]
        if "flatvh" in optics_file:
            return "flatvh"
        elif "flathv" in optics_file:
            return "flathv"

    logging.warning("Crossing type not found in the dataframe. Falling back to flathv.")
    return "flathv"


def get_LHC_version_str(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the LHC version from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing LHC version information.

    Returns:
        str: The LHC version string.
    """
    string_HL_LHC = None
    string_LHC = None
    if "ver_hllhc_optics" in dataframe_data.columns:
        ver_hllhc_optics = dataframe_data["ver_hllhc_optics"].unique()[0]
        if ver_hllhc_optics is not None and not np.isnan(ver_hllhc_optics):
            string_HL_LHC = f"HL-LHC v{ver_hllhc_optics}"
    if "ver_lhc_run" in dataframe_data.columns:
        ver_lhc_run = dataframe_data["ver_lhc_run"].unique()[0]
        if ver_lhc_run is not None and not np.isnan(ver_lhc_run):
            string_LHC = f"LHC Run {int(ver_lhc_run)}"

    if string_HL_LHC is not None and string_LHC is not None:
        raise ValueError("Both HL-LHC and LHC Run versions found in the dataframe. Please check.")
    elif string_HL_LHC is not None:
        return string_HL_LHC
    elif string_LHC is not None:
        return string_LHC
    logging.warning("LHC version not found in the dataframe")
    return ""


def get_energy_str(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the energy from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing energy information.

    Returns:
        str: The energy string.
    """
    if "beam_energy_tot_b1" in dataframe_data.columns:
        energy_value = dataframe_data["beam_energy_tot_b1"].unique()[0] / 1000
        return f"$E = {{{energy_value:.1f}}}$ $TeV$"
    else:
        logging.warning("Energy not found in the dataframe")
        return ""


def get_bunch_index_str(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the bunch index from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing bunch index information.

    Returns:
        str: The bunch index string.
    """
    if "i_bunch_b1" in dataframe_data.columns:
        bunch_index_value = dataframe_data["i_bunch_b1"].unique()[0]
        return f"Bunch {bunch_index_value}"
    else:
        logging.warning("Bunch index not found in the dataframe")
        return ""


def get_CC_crossing_str(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the crab cavity crossing angle from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing crab cavity crossing angle
            information.

    Returns:
        str: The crab cavity crossing angle string.
    """
    if "on_crab1" in dataframe_data.columns:
        CC_crossing_value = dataframe_data["on_crab1"].unique()[0]
        return f"$CC = {{{CC_crossing_value:.1f}}}$ $\mu rad$"
    else:
        logging.warning("CC crossing not found in the dataframe")
        return ""


def get_bunch_intensity_str(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the bunch intensity string from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing bunch intensity information.

    Returns:
        str: The bunch intensity string.
    """

    if "final_num_particles_per_bunch" in dataframe_data.columns:
        bunch_intensity_value = dataframe_data["final_num_particles_per_bunch"].unique()[0]
        return f"$N_b \simeq ${latex_float(float(bunch_intensity_value))} ppb"
    elif "num_particles_per_bunch" in dataframe_data.columns:
        logging.warning(
            "final_num_particles_per_bunch not found in the dataframe."
            "Using num_particles_per_bunch instead."
        )
        bunch_intensity_value = dataframe_data["num_particles_per_bunch"].unique()[0]
        return f"$N_b \simeq ${latex_float(float(bunch_intensity_value))} ppb"
    else:
        logging.warning("Bunch intensity not found in the dataframe")
        return ""


def get_beta_str(betx_value: float, bety_value: float) -> str:
    """
    Retrieves the beta functions from the dataframe.

    Args:
        betx_value (float): The value of the horizontal beta function.
        bety_value (float): The value of the vertical beta function.

    Returns:
        str: The beta function string.
    """

    betx_str = r"$\beta^{*}_{x,1}$"
    bety_str = r"$\beta^{*}_{y,1}$"
    return f"{betx_str}$= {{{betx_value}}}$ m, {bety_str}" + f"$= {{{bety_value}}}$" + " m"


def _get_plane_crossing_IP_1_5_str(
    dataframe_data: pd.DataFrame, type_crossing: str
) -> tuple[str, str]:
    """
    Retrieves the plane crossing strings for IP1 and IP5.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing plane crossing information.
        type_crossing (str): The type of crossing. Either "flathv" or "flatvh".

    Returns:
        tuple[str, str]: The plane crossing strings for IP1 and IP5.
    """
    if type_crossing == "flatvh":
        phi_1_str = r"$\Phi/2_{1(V)}$"
        phi_5_str = r"$\Phi/2_{5(H)}$"

    # Crossing angle at IP1/5
    elif type_crossing == "flathv":
        phi_1_str = r"$\Phi/2_{1(H)}$"
        phi_5_str = r"$\Phi/2_{5(V)}$"
    else:
        raise ValueError(f"Unknown crossing type: {type_crossing}. Must be flathv or flatvh.")

    return phi_1_str, phi_5_str


def _get_crossing_value_IP_1_5(dataframe_data: pd.DataFrame, ip: int) -> float:
    """
    Retrieves the crossing angle value at IP1 or IP5.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing crossing angle information.
        ip (int): The IP number.

    Returns:
        float: The crossing angle value at IP1 or IP5.
    """
    if f"final_on_x{ip}" in dataframe_data.columns:
        return dataframe_data[f"final_on_x{ip}"].unique()[0]
    elif f"on_x{ip}" in dataframe_data.columns:
        logging.warning(f"final_on_x{ip} not found in the dataframe. Using on_x{ip} instead.")
        return dataframe_data[f"on_x{ip}"].unique()[0]
    else:
        logging.warning(f"Crossing angle at IP{ip} not found in the dataframe")
        return np.nan


def get_crossing_IP_1_5_str(dataframe_data: pd.DataFrame, type_crossing: str) -> tuple[str, str]:
    """
    Retrieves the crossing angle strings for IP1 and IP5.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing crossing angle information.
        type_crossing (str): The type of crossing. Either "flathv" or "flatvh".

    Returns:
        tuple[str, str]: The crossing angle strings for IP1 and IP5.
    """
    # Get crossing plane at IP1/5
    phi_1_str, phi_5_str = _get_plane_crossing_IP_1_5_str(dataframe_data, type_crossing)

    # Get crossing angle values at IP1 and IP5
    xing_value_IP1 = _get_crossing_value_IP_1_5(dataframe_data, ip=1)
    xing_value_IP5 = _get_crossing_value_IP_1_5(dataframe_data, ip=5)

    # Get corresponding strings
    xing_IP1_str = f"{phi_1_str}$= {{{xing_value_IP1:.0f}}}$" + " $\mu rad$"
    xing_IP5_str = f"{phi_5_str}$= {{{xing_value_IP5:.0f}}}$" + " $\mu rad$"

    return xing_IP1_str, xing_IP5_str


def get_crossing_IP_2_8_str(dataframe_data: pd.DataFrame) -> list[str]:
    """
    Retrieves the crossing angle strings for IP2 and IP8.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing crossing angle information.

    Returns:
        tuple[str, str]: The crossing angle strings for IP2 and IP8.
    """
    # First collect crossing angle values
    dic_xing_values = {}
    for ip in [2, 8]:
        dic_xing_values[ip] = {}
        for type_angle in ["", "h", "v"]:
            if f"on_x{ip}{type_angle}_final" in dataframe_data.columns:
                xing_value = dataframe_data[f"on_x{ip}{type_angle}_final"].unique()[0]
            elif f"on_x{ip}{type_angle}" in dataframe_data.columns:
                logging.warning(
                    f"on_x{ip}{type_angle}_final not found in the dataframe. "
                    f"Using on_x{ip}{type_angle} instead."
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
                f"Only keeping the plane with the maximum crossing angle, but you might want to "
                f"double-check this."
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


def get_bunch_length_str(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the bunch length from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing bunch length information.

    Returns:
        str: The bunch length string.
    """
    if "sigma_z" in dataframe_data.columns:
        bunch_length_value = dataframe_data["sigma_z"].unique()[0] * 100
        return f"$\sigma_{{z}} = {{{bunch_length_value}}}$ $cm$"
    else:
        logging.warning("Bunch length not found in the dataframe")
        return ""


def get_polarity_IP_2_8_str(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the polarity at IP2 and IP8 from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing polarity information.

    Returns:
        str: The polarity string.
    """
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


def get_normalized_emittance_str(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the normalized emittance from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing normalized emittance information.

    Returns:
        str: The normalized emittance string.
    """
    if "nemitt_x" in dataframe_data.columns:
        emittance_value = dataframe_data["nemitt_x"].unique()[0] / 1e-6
        # Round to 5 digits
        emittance_value = round(emittance_value, 5)
        return f"$\epsilon_{{n}} = {{{emittance_value}}}$ $\mu m$"
    else:
        logging.warning("Emittance not found in the dataframe")
        return ""


def get_chromaticity_str(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the chromaticity from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing chromaticity information.

    Returns:
        str: The chromaticity string.
    """
    if "dqx_b1" in dataframe_data.columns:
        chroma_value = dataframe_data["dqx_b1"].unique()[0]
        return f"$Q' = {{{chroma_value}}}$"
    else:
        logging.warning("Chromaticity not found in the dataframe")
        return ""


def get_octupole_intensity_str(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the octupole intensity from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing octupole intensity information.

    Returns:
        str: The octupole intensity string.
    """
    if "i_oct_b1" in dataframe_data.columns:
        octupole_intensity_value = dataframe_data["i_oct_b1"].unique()[0]
        return f"$I_{{OCT}} = {{{octupole_intensity_value}}}$ $A$"
    else:
        logging.warning("Octupole intensity not found in the dataframe")
        return ""


def get_linear_coupling_str(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the linear coupling from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing linear coupling information.

    Returns:
        str: The linear coupling string.
    """
    if "delta_cmr" in dataframe_data.columns:
        coupling_value = dataframe_data["delta_cmr"].unique()[0]
        return f"$C^- = {{{coupling_value}}}$"
    else:
        logging.warning("Linear coupling not found in the dataframe")
        return ""


def get_filling_scheme_str(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the filling scheme from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing filling scheme information.

    Returns:
        str: The filling scheme string.
    """
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


def get_tune_str(dataframe_data: pd.DataFrame) -> str:
    """
    Retrieves the tune from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing tune information.

    Returns:
        str: The tune string.
    """
    if "qx_b1" in dataframe_data.columns and "qy_b1" in dataframe_data.columns:
        tune_h_value = dataframe_data["qx_b1"].unique()[0]
        tune_v_value = dataframe_data["qy_b1"].unique()[0]
        return f"$Q_x = {tune_h_value}$, $Q_y = {tune_v_value}$"
    else:
        logging.warning("Tune not found in the dataframe")
        return ""


def get_luminosity_at_ip_str(dataframe_data: pd.DataFrame, ip: int, beam_beam=True) -> str:
    """
    Retrieves the luminosity at a given IP from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing luminosity information.
        ip (int): The IP number.
        beam_beam (bool, optional): Whether to consider beam-beam luminosity. Defaults to True.

    Returns:
        str: The luminosity string.
    """
    # sourcery skip: merge-else-if-into-elif, simplify-fstring-formatting
    unit_luminosity = "cm$^{-2}$s$^{-1}$"
    if beam_beam:
        if f"luminosity_ip{ip}_with_beam_beam" in dataframe_data.columns:
            luminosity_value = dataframe_data[f"luminosity_ip{ip}_with_beam_beam"].unique()[0]
            return f"$L_{{{ip}}} \simeq ${latex_float(float(luminosity_value))} {unit_luminosity}"
        else:
            logging.warning(f"Luminosity at IP{ip} with beam-beam not found in the dataframe")
            return ""
    else:
        if f"luminosity_ip{ip}_without_beam_beam" in dataframe_data.columns:
            luminosity_value = dataframe_data[f"luminosity_ip{ip}_without_beam_beam"].unique()[0]
            return f"$L_{{{ip}}} \simeq ${latex_float(float(luminosity_value))} {unit_luminosity}"
        else:
            logging.warning(f"Luminosity at IP{ip} without beam-beam not found in the dataframe")
            return ""


def get_PU_at_IP_str(dataframe_data: pd.DataFrame, ip: int, beam_beam=True) -> str:
    """
    Retrieves the pile-up at a given IP from the dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing pile-up information.
        ip (int): The IP number.
        beam_beam (bool, optional): Whether to consider beam-beam pile-up. Defaults to True.

    Returns:
        str: The pile-up string.
    """
    # sourcery skip: merge-else-if-into-elif, simplify-fstring-formatting
    if beam_beam:
        if f"Pile-up_ip{ip}_with_beam_beam" in dataframe_data.columns:
            PU_value = dataframe_data[f"Pile-up_ip{ip}_with_beam_beam"].unique()[0]
            return f"$PU_{{{ip}}} \simeq ${latex_float(float(PU_value))}"
        else:
            logging.warning(f"Pile-up at IP{ip} with beam-beam not found in the dataframe")
            return ""
    else:
        if f"Pile-up_ip{ip}_without_beam_beam" in dataframe_data.columns:
            PU_value = dataframe_data[f"Pile-up_ip{ip}_without_beam_beam"].unique()[0]
            return f"$PU_{{{ip}}} \simeq ${latex_float(float(PU_value))}"
        else:
            logging.warning(f"Pile-up at IP{ip} without beam-beam not found in the dataframe")
            return ""


def get_title_from_configuration(
    dataframe_data: pd.DataFrame,
    betx_value: float = np.nan,
    bety_value: float = np.nan,
    crossing_type: Optional[str] = None,
    display_LHC_version: bool = True,
    display_energy: bool = True,
    display_bunch_index: bool = True,
    display_CC_crossing: bool = True,
    display_bunch_intensity: bool = True,
    display_beta: bool = True,
    display_crossing_IP_1: bool = True,
    display_crossing_IP_2: bool = True,
    display_crossing_IP_5: bool = True,
    display_crossing_IP_8: bool = True,
    display_bunch_length: bool = True,
    display_polarity_IP_2_8: bool = True,
    display_emittance: bool = True,
    display_chromaticity: bool = True,
    display_octupole_intensity: bool = True,
    display_coupling: bool = True,
    display_filling_scheme: bool = True,
    display_tune: bool = True,
    display_luminosity_1: bool = True,
    display_luminosity_2: bool = True,
    display_luminosity_5: bool = True,
    display_luminosity_8: bool = True,
    display_PU_1: bool = True,
    display_PU_2: bool = True,
    display_PU_5: bool = True,
    display_PU_8: bool = True,
) -> str:
    """
    Generates a title string from the configuration data.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing configuration data.
        betx_value (float, optional): The value of the horizontal beta function. Defaults to np.nan.
        bety_value (float, optional): The value of the vertical beta function. Defaults to np.nan.
        crossing_type (str, optional): The type of crossing. Defaults to "flathv".
        display_LHC_version (bool, optional): Whether to display the LHC version. Defaults to True.
        display_energy (bool, optional): Whether to display the energy. Defaults to True.
        display_bunch_index (bool, optional): Whether to display the bunch index. Defaults to True.
        display_CC_crossing (bool, optional): Whether to display the CC crossing. Defaults to True.
        display_bunch_intensity (bool, optional): Whether to display the bunch intensity. Defaults
            to True.
        display_beta (bool, optional): Whether to display the beta function. Defaults to True.
        display_crossing_IP_1 (bool, optional): Whether to display the crossing at IP1. Defaults to
            True.
        display_crossing_IP_2 (bool, optional): Whether to display the crossing at IP2. Defaults to
            True.
        display_crossing_IP_5 (bool, optional): Whether to display the crossing at IP5. Defaults to
            True.
        display_crossing_IP_8 (bool, optional): Whether to display the crossing at IP8. Defaults to
            True.
        display_bunch_length (bool, optional): Whether to display the bunch length. Defaults to
            True.
        display_polarity_IP_2_8 (bool, optional): Whether to display the polarity at IP2 and IP8.
            Defaults to True.
        display_emittance (bool, optional): Whether to display the emittance. Defaults to True.
        display_chromaticity (bool, optional): Whether to display the chromaticity.
            Defaults to True.
        display_octupole_intensity (bool, optional): Whether to display the octupole intensity.
            Defaults to True.
        display_coupling (bool, optional): Whether to display the coupling. Defaults to True.
        display_filling_scheme (bool, optional): Whether to display the filling scheme. Defaults to
            True.
        display_tune (bool, optional): Whether to display the tune. Defaults to True.
        display_luminosity_1 (bool, optional): Whether to display the luminosity at IP1. Defaults to
            True.
        display_luminosity_2 (bool, optional): Whether to display the luminosity at IP2. Defaults to
            True.
        display_luminosity_5 (bool, optional): Whether to display the luminosity at IP5. Defaults to
            True.
        display_luminosity_8 (bool, optional): Whether to display the luminosity at IP8. Defaults to
            True.
        display_PU_1 (bool, optional): Whether to display the PU at IP1. Defaults to True.
        display_PU_2 (bool, optional): Whether to display the PU at IP2. Defaults to True.
        display_PU_5 (bool, optional): Whether to display the PU at IP5. Defaults to True.
        display_PU_8 (bool, optional): Whether to display the PU at IP8. Defaults to True.

    Returns:
        str: The generated title string.
    """
    # Find out what is the crossing type
    crossing_type = get_crossing_type(dataframe_data)

    # Collect all the information to display
    LHC_version_str = get_LHC_version_str(dataframe_data)
    energy_str = get_energy_str(dataframe_data)
    bunch_index_str = get_bunch_index_str(dataframe_data)
    CC_crossing_str = get_CC_crossing_str(dataframe_data)
    bunch_intensity_str = get_bunch_intensity_str(dataframe_data)
    beta_str = get_beta_str(betx_value, bety_value)
    xing_IP1_str, xing_IP5_str = get_crossing_IP_1_5_str(dataframe_data, crossing_type)
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

    def test_if_empty_and_add_period(string: str) -> str:
        """
        Test if a string is empty and add a period if not.

        Args:
            string (str): The string to test.

        Returns:
            str: The string with a period if not empty.
        """
        return f"{string}. " if string != "" else ""

    # Make the final title (order is the same as in the past)
    title = ""
    if display_LHC_version:
        title += test_if_empty_and_add_period(LHC_version_str)
    if display_energy:
        title += test_if_empty_and_add_period(energy_str)
    if display_CC_crossing:
        title += test_if_empty_and_add_period(CC_crossing_str)
    if display_bunch_intensity:
        title += test_if_empty_and_add_period(bunch_intensity_str)
    # Jump to the next line
    title += "\n"
    if display_luminosity_1:
        title += test_if_empty_and_add_period(dic_lumi_PU_str["with_beam_beam"]["lumi"][1])
    if display_PU_1:
        title += test_if_empty_and_add_period(dic_lumi_PU_str["with_beam_beam"]["PU"][1])
    if display_luminosity_5:
        title += test_if_empty_and_add_period(dic_lumi_PU_str["with_beam_beam"]["lumi"][5])
    if display_PU_5:
        title += test_if_empty_and_add_period(dic_lumi_PU_str["with_beam_beam"]["PU"][5])
    # Jump to the next line
    title += "\n"
    if display_luminosity_2:
        title += test_if_empty_and_add_period(dic_lumi_PU_str["with_beam_beam"]["lumi"][2])
    if display_PU_2:
        title += test_if_empty_and_add_period(dic_lumi_PU_str["with_beam_beam"]["PU"][2])
    if display_luminosity_8:
        title += test_if_empty_and_add_period(dic_lumi_PU_str["with_beam_beam"]["lumi"][8])
    if display_PU_8:
        title += test_if_empty_and_add_period(dic_lumi_PU_str["with_beam_beam"]["PU"][8])
    # Jump to the next line
    title += "\n"
    if display_beta:
        title += test_if_empty_and_add_period(beta_str)
    if display_polarity_IP_2_8:
        title += test_if_empty_and_add_period(polarity_str)
    if display_bunch_length:
        title += test_if_empty_and_add_period(bunch_length_str)
    # Jump to the next line
    title += "\n"
    if display_crossing_IP_1:
        title += test_if_empty_and_add_period(xing_IP1_str)
    if display_crossing_IP_5:
        title += test_if_empty_and_add_period(xing_IP5_str)
    if display_crossing_IP_2:
        title += test_if_empty_and_add_period(xing_IP2_str)
    if display_crossing_IP_8:
        title += test_if_empty_and_add_period(xing_IP8_str)

    # Jump to the next line
    title += "\n"
    if display_emittance:
        title += test_if_empty_and_add_period(emittance_str)
    if display_chromaticity:
        title += test_if_empty_and_add_period(chromaticity_str)
    if display_octupole_intensity:
        title += test_if_empty_and_add_period(octupole_intensity_str)
    if display_coupling:
        title += test_if_empty_and_add_period(coupling_str)
    if display_tune:
        title += test_if_empty_and_add_period(tune_str)
    # Jump to the next line
    title += "\n"
    if display_filling_scheme:
        title += test_if_empty_and_add_period(filling_scheme_str)
    if display_bunch_index:
        title += test_if_empty_and_add_period(bunch_index_str)

    return title
