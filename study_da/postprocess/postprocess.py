"""
This module provides functions to process and analyze simulation output data.

Functions:
    get_particles_data() -> List[pd.DataFrame]:

    add_parameters_from_config() -> List[pd.DataFrame]:

    merge_and_group_by_parameters_of_interest() -> pd.DataFrame:

    aggregate_output_data() -> pd.DataFrame:

    fix_LHC_version() -> pd.DataFrame:
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import inspect
import logging
import os
from typing import Dict, List, Optional

# Third party imports
import numpy as np
import pandas as pd

# Local imports
from study_da.submit.config_jobs import ConfigJobs
from study_da.utils import load_dic_from_path, nested_get


# ==================================================================================================
# --- Functions to browse simulations folder and extract relevant observables
# ==================================================================================================
def get_particles_data(
    dic_all_jobs: Dict[str, Dict[str, List[str]]],
    absolute_path_study: str,
    generation_of_interest: int = 2,
    name_output: str = "output_particles.parquet",
) -> List[pd.DataFrame]:
    """
    Retrieves particle data from simulation output files.

    Args:
        dic_all_jobs (dict): Dictionary containing all jobs and their details.
        absolute_path_study (str): The absolute path to the study directory.
        generation_of_interest (int, optional): The generation of interest. Defaults to 2.
        name_output (str, optional): The name of the output file.
            Defaults to "output_particles.parquet".

    Returns:
        list: A list of DataFrames containing the particle data.
    """

    # Loop over all jobs and extract the output data
    l_df_output = []
    for relative_path_job, dic_job in dic_all_jobs.items():
        if dic_job["gen"] != generation_of_interest:
            continue
        absolute_path_job = os.path.join(absolute_path_study, relative_path_job)
        absolute_folder_job = os.path.dirname(absolute_path_job)
        try:
            df_output = pd.read_parquet(os.path.join(absolute_folder_job, name_output))
        except FileNotFoundError as e:
            logging.warning(f"File not found: {e}")
            continue
        except Exception as e:
            logging.warning(f"Error reading parquet file: {e}")
            continue

        # Register path of the job
        df_output["name base collider"] = relative_path_job

        # Add to the list
        l_df_output.append(df_output)

    return l_df_output


def add_parameters_from_config(
    l_df_output: List[pd.DataFrame],
    dic_parameters_of_interest: Dict[str, List[str]],
    default_path_template_parameters: bool = False,
) -> List[pd.DataFrame]:
    """
    Adds parameters from the configuration to the output data.

    Args:
        l_df_output (list): List of DataFrames containing the output data.
        dic_parameters_of_interest (dict): Dictionary of parameters of interest.
        default_path_template_parameters (bool, optional): Flag to indicate if the default path
            template parameters are used. If True, less caution is applied in the checking of the
            parameters. Defaults to False.

    Returns:
        list: A list of DataFrames with added parameters.
    """

    for df_output in l_df_output:
        # Get generation configurations as dictionnaries for parameter assignation
        dic_configuration = df_output.attrs["configuration"]

        # Select simulations parameters of interest
        for name_param, l_path_param in dic_parameters_of_interest.items():
            try:
                df_output[name_param] = nested_get(dic_configuration, l_path_param)
            except KeyError:
                # Only be verbose if the dic_parameters_of_interest has not been provided by the user
                if not default_path_template_parameters:
                    logging.warning(f"Parameter {name_param} not found in the configuration file")

    return l_df_output


def merge_and_group_by_parameters_of_interest(
    l_df_output: List[pd.DataFrame],
    l_group_by_parameters: List[str],
    only_keep_lost_particles: bool = True,
    l_parameters_to_keep: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Merges and groups the output data by parameters of interest.

    Args:
        l_df_output (list): List of DataFrames containing the output data.
        l_group_by_parameters (list): List of parameters to group by.
        only_keep_lost_particles (bool, optional): Flag to indicate if only lost particles should
            be kept. Defaults to True.
        l_parameters_to_keep (list, optional): List of parameters to keep. Defaults to None.

    Returns:
        pd.DataFrame: The merged and grouped DataFrame.
    """
    # Merge all dataframes
    df_all_sim = pd.concat(l_df_output)

    # Handle mutable default arguments
    if l_parameters_to_keep is None:
        logging.info("No list of parameters to keep provided, keeping all available parameters")
        l_parameters_to_keep = list(df_all_sim.columns)

    if only_keep_lost_particles:
        # Extract the particles that were lost for DA computation
        df_all_sim = df_all_sim[df_all_sim["state"] != 1]

    # Check if the dataframe is empty
    if df_all_sim.empty:
        logging.warning("No unstable particles found, the output dataframe will be empty.")

    # Group by parameters of interest
    df_grouped = df_all_sim.groupby(l_group_by_parameters)

    # Return the grouped dataframe, keeping only the minimum values of the parameters of interest
    # (should not have impact except for DA, which we want to be minimal)
    return pd.DataFrame(
        [df_grouped[parameter].min() for parameter in l_parameters_to_keep]
    ).transpose()


def aggregate_output_data(
    path_tree: str,
    l_group_by_parameters: List[str],
    generation_of_interest: int = 2,
    name_output: str = "output_particles.parquet",
    write_output: bool = True,
    path_output: Optional[str] = None,
    only_keep_lost_particles: bool = True,
    dic_parameters_of_interest: Optional[Dict[str, List[str]]] = None,
    l_parameters_to_keep: Optional[List[str]] = None,
    name_template_parameters: str = "parameters_lhc.yaml",
    path_template_parameters: Optional[str] = None,
    force_overwrite: bool = False,
) -> pd.DataFrame:
    """
    Aggregates output data from simulation files.

    Args:
        path_tree (str): The path to the tree file.
        l_group_by_parameters (list): List of parameters to group by.
        generation_of_interest (int, optional): The generation of interest. Defaults to 2.
        name_output (str, optional): The name of the output file. Defaults to "output_particles.parquet".
        write_output (bool, optional): Flag to indicate if the output should be written to a file.
            Defaults to True.
        path_output (str, optional): The path to the output file. If not provided, the default
            output file will be in the study folder as 'da.parquet'. Defaults to None.
        only_keep_lost_particles (bool, optional): Flag to indicate if only lost particles should be
            kept. Defaults to True.
        dic_parameters_of_interest (dict, optional): Dictionary of parameters of interest. Defaults
            to None.
        l_parameters_to_keep (list, optional): List of parameters to keep. Defaults to None.
        name_template_parameters (str, optional): The name of the template parameters file
            associating each parameter to a list of keys. Defaults to "parameters_lhc.yaml", which
            is already contained in the study-da package, and includes the main usual parameters.
        path_template_parameters (str, optional): The path to the template parameters file. Must
            be provided if a no template already contained in study-da is provided through the
            argument name_template_parameters. Defaults to None.
        force_overwrite (bool, optional): Flag to indicate if the output file should be overwritten
            if it already exists. Defaults to False.

    Returns:
        pd.DataFrame: The final aggregated DataFrame.
    """
    # Check it the output doesn't already exist and ask for confirmation to overwrite
    dic_tree, _ = load_dic_from_path(path_tree)
    absolute_path_study = dic_tree["absolute_path"]
    if path_output is None:
        path_output = os.path.join(absolute_path_study, "da.parquet")
    if os.path.exists(path_output) and not force_overwrite:
        input_user = input(
            f"The output file {path_output} already exists. Do you want to overwrite it? (y/n) "
        )
        if input_user.lower() != "y":
            logging.warning("Output file not overwritten")
            return pd.read_parquet(path_output)

    logging.info("Analysis of output simulation files started")

    dic_all_jobs = ConfigJobs(dic_tree).find_all_jobs()

    l_df_sim = get_particles_data(
        dic_all_jobs, absolute_path_study, generation_of_interest, name_output
    )

    default_path_template_parameters = False
    if dic_parameters_of_interest is None:
        if path_template_parameters is not None:
            logging.info("Loading parameters of interest from the provided configuration file")
        else:
            if name_template_parameters is None:
                raise ValueError(
                    "No template configuration file provided for the parameters of interest"
                )
            logging.info("Loading parameters of interest from the template configuration file")
            path_template_parameters = os.path.join(
                os.path.dirname(inspect.getfile(aggregate_output_data)),
                "configs",
                name_template_parameters,
            )
            default_path_template_parameters = True
        dic_parameters_of_interest, _ = load_dic_from_path(path_template_parameters)

    l_df_output = add_parameters_from_config(
        l_df_sim, dic_parameters_of_interest, default_path_template_parameters
    )

    df_final = merge_and_group_by_parameters_of_interest(
        l_df_output, l_group_by_parameters, only_keep_lost_particles, l_parameters_to_keep
    )

    print("ICI", df_final)

    # Fix the LHC version type
    df_final = fix_LHC_version(df_final)

    if write_output:
        df_final.to_parquet(path_output)
    elif path_output is not None:
        logging.warning("Output path provided but write_output set to False, no output saved")

    logging.info("Final dataframe for current set of simulations: %s", df_final)
    return df_final


def fix_LHC_version(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fixes the LHC version type in the DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to fix.

    Returns:
        pd.DataFrame: The fixed DataFrame.
    """
    # Fix the LHC version type
    print(df["ver_lhc_run"])
    if "ver_lhc_run" in df.columns and not df["ver_lhc_run"].empty:
        if df["ver_lhc_run"].isna().sum() != 0:
            logging.warning("Some LHC version numbers are NaN... Ignoring")
        else:
            df["ver_lhc_run"] = df["ver_lhc_run"].astype("int32")
    if "ver_hllhc_optics" in df.columns and not df["ver_hllhc_optics"].empty:
        if df["ver_hllhc_optics"].isna().sum() != 0:
            logging.warning("Some HLLHC optics version numbers are NaN... Ignoring")
        else:
            df["ver_hllhc_optics"] = df["ver_hllhc_optics"].astype("float32")

    return df
