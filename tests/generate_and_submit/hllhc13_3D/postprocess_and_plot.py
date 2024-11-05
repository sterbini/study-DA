# ==================================================================================================
# --- Imports
# ==================================================================================================
import pandas as pd

from study_da.plot import plot_3D
from study_da.postprocess import aggregate_output_data

# ==================================================================================================
# --- Postprocess the study
# ==================================================================================================

df_final = aggregate_output_data(
    "example_3D_scan/tree.yaml",
    l_group_by_parameters=["qx_b1", "qy_b1", "i_oct_b1", "i_oct_b2", "nemitt_x", "nemitt_y"],
    generation_of_interest=2,
    name_output="output_particles.parquet",
    write_output=True,
    only_keep_lost_particles=True,
)


# Some more manual postprocessing to fill the missing values
df_final = df_final[["qx_b1", "i_oct_b1", "nemitt_x", "normalized amplitude in xy-plane"]]
df_final = df_final.drop_duplicates()
df_final = df_final.set_index(["qx_b1", "i_oct_b1", "nemitt_x"])
idx = pd.MultiIndex.from_product(
    [df_final.index.levels[0], df_final.index.levels[1], df_final.index.levels[2]]
)
df_final = df_final.reindex(idx, fill_value=None).reset_index()

# Interpolate missing values in df_final for the column "normalized amplitude in xy-plane"
df_final["normalized amplitude in xy-plane"] = df_final.groupby(["qx_b1", "i_oct_b1"])[
    "normalized amplitude in xy-plane"
].transform(lambda x: x.interpolate(method="linear", limit_direction="both"))

# Fill remaining missing values with 8 as it corresponds to simulation with no lost particles
df_final["normalized amplitude in xy-plane"] = df_final["normalized amplitude in xy-plane"].fillna(
    8
)
# ==================================================================================================
# --- Plot
# ==================================================================================================


fig = plot_3D(
    df_final,
    "qx_b1",
    "i_oct_b1",
    "nemitt_x",
    "normalized amplitude in xy-plane",
    xlabel=r"Qx",
    ylabel=r"I [A]",
    z_label=r"Normalized emittance [μm]",
    vmin=3.9,
    vmax=8.1,
    output_path="3D.png",
    output_path_html="3D.html",
    surface_count=10,
    display_plot=False,
    display_colormap=False,
    figsize=(600, 600),
)
