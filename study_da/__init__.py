# ==================================================================================================
# --- Imports
# ==================================================================================================

# Standard library imports
import importlib.metadata

# Local imports
from .generate.generate_scan import GenerateScan
from .plot import get_title_from_configuration, plot_3D, plot_heatmap
from .postprocess import aggregate_output_data
from .study_da import create, create_single_job, submit
from .submit.submit_scan import SubmitScan

# ==================================================================================================
# --- Package version
# ==================================================================================================
try:
    __version__ = importlib.metadata.version("study-da")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    "GenerateScan",
    "SubmitScan",
    "create",
    "create_single_job",
    "submit",
    "aggregate_output_data",
    "get_title_from_configuration",
    "plot_heatmap",
    "plot_3D",
    "__version__",
]
