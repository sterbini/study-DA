# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging
import os

# Import third-party modules
import numpy as np

# Import user-defined modules
from study_da import create
from study_da.utils import (
    find_item_in_dic,
    load_dic_from_path,
    write_dic_to_path,
)

# Set up the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


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
write_dic_to_path(config, "config_hllhc16.yaml", ryaml)

# Now generate the study in the local directory
# study_da = GenerateScan(path_config="config_scan.yaml")
# study_da.create_study(tree_file=True, force_overwrite=True)


# Load configuration
config, ryaml = load_dic_from_path("config_scan_manual_gen_2.yaml")
n_split = find_item_in_dic(config, "n_split")
dic_parameter_all_gen = {
    "generation_2": {
        "distribution_file": [f"{x}.parquet" for x in range(n_split)],
        "qx": [{key: qx for key in ["lhcb1", "lhcb2"]} for qx in np.linspace(62.31, 62.32, 10)],
        "qy": [{key: qy for key in ["lhcb1", "lhcb2"]} for qy in np.linspace(60.32, 60.33, 10)],
    }
}
dic_parameter_all_gen_naming = {
    "generation_2": {
        "distribution_file": [f"{x}.parquet" for x in range(n_split)],
        "qx": np.linspace(62.31, 62.32, 10),
        "qy": np.linspace(60.32, 60.33, 10),
    }
}


create(
    path_config="config_scan_manual_gen_2.yaml",
    tree_file=True,
    force_overwrite=True,
    dic_parameter_all_gen=dic_parameter_all_gen,
    dic_parameter_all_gen_naming=dic_parameter_all_gen_naming,
)

# Delete the configuration
os.remove("config_hllhc16.yaml")
