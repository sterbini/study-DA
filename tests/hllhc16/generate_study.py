# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging
import os

# Import third-party modules
# Import user-defined modules
from study_da import StudyDA

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================

# First copy the template configuration in the local directory
os.system("cp ../../study_da/template_configurations/config_hllhc16.yaml .")

# Now generate the study in the local directory
study_da = StudyDA(path_config="configuration_scan.yaml")
