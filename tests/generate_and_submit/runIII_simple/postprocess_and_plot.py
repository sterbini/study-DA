# ==================================================================================================
# --- Imports
# ==================================================================================================
from study_da.plot import get_title_from_configuration, plot_heatmap
from study_da.postprocess import aggregate_output_data

# ==================================================================================================
# --- Postprocess the study
# ==================================================================================================

df_final = aggregate_output_data(
    "example_dummy_scan/tree.yaml",
    l_group_by_parameters=["qx_b1", "n_turns"],
    generation_of_interest=2,
    name_output="output_particles.parquet",
    write_output=True,
    only_keep_lost_particles=True,
    force_overwrite=False,
)

# ==================================================================================================
# --- Plot
# ==================================================================================================

title = get_title_from_configuration(
    df_final,
    betx_value=0.485,
    bety_value=0.485,
    crossing_type="vh",
    display_LHC_version=True,
    display_energy=True,
    display_bunch_index=True,
    display_CC_crossing=False,
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
    display_octupole_intensity=False,
    display_coupling=True,
    display_filling_scheme=True,
    display_horizontal_tune=True,
    display_luminosity_1=True,
    display_luminosity_2=True,
    display_luminosity_5=True,
    display_luminosity_8=True,
    display_PU_1=True,
    display_PU_2=True,
    display_PU_5=True,
    display_PU_8=True,
)

fig, ax = plot_heatmap(
    df_final,
    horizontal_variable="n_turns",
    vertical_variable="qx_b1",
    color_variable="normalized amplitude in xy-plane",
    link="www.link-to-your-study.com",
    position_qr="bottom-right",
    plot_contours=True,
    xlabel="Number of turns",
    ylabel=r"$Q_x$",
    title=title,
    vmin=4.0,
    vmax=8.0,
    green_contour=6.0,
    label_cbar="Minimum DA (" + r"$\sigma$" + ")",
    output_path="qx_turns.png",
    vectorize=False,
    xaxis_ticks_on_top=False,
    plot_diagonal_lines=False,
)
