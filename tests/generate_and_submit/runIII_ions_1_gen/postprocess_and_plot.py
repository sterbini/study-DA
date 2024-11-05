# ==================================================================================================
# --- Imports
# ==================================================================================================
from study_da.plot import get_title_from_configuration, plot_heatmap
from study_da.postprocess import aggregate_output_data

# ==================================================================================================
# --- Postprocess the study
# ==================================================================================================

df_final = aggregate_output_data(
    "example_scan_1_gen/tree.yaml",
    l_group_by_parameters=["qx_b1", "qy_b1"],
    generation_of_interest=1,
    name_output="output_particles.parquet",
    write_output=True,
    only_keep_lost_particles=True,
)

# ==================================================================================================
# --- Plot
# ==================================================================================================

title = get_title_from_configuration(
    df_final,
    ions=True,
    betx_value=0.5,
    bety_value=0.5,
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
    display_emittance=True,
    display_chromaticity=True,
    display_octupole_intensity=True,
    display_coupling=True,
    display_filling_scheme=True,
    display_tune=False,
    display_luminosity_1=True,
    display_luminosity_2=True,
    display_luminosity_5=True,
    display_luminosity_8=True,
    display_PU_1=False,
    display_PU_2=False,
    display_PU_5=False,
    display_PU_8=False,
)

fig, ax = plot_heatmap(
    df_final,
    horizontal_variable="qx_b1",
    vertical_variable="qy_b1",
    color_variable="normalized amplitude in xy-plane",
    plot_contours=False,
    xlabel=r"Horizontal tune $Q_x$",
    ylabel=r"Vertical tune $Q_y$",
    tick_interval=1,
    symmetric_missing=True,
    mask_lower_triangle=True,
    shift_diagonal_lines=0,
    title=title,
    vmin=4,
    vmax=16,
    green_contour=2.0,
    label_cbar="Minimum DA (" + r"$\sigma$" + ")",
    output_path="1_gen_tune_scan.png",
    vectorize=False,
    fill_missing_value_with="interpolate",
)
