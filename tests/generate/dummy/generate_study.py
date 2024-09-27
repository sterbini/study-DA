# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
# Import third-party modules
# Import user-defined modules
from study_da import GenerateScan

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================

# Generate the study in the local directory
study_da = GenerateScan(path_config="config_scan.yaml")
study_da.create_study(tree_file=True, force_overwrite=True)
