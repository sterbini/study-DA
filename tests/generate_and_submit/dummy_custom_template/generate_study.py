# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging

# Import third-party modules
# Import user-defined modules
from study_da import create

# Set up the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================

# Generate the study in the local directory
create(path_config_scan="config_scan.yaml", force_overwrite=False)
