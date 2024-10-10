# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
# Import third-party modules
# Import user-defined modules
from study_da import create

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================

# Generate the study in the local directory
create(path_config="config_scan.yaml", tree_file=True, force_overwrite=True)
