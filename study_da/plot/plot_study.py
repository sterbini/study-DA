# ==================================================================================================
# --- Imports
# ==================================================================================================
# Standard library imports
import logging
from typing import Optional

# Third party imports
import matplotlib
import matplotlib.pyplot as plt
import matplotlib_inline
import numpy as np
import qrcode
import seaborn as sns
from scipy.ndimage.filters import gaussian_filter

# ==================================================================================================
# --- Functions to create study plots
# ==================================================================================================


def apply_high_quality(vectorial=False):
    if vectorial:
        matplotlib_inline.backend_inline.set_matplotlib_formats("svg")
    else:
        matplotlib_inline.backend_inline.set_matplotlib_formats("retina")

def apply_standard_quality():
    matplotlib_inline.backend_inline.set_matplotlib_formats("png")

def use_latex_fonts(italic=False):
    matplotlib.rcParams["mathtext.fontset"] = "cm"
    matplotlib.rcParams["font.family"] = "STIXGeneral"
    if not italic:
        matplotlib.rcParams["mathtext.default"] = "regular"
        matplotlib.rcParams["font.weight"] = "light"
        
def use_default_fonts():
    matplotlib.rcParams["mathtext.fontset"] = "dejavusans"
    matplotlib.rcParams["font.family"] = "DejaVu Sans"
    matplotlib.rcParams["mathtext.default"] = "it"
    matplotlib.rcParams["font.weight"] = "normal"


def apply_nicer_style(remove_right_upper_spines=True):
    sns.set_theme(style="whitegrid")

    if remove_right_upper_spines:
        custom_params = {"axes.spines.right": False, "axes.spines.top": False}
        sns.set_theme(style="ticks", rc=custom_params)

    # sns.set(font='Adobe Devanagari')
    sns.set_context("paper", font_scale=1, rc={"lines.linewidth": 0.5, "grid.linewidth": 0.3})


def _add_text_annotation(df_to_plot, data_array, ax, vmin, vmax):
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


def _smooth(data_array, symmetric, mask_lower_triangle, mask_upper_triangle, k_masking=-1):
    # make the matrix symmetric by replacing the lower triangle with the upper triangle
    data_smoothed = np.copy(data_array)
    data_smoothed[np.isnan(data_array)] = 0
    if symmetric:
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

    # Mask the lower triangle of the smoothed matrix
    # ! You might need to adjust the k_masking parameter if the matrix you work with is not symmetric
    if mask_lower_triangle:
        mask = np.tri(data_smoothed.shape[0], k=k_masking)
        return np.ma.masked_array(data_smoothed, mask=mask.T)
    elif mask_upper_triangle:
        mask = np.tri(data_smoothed.shape[0], k=k_masking)
        return np.ma.masked_array(data_smoothed, mask=mask)
    else:
        return data_smoothed


def _add_contours(ax, data_array, mx, green_contour, min_level=1, max_level=15, delta_levels=0.5):
    if green_contour is None:
        CSS = ax.contour(
            np.arange(0.5, data_array.shape[1]),
            np.arange(0.5, data_array.shape[0]),
            mx,
            colors="black",
            levels=list(np.arange(min_level, max_level, delta_levels)),
            linewidths=0.2,
        )
        ax.clabel(CSS, inline=True, fontsize=6)
    else:
        CSS = ax.contour(
            np.arange(0.5, data_array.shape[1]),
            np.arange(0.5, data_array.shape[0]),
            mx,
            colors="black",
            levels=list(np.arange(min_level, green_contour, delta_levels))
            + list(np.arange(green_contour + delta_levels, max_level, delta_levels)),
            linewidths=0.2,
        )
        ax.clabel(CSS, inline=True, fontsize=6)
        CS2 = ax.contour(
            np.arange(0.5, data_array.shape[1]),
            np.arange(0.5, data_array.shape[0]),
            mx,
            colors="green",
            levels=[green_contour],
            linewidths=1,
        )
        ax.clabel(CS2, inline=1, fontsize=6)

    return ax


def _add_diagonal_lines(ax, shift=1):
    ax.plot([0, 1000], [shift, 1000 + shift], color="tab:blue", linestyle="--", linewidth=1)
    ax.plot([0, 1000], [-10 + shift, 990 + shift], color="tab:blue", linestyle="--", linewidth=1)
    ax.plot([0, 1000], [-5 + shift, 995 + shift], color="black", linestyle="--", linewidth=1)
    return ax


def add_QR_code(fig, link):
    # Add QR code pointing to the github repository
    qr = qrcode.QRCode(
        # version=None,
        box_size=10,
        border=1,
    )
    qr.add_data(link)
    qr.make(fit=False)
    im = qr.make_image(fill_color="black", back_color="transparent")
    newax = fig.add_axes([0.9, 0.9, 0.05, 0.05], anchor="NE", zorder=1)
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


def plot_heatmap(
    dataframe_data,
    horizontal_variable,
    vertical_variable,
    color_variable,
    link=None,
    plot_contours=True,
    xlabel=None,
    ylabel=None,
    symmetric=True,
    mask_lower_triangle=True,
    mask_upper_triangle=False,
    plot_diagonal_lines=True,
    shift_diagonal_lines=1,
    xaxis_ticks_on_top=True,
    title="",
    vmin=4.5,
    vmax=7.5,
    k_masking=-1,
    green_contour: Optional[float] = 6.0,
    min_level_contours=1,
    max_level_contours=15,
    delta_levels_contours=0.5,
    figsize=None,
    label_cbar="Minimum DA (" + r"$\sigma$" + ")",
    colormap="coolwarm",
    style="ggplot",
    output_path="output.pdf",
    display_plot=True,
):
    # Use the requested style
    plt.style.use(style)

    # Get the dataframe to plot
    df_to_plot = dataframe_data.pivot(
        index=vertical_variable, columns=horizontal_variable, values=color_variable
    )

    # Get numpy array from dataframe
    data_array = df_to_plot.to_numpy()

    # Define colormap and set NaNs to white
    cmap = matplotlib.colormaps.get_cmap(colormap)
    cmap.set_bad("w")

    # Build heatmap, with inverted y axis
    fig, ax = plt.subplots()
    if figsize is not None:
        fig.set_size_inches(figsize)
    im = ax.imshow(data_array, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.invert_yaxis()

    # Filter out odd ticks and and label the rest with the respective list entries
    ax.set_xticks(np.arange(len(df_to_plot.columns))[::2], labels=df_to_plot.columns[::2])
    ax.set_yticks(np.arange(len(df_to_plot.index))[::2], labels=df_to_plot.index[::2])

    # Add text annotations
    ax = _add_text_annotation(df_to_plot, data_array, ax, vmin, vmax)

    # Smooth data for contours
    mx = _smooth(data_array, symmetric, mask_lower_triangle, mask_upper_triangle, k_masking)

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

    # Create colorbar
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.026, pad=0.04)
    cbar.ax.set_ylabel(label_cbar, rotation=90, va="bottom", labelpad=15)

    # Remove potential grid
    plt.grid(visible=None)

    # Add QR code with a link to the topright side (a bit experimental, might need adjustments)
    if link is not None:
        fig = add_QR_code(fig, link)

    # Save and potentially display the plot
    if output_path is not None:
        plt.savefig(output_path, bbox_inches="tight")

    if display_plot:
        plt.show()
    return fig, ax
