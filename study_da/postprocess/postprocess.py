# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import logging

# Third party imports
import pandas as pd

# Local imports
from study_da.submit.config_jobs import ConfigJobs
from study_da.utils import nested_get
from study_da.utils.configuration import load_dic_from_path


# ==================================================================================================
# --- Functions to browse simulations folder and extract relevant observables
# ==================================================================================================
def get_particles_data(dic_all_jobs, name_output="output_particles.parquet"):
    l_df_output = []
    for job, path_job in dic_all_jobs.items():
        try:
            df_output = pd.read_parquet(f"{path_job}/{name_output}")
        except Exception as e:
            print(e)
            logging.warning(f"{job } does not have {name_output}")
            continue

        # Register path of the job
        df_output["name base collider"] = job

        # Add to the list
        l_df_output.append(df_output)

    return l_df_output


def add_parameters_from_config(l_df_output, dic_parameters_of_interest):
    for df_output in l_df_output:
        # Get generation configurations as dictionnaries for parameter assignation
        dic_configuration = df_output.attrs["configuration"]["config_collider"]

        # Select simulations parameters of interest
        for name_param, l_path_param in dic_parameters_of_interest.items():
            df_output[name_param] = nested_get(dic_configuration, l_path_param)

    return l_df_output


def merge_and_group_by_parameters_of_interest(
    df_all_sim,
    l_group_by_parameters,
    only_keep_lost_particles=True,
    l_parameters_to_keep=None,
):
    # Handle mutable default arguments
    if l_parameters_to_keep is None:
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


def aggregate_output_data(path_tree, write_output=True):
    # Start of the script
    logging.warning("Analysis of output simulation files started")

    # Load Data
    study_name = "example_tunescan"

    # Load the tree
    dic_tree, _ = load_dic_from_path(path_tree)

    # Get all jobs
    dic_all_jobs = ConfigJobs(dic_tree).find_all_jobs()

    # Get particles data
    l_df_sim = get_particles_data(dic_all_jobs)

    # Define parameters of interest
    dic_parameters_of_interest = {
,
    }

    # Reorganize data
    l_df_output = add_parameters_from_config(l_df_sim, dic_parameters_of_interest)

    # Merge and group by parameters of interest
    l_group_by_parameters = ["beam", "name base collider", "qx", "qy"]
    l_parameters_to_keep = [
        "normalized amplitude in xy-plane",
        "qx",
        "qy",
        "dqx",
        "dqy",
        "i_bunch",
        "i_oct",
        "num_particles_per_bunch",
    ]
    only_keep_lost_particles = True
    df_final = merge_and_group_by_parameters_of_interest(
        l_df_output, l_group_by_parameters, only_keep_lost_particles, l_parameters_to_keep
    )
    print("Final dataframe for current set of simulations: ", df_final)

    # Save data and print time
    df_final.to_parquet(f"../scans/{study_name}/da.parquet")

    return df_final
