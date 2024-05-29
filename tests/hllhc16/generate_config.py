# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging

# Import third-party modules
# Import user-defined modules
from study_da import load_configuration_from_path

# ==================================================================================================
# --- Script to generate configuration (to generate a study)
# ==================================================================================================

# Load template config hllhc16
configuration, ryaml = load_configuration_from_path(
    "../../study_da/template_configurations/config_hllhc16.yaml"
)

