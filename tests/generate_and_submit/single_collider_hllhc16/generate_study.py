# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import os

# Import third-party modules
# Import user-defined modules
from study_da import create_single_job
from study_da.utils import load_dic_from_path, write_dic_to_path

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================

# Load the configuration from hllhc16
config, ryaml = load_dic_from_path(
    "../../../study_da/generate/template_configurations/config_hllhc16.yaml"
)

# Update the location of acc-models
config["config_mad"]["links"]["acc-models-lhc"] = (
    "../../../../../external_dependencies/acc-models-lhc"
)
# Adapt the number of turns
config["config_simulation"]["n_turns"] = 100

# Drop the configuration locally
local_config = "config_hllhc16.yaml"
write_dic_to_path(config, local_config, ryaml)

# Now generate the study in the local directory
create_single_job(
    name_main_configuration=local_config,
    name_executable_generation_1="generation_1.py",
    name_executable_generation_2="generation_2_level_by_nb.py",
    name_study="single_job_study_hllhc16",
    force_overwrite=True,
)

# Delete the configuration
os.remove(local_config)
