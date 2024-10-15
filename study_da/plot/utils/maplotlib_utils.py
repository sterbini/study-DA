# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports

# Third party imports
import matplotlib
import matplotlib_inline
import seaborn as sns

# ==================================================================================================
# --- Functions to create study plots
# ==================================================================================================


def apply_high_quality(vectorial: bool = False) -> None:
    """
    Sets the matplotlib output format to high quality or vectorial plots.

    Args:
        vectorial (bool, optional): If True, sets the format to 'svg'. Otherwise, sets it to
            'retina'. Defaults to False.
    """
    if vectorial:
        matplotlib_inline.backend_inline.set_matplotlib_formats("svg")
    else:
        matplotlib_inline.backend_inline.set_matplotlib_formats("retina")


def apply_standard_quality() -> None:
    """
    Sets the matplotlib output format to standard quality ("png" argument).
    """
    matplotlib_inline.backend_inline.set_matplotlib_formats("png")


def use_latex_fonts(italic: bool = False) -> None:
    """
    Configures matplotlib to use LaTeX fonts.

    Args:
        italic (bool, optional): If True, sets the default mathtext to italic. Otherwise, sets it
            to regular. Defaults to False.
    """
    matplotlib.rcParams["mathtext.fontset"] = "cm"
    matplotlib.rcParams["font.family"] = "STIXGeneral"
    if not italic:
        matplotlib.rcParams["mathtext.default"] = "regular"
        matplotlib.rcParams["font.weight"] = "light"


def use_default_fonts() -> None:
    """
    Configures matplotlib to use the default DejaVu Sans fonts.
    """
    matplotlib.rcParams["mathtext.fontset"] = "dejavusans"
    matplotlib.rcParams["font.family"] = "DejaVu Sans"
    matplotlib.rcParams["mathtext.default"] = "it"
    matplotlib.rcParams["font.weight"] = "normal"


def apply_nicer_style(remove_right_upper_spines: bool = True) -> None:
    """
    Applies a nicer style to plots, using the whitegrid seaborn theme.

    Args:
        remove_right_upper_spines (bool, optional): If True, removes the right and upper spines
            from the plots. Defaults to True.
    """
    sns.set_theme(style="whitegrid")

    if remove_right_upper_spines:
        custom_params = {"axes.spines.right": False, "axes.spines.top": False}
        sns.set_theme(style="ticks", rc=custom_params)

    # sns.set(font='Adobe Devanagari')
    sns.set_context("paper", font_scale=1, rc={"lines.linewidth": 0.5, "grid.linewidth": 0.3})
