# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import inspect
import logging
import os
from typing import Optional

# Third party imports
import pandas as pd

# Local imports
from study_da.submit.config_jobs import ConfigJobs
from study_da.utils import nested_get
from study_da.utils.configuration import load_dic_from_path


# ==================================================================================================
# --- Functions to browse simulations folder and extract relevant observables
# ==================================================================================================
def get_particles_data(
    dic_all_jobs,
    absolute_path_study,
    generation_of_interest=2,
    name_output="output_particles.parquet",
):
    l_df_output = []
    for relative_path_job, dic_job in dic_all_jobs.items():
        if dic_job["gen"] != generation_of_interest:
            continue
        absolute_path_job = f"{absolute_path_study}/{relative_path_job}"
        absolute_folder_job = os.path.dirname(absolute_path_job)
        try:
            df_output = pd.read_parquet(f"{absolute_folder_job}/{name_output}")
        except Exception as e:
            logging.warning(e)
            continue

        # Register path of the job
        df_output["name base collider"] = relative_path_job

        # Add to the list
        l_df_output.append(df_output)

    return l_df_output


def add_parameters_from_config(
    l_df_output, dic_parameters_of_interest, default_path_template_parameters=False
):
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
    df_all_sim,
    l_group_by_parameters,
    only_keep_lost_particles=True,
    l_parameters_to_keep=None,
):
    # Merge all dataframes
    df_all_sim = pd.concat(df_all_sim)

    # Handle mutable default arguments
    if l_parameters_to_keep is None:
        logging.info("No list of parameters to keep provided, keeping all available parameters")
        l_parameters_to_keep = list(df_all_sim.columns)

    if only_keep_lost_particles:
        # Extract the particles that were lost for DA computation
        df_all_sim = df_all_sim[df_all_sim["state"] != 1]  # Lost particles

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
    l_group_by_parameters: list[str],
    generation_of_interest=2,
    name_output="output_particles.parquet",
    write_output=True,
    path_output=None,
    only_keep_lost_particles=True,
    dic_parameters_of_interest=None,
    l_parameters_to_keep: Optional[list[str]] = None,
    name_template_parameters="parameters_lhc.yaml",
    path_template_parameters=None,
):
    # Start of the script
    logging.info("Analysis of output simulation files started")

    # Load the tree
    dic_tree, _ = load_dic_from_path(path_tree)

    # Get absolute path of the study
    absolute_path_study = dic_tree["absolute_path"]

    # Get all jobs
    dic_all_jobs = ConfigJobs(dic_tree).find_all_jobs()

    # # Get particles data
    l_df_sim = get_particles_data(
        dic_all_jobs, absolute_path_study, generation_of_interest, name_output
    )

    # Define parameters of interest
    default_path_template_parameters = False
    if dic_parameters_of_interest is None:
        if path_template_parameters is not None:
            # Load dic_parameters_of_interest from the template configs
            logging.info("Loading parameters of interest from the provided configuration file")
        else:
            if name_template_parameters is None:
                raise ValueError(
                    "No template configuration file provided for the parameters of interest"
                )
            # Load dic_parameters_of_interest from the template configs
            logging.info("Loading parameters of interest from the template configuration file")
            path_template_parameters = (
                f"{os.path.dirname(inspect.getfile(aggregate_output_data))}"
                f"/configs/{name_template_parameters}"
            )
            default_path_template_parameters = True
        dic_parameters_of_interest, _ = load_dic_from_path(path_template_parameters)

    # Add parameters from config to the output data
    l_df_output = add_parameters_from_config(
        l_df_sim, dic_parameters_of_interest, default_path_template_parameters
    )

    # Merge and group by parameters of interest
    df_final = merge_and_group_by_parameters_of_interest(
        l_df_output, l_group_by_parameters, only_keep_lost_particles, l_parameters_to_keep
    )

    # Save data
    if write_output:
        if path_output is None:
            path_output = f"{absolute_path_study}/da.parquet"
        df_final.to_parquet(path_output)
    elif path_output is not None:
        logging.warning("Output path provided but write_output set to False, no output saved")

    logging.info("Final dataframe for current set of simulations: ", df_final)
    return df_final
