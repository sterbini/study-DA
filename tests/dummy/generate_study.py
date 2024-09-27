# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
# Import third-party modules
# Import user-defined modules
from study_da import StudyDA

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================

# Generate the study in the local directory
study_da = StudyDA(path_config="config_scan.yaml")
study_da.create_study(tree_file=True, force_overwrite=True)
