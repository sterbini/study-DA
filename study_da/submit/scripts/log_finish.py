"""This module contains the log_finish script that tags a job as finished in the tree file."""

# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import sys

# Third party imports
from filelock import SoftFileLock

# Local imports
from study_da.utils import load_dic_from_path, nested_set, write_dic_to_path

# ==================================================================================================
# --- Script
# ==================================================================================================

# Get path of the tree and keys to tag
tree_path = sys.argv[1]
l_keys = sys.argv[2:]

# Define lock
lock = SoftFileLock(f"{tree_path}.lock", timeout=30)

# Update tag
with lock:
    # Load the tree
    tree = load_dic_from_path(tree_path)[0]

    # Update the tree
    nested_set(tree, l_keys + ["status"], "finished")

    # Write the tree
    write_dic_to_path(tree, tree_path)
