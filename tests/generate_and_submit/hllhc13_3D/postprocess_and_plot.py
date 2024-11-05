# ==================================================================================================
# --- Imports
# ==================================================================================================
from study_da.plot import get_title_from_configuration, plot_3D
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

# ==================================================================================================
# --- Plot
# ==================================================================================================

title = get_title_from_configuration(
    df_final,
    betx_value=0.15,
    bety_value=0.15,
    display_LHC_version=True,
    display_energy=True,
    display_bunch_index=True,
    display_CC_crossing=True,
    display_bunch_intensity=True,
    display_beta=True,
    display_crossing_IP_1=True,
    display_crossing_IP_2=True,
    display_crossing_IP_5=True,
    display_crossing_IP_8=True,
    display_bunch_length=True,
    display_polarity_IP_2_8=True,
    display_emittance=False,
    display_chromaticity=True,
    display_octupole_intensity=False,
    display_coupling=True,
    display_filling_scheme=True,
    display_tune=False,
    display_luminosity_1=True,
    display_luminosity_2=True,
    display_luminosity_5=True,
    display_luminosity_8=True,
    display_PU_1=True,
    display_PU_2=True,
    display_PU_5=True,
    display_PU_8=True,
)

plot_3D(
    df_final,
    "qx_b1",
    "i_oct_b1",
    "nemitt_x",
    "normalized amplitude in xy-plane",
    xlabel=r"$Q_x$" + "with " + r"$Q_y = Q_x -2 + 0.005$",
    ylabel="Octupole intensity [A]",
    z_label=r"Normalized emittance [$\mu$m]",
    title=title,
    vmin=4,
    vmax=8,
    output_path="output.png",
    output_path_html="output.html",
    display_plot=False,
)
