# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
# Import third-party modules
# Import user-defined modules
from study_da import GenerateScan
from study_da.utils.configuration import load_dic_from_path, write_dic_to_path

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
config["config_simulation"]["n_turns"] = 100000

# Drop the configuration locally
write_dic_to_path(config, "config_hllhc16.yaml", ryaml)

# Now generate the study in the local directory
study_da = GenerateScan(path_config="config_scan.yaml")
study_da.create_study(tree_file=True, force_overwrite=True)
