"""
This module provides functions to create and customize study plots, including heatmaps and 3D
volume renderings.

Functions:
    _set_style() -> None:

    _add_text_annotation() -> plt.Axes:

    _smooth() -> np.ndarray:

    _mask() -> np.ndarray:

    _add_contours() -> plt.Axes:

    _add_diagonal_lines() -> plt.Axes:

    add_QR_code() -> plt.Figure:

    _set_labels() -> plt.Axes:

    plot_heatmap() -> tuple[plt.Figure, plt.Axes]:

    plot_3D() -> Any:
"""

# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import logging
from typing import Any, Optional

# Third party imports
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import qrcode
from scipy.interpolate import griddata
from scipy.ndimage.filters import gaussian_filter

# Local imports
from .utils import (
    apply_high_quality,
    use_default_fonts,
    use_latex_fonts,
)


# ==================================================================================================
# --- Functions to create study plots
# ==================================================================================================
def _set_style(style: str, latex_fonts: bool, vectorize: bool) -> None:
    """
    Sets the style for the plot.

    Args:
        style (str): The style to use for the plot.
        latex_fonts (bool): Whether to use LaTeX fonts.
        vectorize (bool): Whether to vectorize the plot.
    """
    if latex_fonts:
        use_latex_fonts()
    else:
        use_default_fonts()

    if vectorize:
        apply_high_quality(vectorial=True)
    else:
        apply_high_quality(vectorial=False)

    plt.style.use(style)


def _add_text_annotation(
    df_to_plot: pd.DataFrame, data_array: np.ndarray, ax: plt.Axes, vmin: float, vmax: float
) -> plt.Axes:
    """
    Adds text annotations to the heatmap.

    Args:
        df_to_plot (pd.DataFrame): The dataframe to plot.
        data_array (np.ndarray): The corresponding data array.
        ax (plt.Axes): The axes to plot on.
        vmin (float): The minimum value for the color scale.
        vmax (float): The maximum value for the color scale.

    Returns:
        plt.Axes: The axes with text annotations.
    """
    # Loop over data dimensions and create text annotations.
    for i in range(len(df_to_plot.index)):
        for j in range(len(df_to_plot.columns)):
            if data_array[i, j] >= vmax:
                val = r"$\geq $" + str(vmax)
            elif data_array[i, j] <= vmin:
                val = r"$\leq $" + str(vmin)
            else:
                val = f"{data_array[i, j]:.1f}"
            _ = ax.text(j, i, val, ha="center", va="center", color="white", fontsize=4)

    return ax


def _smooth(data_array: np.ndarray, symmetric_missing: bool) -> np.ndarray:
    """
    Smooths the data array.

    Args:
        data_array (np.ndarray): The data array to smooth.
        symmetric_missing (bool): Whether to make the matrix symmetric by replacing the lower
            triangle with the upper triangle (or conversely). Needed for clean smoothing.

    Returns:
        np.ndarray: The smoothed data array.
    """
    # make the matrix symmetric by replacing the lower triangle with the upper triangle
    data_smoothed = np.copy(data_array)
    data_smoothed[np.isnan(data_array)] = 0
    if symmetric_missing:
        try:
            # sum the upper and lower triangle, but not the intersection of the two matrices
            intersection = np.zeros_like(data_smoothed)
            for x in range(data_smoothed.shape[0]):
                for y in range(data_smoothed.shape[1]):
                    if np.min((data_smoothed[x, y], data_smoothed[y, x])) == 0.0:
                        intersection[x, y] = 0.0
                    else:
                        intersection[x, y] = data_smoothed[y, x]
            data_smoothed = data_smoothed + data_smoothed.T - intersection
        except Exception:
            logging.warning("Did not manage to smooth properly")
    data_smoothed = gaussian_filter(data_smoothed, 0.7)

    return data_smoothed


def _mask(
    mask_lower_triangle: bool, mask_upper_triangle: bool, data_smoothed: np.ndarray, k_masking: int
) -> tuple[np.ndarray, np.ndarray | None]:
    """
    Masks the lower or upper triangle of the data array.

    Args:
        mask_lower_triangle (bool): Whether to mask the lower triangle.
        mask_upper_triangle (bool): Whether to mask the upper triangle.
        data_smoothed (np.ndarray): The smoothed data array.
        k_masking (int): The k parameter for masking (distance form the diagonal).

    Returns:
        tuple[np.ndarray, np.ndarray|None]: The masked data array and the mask.
    """
    # You might need to adjust the k_masking parameter if the matrix you work with is not symmetric
    if mask_lower_triangle:
        mask = np.tri(data_smoothed.shape[0], k=k_masking)
        return np.ma.masked_array(data_smoothed, mask=mask.T), mask.T
    elif mask_upper_triangle:
        mask = np.tri(data_smoothed.shape[0], k=k_masking)
        return np.ma.masked_array(data_smoothed, mask=mask), mask.T
    else:
        return data_smoothed, None


def _add_contours(
    ax: plt.Axes,
    data_array: np.ndarray,
    mx: np.ndarray,
    green_contour: Optional[float],
    min_level: float = 1,
    max_level: float = 15,
    delta_levels: float = 0.5,
    mask: np.ndarray | None = None,
) -> plt.Axes:
    """
    Adds contour lines to the heatmap.

    Args:
        ax (plt.Axes): The axes to plot on.
        data_array (np.ndarray): The data array.
        mx (np.ndarray): The smoothed data array.
        green_contour (Optional[float]): The value for the green contour line.
        min_level (float, optional): The minimum level for the contours. Defaults to 1.
        max_level (float, optional): The maximum level for the contours. Defaults to 15.
        delta_levels (float, optional): The delta between contour levels. Defaults to 0.5.
        mask (np.ndarray, optional): The mask for the data array. Defaults to None.

    Returns:
        plt.Axes: The axes with contour lines.
    """
    if green_contour is None:
        levels = list(np.arange(min_level, max_level, delta_levels))
    else:
        levels = list(np.arange(min_level, green_contour, delta_levels)) + list(
            np.arange(green_contour + delta_levels, max_level, delta_levels)
        )
    X = np.arange(0.5, data_array.shape[1])
    Y = np.arange(0.5, data_array.shape[0])

    if mask is not None:
        mx = np.ma.masked_array(mx, mask=mask)

    CSS = ax.contour(X, Y, mx, colors="black", levels=levels, linewidths=0.2)
    ax.clabel(CSS, inline=True, fontsize=6)

    if green_contour is not None:
        CS2 = ax.contour(X, Y, mx, colors="green", levels=[green_contour], linewidths=1)
        ax.clabel(CS2, inline=1, fontsize=6)

    return ax


def _add_diagonal_lines(ax: plt.Axes, shift: int = 1) -> plt.Axes:
    """
    Adds diagonal lines to the heatmap.

    Args:
        ax (plt.Axes): The axes to plot on.
        shift (int, optional): The shift for the diagonal lines. Defaults to 1.

    Returns:
        plt.Axes: The axes with diagonal lines.
    """
    ax.plot([0, 1000], [shift, 1000 + shift], color="tab:blue", linestyle="--", linewidth=1)
    ax.plot([0, 1000], [-10 + shift, 990 + shift], color="tab:blue", linestyle="--", linewidth=1)
    ax.plot([0, 1000], [-5 + shift, 995 + shift], color="black", linestyle="--", linewidth=1)
    return ax


def add_QR_code(fig: plt.Figure, link: str, position_qr="top-right") -> plt.Figure:
    """
    Adds a QR code pointing to the given link to the figure.

    Args:
        fig (plt.Figure): The figure to add the QR code to.
        link (str): The link to encode in the QR code.

    Returns:
        plt.Figure: The figure with the QR code.
    """
    # Add QR code pointing to the github repository
    qr = qrcode.QRCode(
        # version=None,
        box_size=10,
        border=1,
    )
    qr.add_data(link)
    qr.make(fit=False)
    im = qr.make_image(fill_color="black", back_color="transparent")
    if position_qr == "top-right":
        newax = fig.add_axes([0.9, 0.9, 0.05, 0.05], anchor="NE", zorder=1)
    elif position_qr == "bottom-right":
        newax = fig.add_axes([0.9, 0.1, 0.05, 0.05], anchor="SE", zorder=1)
    elif position_qr == "bottom-left":
        newax = fig.add_axes([0.1, 0.1, 0.05, 0.05], anchor="SW", zorder=1)
    elif position_qr == "top-left":
        newax = fig.add_axes([0.1, 0.9, 0.05, 0.05], anchor="NW", zorder=1)
    else:
        raise ValueError(f"Position {position_qr} not recognized")
    newax.imshow(im, resample=False, interpolation="none", filternorm=False)
    # Add link below qrcode
    newax.plot([0, 0], [0, 0], color="white", label="link")
    _ = newax.annotate(
        "lin",
        xy=(0, 300),
        xytext=(0, 300),
        fontsize=30,
        url=link,
        bbox=dict(color="white", alpha=1e-6, url=link),
        alpha=0,
    )
    # Hide X and Y axes label marks
    newax.xaxis.set_tick_params(labelbottom=False)
    newax.yaxis.set_tick_params(labelleft=False)
    # Hide X and Y axes tick marks
    newax.set_xticks([])
    newax.set_yticks([])
    newax.set_axis_off()

    return fig


def _set_labels(
    ax: plt.Axes,
    df_to_plot: pd.DataFrame,
    data_array: np.ndarray,
    horizontal_variable: str,
    vertical_variable: str,
    xlabel: Optional[str],
    ylabel: Optional[str],
    xaxis_ticks_on_top: bool,
) -> plt.Axes:
    """
    Sets the labels for the heatmap.

    Args:
        ax (plt.Axes): The axes to plot on.
        df_to_plot (pd.DataFrame): The dataframe to plot.
        data_array (np.ndarray): The data array.
        horizontal_variable (str): The horizontal variable.
        vertical_variable (str): The vertical variable.
        xlabel (Optional[str]): The label for the x-axis.
        ylabel (Optional[str]): The label for the y-axis.
        xaxis_ticks_on_top (bool): Whether to place the x-axis ticks on top.

    Returns:
        plt.Axes: The axes with labels set.
    """
    # Filter out odd ticks and and label the rest with the respective list entries
    ax.set_xticks(np.arange(len(df_to_plot.columns))[::2], labels=df_to_plot.columns[::2])
    ax.set_yticks(np.arange(len(df_to_plot.index))[::2], labels=df_to_plot.index[::2])

    if xlabel is None:
        xlabel = horizontal_variable
    if ylabel is None:
        ylabel = vertical_variable
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(-0.5, data_array.shape[1] - 0.5)
    ax.set_ylim(-0.5, data_array.shape[0] - 0.5)

    # Ticks on top
    if xaxis_ticks_on_top:
        ax.xaxis.tick_top()

    # Rotate the tick labels and set their alignment.
    plt.setp(
        ax.get_xticklabels(),
        rotation=-30,
        rotation_mode="anchor",
        # ha="left",
    )

    # If the x-axis needs to be padded... This needs testing
    # ax.tick_params(axis='x', which='major', pad=5)
    return ax


def plot_heatmap(
    dataframe_data: pd.DataFrame,
    horizontal_variable: str,
    vertical_variable: str,
    color_variable: str,
    link: Optional[str] = None,
    position_qr: Optional[str] = "top-right",
    plot_contours: bool = True,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    symmetric_missing: bool = False,
    mask_lower_triangle: bool = False,
    mask_upper_triangle: bool = False,
    plot_diagonal_lines: bool = True,
    shift_diagonal_lines: int = 1,
    xaxis_ticks_on_top: bool = True,
    title: str = "",
    vmin: float = 4.5,
    vmax: float = 7.5,
    k_masking: int = -1,
    green_contour: Optional[float] = 6.0,
    min_level_contours: float = 1,
    max_level_contours: float = 15,
    delta_levels_contours: float = 0.5,
    figsize: Optional[tuple[float, float]] = None,
    label_cbar: str = "Minimum DA (" + r"$\sigma$" + ")",
    colormap: str = "coolwarm_r",
    style: str = "ggplot",
    output_path: str = "output.pdf",
    display_plot: bool = True,
    latex_fonts: bool = True,
    vectorize: bool = False,
    fill_missing_value_with: Optional[str | float] = None,
    dpi=300,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Plots a heatmap from the given dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing the data to plot.
        horizontal_variable (str): The variable to plot on the horizontal axis.
        vertical_variable (str): The variable to plot on the vertical axis.
        color_variable (str): The variable to use for the color scale.
        link (Optional[str], optional): A link to encode in a QR code. Defaults to None.
        plot_contours (bool, optional): Whether to plot contours. Defaults to True.
        xlabel (Optional[str], optional): The label for the x-axis. Defaults to None.
        ylabel (Optional[str], optional): The label for the y-axis. Defaults to None.
        symmetric_missing (bool, optional): Whether to make the matrix symmetric by replacing the
            lower triangle with the upper triangle. Defaults to False.
        mask_lower_triangle (bool, optional): Whether to mask the lower triangle. Defaults to False.
        mask_upper_triangle (bool, optional): Whether to mask the upper triangle. Defaults to False.
        plot_diagonal_lines (bool, optional): Whether to plot diagonal lines. Defaults to True.
        shift_diagonal_lines (int, optional): The shift for the diagonal lines. Defaults to 1.
        xaxis_ticks_on_top (bool, optional): Whether to place the x-axis ticks on top. Defaults to True.
        title (str, optional): The title of the plot. Defaults to "".
        vmin (float, optional): The minimum value for the color scale. Defaults to 4.5.
        vmax (float, optional): The maximum value for the color scale. Defaults to 7.5.
        k_masking (int, optional): The k parameter for masking. Defaults to -1.
        green_contour (Optional[float], optional): The value for the green contour line. Defaults to 6.0.
        min_level_contours (float, optional): The minimum level for the contours. Defaults to 1.
        max_level_contours (float, optional): The maximum level for the contours. Defaults to 15.
        delta_levels_contours (float, optional): The delta between contour levels. Defaults to 0.5.
        figsize (Optional[tuple[float, float]], optional): The size of the figure. Defaults to None.
        label_cbar (str, optional): The label for the colorbar. Defaults to "Minimum DA ($\sigma$)".
        colormap (str, optional): The colormap to use. Defaults to "coolwarm_r".
        style (str, optional): The style to use for the plot. Defaults to "ggplot".
        output_path (str, optional): The path to save the plot. Defaults to "output.pdf".
        display_plot (bool, optional): Whether to display the plot. Defaults to True.
        latex_fonts (bool, optional): Whether to use LaTeX fonts. Defaults to True.
        vectorize (bool, optional): Whether to vectorize the plot. Defaults to False.
        fill_missing_value_with (Optional[str | float], optional): The value to fill missing values
            with. Can be a number or 'interpolate'. Defaults to None.
        dpi (int, optional): The DPI for the plot. Defaults to 300.

    Returns:
        tuple[plt.Figure, plt.Axes]: The figure and axes of the plot.
    """
    # Use the requested style
    _set_style(style, latex_fonts, vectorize)

    # Get the dataframe to plot
    df_to_plot = dataframe_data.pivot(
        index=vertical_variable, columns=horizontal_variable, values=color_variable
    )

    # Get numpy array from dataframe
    data_array = df_to_plot.to_numpy(dtype=float)

    # Replace NaNs with a value if requested
    if fill_missing_value_with is not None:
        if isinstance(fill_missing_value_with, (int, float)):
            data_array[np.isnan(data_array)] = fill_missing_value_with
        elif fill_missing_value_with == "interpolate":
            # Interpolate missing values with griddata
            x = np.arange(data_array.shape[1])
            y = np.arange(data_array.shape[0])
            xx, yy = np.meshgrid(x, y)
            x = xx[~np.isnan(data_array)]
            y = yy[~np.isnan(data_array)]
            z = data_array[~np.isnan(data_array)]
            data_array = griddata((x, y), z, (xx, yy), method="cubic")

    # Mask the lower or upper triangle (checks are done in the function)
    data_array_masked, mask_main_array = _mask(
        mask_lower_triangle, mask_upper_triangle, data_array, k_masking
    )

    # Define colormap and set NaNs to white
    cmap = matplotlib.colormaps.get_cmap(colormap)
    cmap.set_bad("w")

    # Build heatmap, with inverted y axis
    fig, ax = plt.subplots()
    if figsize is not None:
        fig.set_size_inches(figsize)
    im = ax.imshow(data_array_masked, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.invert_yaxis()

    # Add text annotations
    ax = _add_text_annotation(df_to_plot, data_array, ax, vmin, vmax)

    # Smooth data for contours
    mx = _smooth(data_array, symmetric_missing)

    # Plot contours if requested
    if plot_contours:
        ax = _add_contours(
            ax,
            data_array,
            mx,
            green_contour,
            min_level_contours,
            max_level_contours,
            delta_levels_contours,
            mask_main_array,
        )

    if plot_diagonal_lines:
        # Diagonal lines must be plotted after the contour lines, because of bug in matplotlib
        # Shift might need to be adjusted
        ax = _add_diagonal_lines(ax, shift=shift_diagonal_lines)

    # Define title and axis labels
    ax.set_title(
        title,
        fontsize=10,
    )

    # Set axis labels
    ax = _set_labels(
        ax,
        df_to_plot,
        data_array,
        horizontal_variable,
        vertical_variable,
        xlabel,
        ylabel,
        xaxis_ticks_on_top,
    )

    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.026, pad=0.04)
    cbar.ax.set_ylabel(label_cbar, rotation=90, va="bottom", labelpad=15)

    # Remove potential grid
    plt.grid(visible=None)

    # Add QR code with a link to the topright side (a bit experimental, might need adjustments)
    if link is not None:
        fig = add_QR_code(fig, link, position_qr)

    # Save and potentially display the plot
    if output_path is not None:
        if output_path.endswith(".pdf") and not vectorize:
            raise ValueError("Please set vectorize=True to save as PDF")
        elif not output_path.endswith(".pdf") and vectorize:
            raise ValueError("Please set vectorize=False to save as PNG or JPG")
        plt.savefig(output_path, bbox_inches="tight", dpi=dpi)

    if display_plot:
        plt.show()
    return fig, ax


# This function is a prototype... Latex title seems buggy
# Can't return a go.Figure, because this would require plotly as a dependency
def plot_3D(
    dataframe_data: pd.DataFrame,
    x_variable: str,
    y_variable: str,
    z_variable: str,
    color_variable: str,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    z_label: Optional[str] = None,
    title: str = "",
    vmin: float = 4.5,
    vmax: float = 7.5,
    surface_count: int = 30,
    opacity: float = 0.2,
    figsize: tuple[float, float] = (1000, 1000),
    colormap: str = "RdBu",
    output_path: str = "output.png",
    output_path_html: str = "output.html",
    display_plot: bool = True,
) -> Any:
    """
    Plots a 3D volume rendering from the given dataframe.

    Args:
        dataframe_data (pd.DataFrame): The dataframe containing the data to plot.
        x_variable (str): The variable to plot on the x-axis.
        y_variable (str): The variable to plot on the y-axis.
        z_variable (str): The variable to plot on the z-axis.
        color_variable (str): The variable to use for the color scale.
        xlabel (Optional[str], optional): The label for the x-axis. Defaults to None.
        ylabel (Optional[str], optional): The label for the y-axis. Defaults to None.
        z_label (Optional[str], optional): The label for the z-axis. Defaults to None.
        title (str, optional): The title of the plot. Defaults to "".
        vmin (float, optional): The minimum value for the color scale. Defaults to 4.5.
        vmax (float, optional): The maximum value for the color scale. Defaults to 7.5.
        surface_count (int, optional): The number of surfaces for volume rendering. Defaults to 30.
        opacity (float, optional): The opacity of the volume rendering. Defaults to 0.2.
        figsize (tuple[float, float], optional): The size of the figure. Defaults to (1000, 1000).
        colormap (str, optional): The colormap to use. Defaults to "RdBu".
        output_path (str, optional): The path to save the plot image. Defaults to "output.png".
        output_path_html (str, optional): The path to save the plot HTML. Defaults to "output.html".
        display_plot (bool, optional): Whether to display the plot. Defaults to True.

    Returns:
        go.Figure: The plotly figure object.
    """
    # Check if plotly is installed
    try:
        import plotly.graph_objects as go
    except ImportError as e:
        raise ImportError("Please install plotly to use this function") from e

    X = np.array(dataframe_data[x_variable])
    Y = np.array(dataframe_data[y_variable])
    Z = np.array(dataframe_data[z_variable])
    values = np.array(dataframe_data[color_variable])
    fig = go.Figure(
        data=go.Volume(
            x=X.flatten(),
            y=Y.flatten(),
            z=Z.flatten(),
            value=values.flatten(),
            isomin=vmin,
            isomax=vmax,
            opacity=opacity,  # needs to be small to see through all surfaces
            surface_count=surface_count,  # needs to be a large number for good volume rendering
            colorscale=colormap,
        )
    )

    fig.update_layout(
        scene_xaxis_title_text=xlabel,
        scene_yaxis_title_text=ylabel,
        scene_zaxis_title_text=z_label,
        title=title,
    )

    # Center the title
    fig.update_layout(title_x=0.5, title_y=0.9, title_xanchor="center", title_yanchor="top")

    # Specify the width and height of the figure
    fig.update_layout(width=figsize[0], height=figsize[1])

    # Display/save/return the figure
    if output_path is not None:
        fig.write_image(output_path)

    if output_path_html is not None:
        fig.write_html(output_path_html)

    if display_plot:
        fig.show()

    return fig
