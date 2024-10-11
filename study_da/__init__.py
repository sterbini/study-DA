# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard library imports
import importlib.metadata

# Local imports
from .generate.generate_scan import GenerateScan
from .study_da import create, create_single_job
from .submit.submit_scan import SubmitScan

__all__ = ["GenerateScan", "SubmitScan", "create", "create_single_job"]

# ==================================================================================================
# --- Package version
# ==================================================================================================
try:
    __version__ = importlib.metadata.version("study-da")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"
