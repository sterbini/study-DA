# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard library imports
import importlib.metadata

# Local imports
from .generate.generate_scan import GenerateScan
from .submit.submit_scan import SubmitScan

__all__ = [
    "GenerateScan",
    "SubmitScan",
]

# ==================================================================================================
# --- Package version
# ==================================================================================================
try:
    __version__ = importlib.metadata.version("study-da")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"
