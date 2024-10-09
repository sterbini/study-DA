# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import logging
from typing import Any, Optional

# Local imports
from . import GenerateScan

# ==================================================================================================
# --- Main functions
# ==================================================================================================


def create(
    path_config: str = "config_scan.yaml",
    tree_file: bool = True,
    force_overwrite: bool = True,
    dic_parameter_all_gen: Optional[dict[str, dict[str, Any]]] = None,
    dic_parameter_all_gen_naming: Optional[dict[str, dict[str, Any]]] = None,
) -> None:
    """
    Create a study based on the configuration file.

    Args:
        path_config (str, optional): Path to the configuration file. Defaults to "config_scan.yaml".
        tree_file (bool, optional): Flag to create the tree file. Defaults to True.
        force_overwrite (bool, optional): Flag to force overwrite the study. Defaults to True.

    Returns:
        None
    """
    logging.info(f"Create study from configuration file: {path_config}")
    study = GenerateScan(path_config=path_config)
    study.create_study(
        tree_file=tree_file,
        force_overwrite=force_overwrite,
        dic_parameter_all_gen=dic_parameter_all_gen,
        dic_parameter_all_gen_naming=dic_parameter_all_gen_naming,
    )
