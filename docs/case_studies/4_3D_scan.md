# Doing a three-dimensional scan

Three-dimensional scans are more rarely requested, but they can be useful when scanning several interdependent variables. For instance, the optimal DA is known to depend on the vertical and horizontal tunes, but also on the octupoles. Yet the optimal tune will depend on the octupole current. In this case, a three-dimensional scan might be helpful.

Just like tune scans and octupole scans, they are usually done in two generations: the first one allows to convert the Mad sequence to a Xsuite collider (single job), while the second one enables to configure the collider and do the scan for whatever multidimensiontal parametric analysis you want to do. Let's give an example with the `config_hllhc13.yaml` configuration template (that you can find [here](../template_files/configurations/config_hllhc13.md)).

## Scan configuration

As usual, let's first configure our scan.

```yaml title="config_scan.yaml"
# ==================================================================================================
# --- Structure of the study ---
# ==================================================================================================
name: example_3D_scan

# List all useful files that will be used by executable in generations below
# These files are placed at the root of the study
dependencies:
  main_configuration: config_hllhc13.yaml

structure:
  # First generation is always at the root of the study
  # such that config_hllhc16.yaml is accessible as ../config_hllhc16.yaml
  generation_1:
    executable: generation_1.py
    common_parameters:
      # Needs to be redeclared as it's used for parallelization
      # And re-used ine the second generation
      n_split: 5

  # Second generation depends on the config from the first generation
  generation_2:
    executable: generation_2_level_by_nb.py
    scans:
      distribution_file:
        # Number of paths is set by n_split in the main config
        path_list: ["____.parquet", n_split]
      qx:
        subvariables: [lhcb1, lhcb2]
        linspace: [62.310, 62.325, 11]
      qy:
        subvariables: [lhcb1, lhcb2]
        expression: qx - 2 + 0.005
        concomitant: [qx]
      i_oct_b1:
        linspace: [-300, 300, 6]
      i_oct_b2:
        linspace: [-300, 300, 6]
        concomitant: [i_oct_b1]
      nemitt_x:
        linspace: [2.e-6, 3.e-6, 6]
      nemitt_y:
        expression: nemitt_x
        concomitant: [nemitt_x]
```

You might find the scan in the ```generation_2``` section a bit more complex than usual, but all the keywords should be relatively clear by now. Note that I used an ```expression``` for the definition of ```nemitt_y```in term of ```nemitt_x```. This is a way to define a variable in term of another one, which is useful when you want to keep the same value for both variables. It's simpler than defining a ```linspace``` with the same value for the two variables, as done with the octupoles.

## Study generation

We can now write the script to generate the study:

```python title="tune_oct_emit_scan.py"
# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import os

# Import third-party modules
# Import user-defined modules
from study_da import create, submit
from study_da.utils import load_template_configuration_as_dic, write_dic_to_path

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================

# Load the template configuration
name_template_config = "config_hllhc13.yaml"
config, ryaml = load_template_configuration_as_dic(name_template_config)

# Update the location of acc-models since it's copied in a different folder
config["config_mad"]["links"]["acc-models-lhc"] = (
    "../../../../../external_dependencies/acc-models-lhc-v13"
)

# Drop the configuration locally
write_dic_to_path(config, name_template_config, ryaml)

# Now generate the study in the local directory
path_tree, name_main_config = create(path_config_scan="config_scan.yaml", force_overwrite=False)

# Delete the configuration
os.remove(name_template_config)

# ==================================================================================================
# --- Script to submit the study
# ==================================================================================================

# In case gen_1 is submitted locally
dic_additional_commands_per_gen = {
    # To clean up the folder after the first generation if submitted locally
    1: "rm -rf final_* modules optics_repository optics_toolkit tools tracking_tools temp mad_collider.log __pycache__ twiss* errors fc* optics_orbit_at* \n"
}

# Dependencies for the executable of each generation. Only needed if one uses HTC or Slurm.
dic_dependencies_per_gen = {
    1: ["acc-models-lhc"],
    2: ["path_collider_file_for_configuration_as_input", "path_distribution_folder_input"],
}

# Submit the study
submit(
    path_tree=path_tree,
    path_python_environment="/afs/cern.ch/work/c/cdroin/private/study-DA/.venv",
    path_python_environment_container="/usr/local/DA_study/miniforge_docker",
    path_container_image="/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cdroin/da-study-docker:0878a028",
    dic_dependencies_per_gen=dic_dependencies_per_gen,
    name_config=name_main_config,
    dic_additional_commands_per_gen=dic_additional_commands_per_gen,
)
```

There shouldn't be anything new to understand here.

## Study post-processing and plotting

The code for post-processing and plotting is a bit different:

```python title="postprocess_and_plot.py"
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
    surface_count=20,
    display_plot=False,
    figsize=(750, 750),
)
```

As you can see, we need to aggregate the data for all the relevant variables in the `l_group_by_parameters` list. However, in this scan, several points are missing, due to either failed jobs (e.g. mismatched due to tune value) or no lost particles. Therefore, a bit more of postprocessing is needed before being able to do the plotting. This postprocessing will be very specific to your study, so you might need to adapt it.

Finally, the 3D plotting function should be relatively straightforward to use, especially if you've used Plotly in the past. Note that a high number of `surface_count` will make the plot more detailed, but also heavier. Also note that the rendering of Latex equations is a bit capricious... So we didn't include a title in this plot(although it's possible, but you will have to play around with the latex string, and this is not the purpose of this tutorial).

Just for illustration, here is the output of the plot (interactive, although the png is also available):

<iframe src="plots/3D.html" style="border:none;width:750px;height:750px;display:block;"></iframe>
