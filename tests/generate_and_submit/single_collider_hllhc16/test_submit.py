# Import standard library modules
import logging

from study_da import SubmitScan
from study_da.utils.configuration import load_dic_from_path, write_dic_to_path

# Set up the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# %%
# Mutate config to have proper path since study was moved
# Load the configuration from hllhc16
config, ryaml = load_dic_from_path("single_job_study_hllhc16/config_hllhc16.yaml")

# Adapt the path to the acc-models-lhc
config["config_mad"]["links"]["acc-models-lhc"] = (
    "../../../../../external_dependencies/acc-models-lhc"
)

# Drop the configuration locally
write_dic_to_path(config, "single_job_study_hllhc16/config_hllhc16.yaml", ryaml)

# %%
study_sub = SubmitScan(
    path_tree="single_job_study_hllhc16/tree.yaml",
    path_python_environment="/afs/cern.ch/work/c/cdroin/private/study-DA/.venv",
    path_python_environment_container="/usr/local/DA_study/miniforge_docker",
    path_container_image="/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cdroin/da-study-docker:42ac73a5",
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
name_config = "config_hllhc16.yaml"

# %%
study_sub.submit(
    one_generation_at_a_time=False,
    dic_additional_commands_per_gen=dic_additional_commands_per_gen,
    dic_dependencies_per_gen=dic_dependencies_per_gen,
    name_config=name_config,
)
# study_sub.keep_submit_until_done(wait_time = 1)
