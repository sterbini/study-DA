"""This class is used to access and modify the study configuration."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules

# Import third-party modules
import ruamel.yaml

# Import user-defined modules


# ==================================================================================================
# --- Function definition
# ==================================================================================================


def load_configuration_from_path(
    path: str, ryaml: ruamel.yaml.YAML | None = None
) -> tuple[dict, ruamel.yaml.YAML]:
    if ryaml is None:
        # Initialize yaml reader
        ryaml = ruamel.yaml.YAML()

    # Load configuration
    with open(path, "r") as fid:
        configuration = ryaml.load(fid)

    return configuration, ryaml


def write_configuration_to_path(
    configuration: dict, path: str, ryaml: ruamel.yaml.YAML | None = None
) -> None:
    if ryaml is None:
        # Initialize yaml reader
        ryaml = ruamel.yaml.YAML()

    # Write configuration
    with open(path, "w") as fid:
        ryaml.dump(configuration, fid)
