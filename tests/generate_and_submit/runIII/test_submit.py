# Import standard library modules
import logging

from study_da import SubmitScan

# Set up the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

study_sub = SubmitScan(
    path_tree="example_tune_scan/tree.yaml",
    path_python_environment="/afs/cern.ch/work/c/cdroin/private/study-DA/.venv",
    path_python_environment_container="/usr/local/DA_study/miniforge_docker",
    path_container_image="/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cdroin/da-study-docker:af320ce3",
)

# %%
study_sub.configure_jobs(force_configure=False)

# %%
### Additional commands to be executed at the end of the run file (generation-specific)

# In case gen_1 is submitted to htc
# dic_additional_commands_per_gen = {
#     1: "cp *.json *.zip $path_job \n"
#     "cp -r particles $path_job/particles \n",
#     2: "",
# }

# In case gen_1 is submitted locally
dic_additional_commands_per_gen = {
    1: "rm -rf final_* modules optics_repository optics_toolkit tools tracking_tools temp mad_collider.log __pycache__ twiss* errors fc* optics_orbit_at* \n",
    2: "",
}


# Dependencies for the executable of each generation. Only needed if one uses HTC or Slurm.
dic_dependencies_per_gen = {1: ["acc-models-lhc"], 2: ["collider_file", "particle_folder"]}
name_config = "config_runIII.yaml"

# %%
study_sub.submit(
    one_generation_at_a_time=False,
    dic_additional_commands_per_gen=dic_additional_commands_per_gen,
    dic_dependencies_per_gen=dic_dependencies_per_gen,
    name_config=name_config,
)
# study_sub.keep_submit_until_done(wait_time = 1)
