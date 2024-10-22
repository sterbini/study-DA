# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import inspect
import os

# Import third-party modules
import ruamel.yaml

# Import user-defined modules
from study_da.generate.generate_scan import GenerateScan

from .dic_utils import load_dic_from_path


# ==================================================================================================
# --- Function definition
# ==================================================================================================
def load_template_configuration_as_dic(
    template_configuration_name: str,
) -> tuple[dict, ruamel.yaml.YAML]:
    """Load a template configuration as a dictionary.

    Args:
        template_configuration_name (str): The name of the template configuration.

    Returns:
        dict: The template dictionary.

    """
    path_local_template_configurations = (
        f"{os.path.dirname(inspect.getfile(GenerateScan))}/template_configurations/"
    )

    # Add .yaml extension to template name
    if not template_configuration_name.endswith(".yaml"):
        template_configuration_name = f"{template_configuration_name}.yaml"

    # Get path to template
    path_template_config = f"{path_local_template_configurations}{template_configuration_name}"

    # Load template
    return load_dic_from_path(path_template_config)


def load_template_script_as_str(template_script_name: str) -> str:
    """Load a template script as a string.

    Args:
        template_script_name (str): The name of the template script.

    Returns:
        str: The template script as a string.

    """
    path_local_template_scripts = (
        f"{os.path.dirname(inspect.getfile(GenerateScan))}/template_scripts/"
    )

    # Get path to template
    path_template_script = f"{path_local_template_scripts}{template_script_name}"

    # Load template
    with open(path_template_script, "r") as fid:
        template_script = fid.read()

    return template_script
