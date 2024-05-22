"""This class is used to access and modify the study configuration."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules

# Import third-party modules
import yaml

# Import user-defined modules


# ==================================================================================================
# --- Function definition
# ==================================================================================================


def load_configuration_from_path(path: str) -> dict:
    # Load configuration
    with open(path, "r") as fid:
        configuration = yaml.safe_load(fid)

    return configuration
