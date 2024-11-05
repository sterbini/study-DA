# Doing a three-dimensional scan

Three-dimensional scans are more rarely requested, but they can be useful when scanning several interdependent variables. For instance, the optimal DA is known to depend on the vertical and horizontal tunes, but also on the octupoles. Yet the optimal tune will depend on the octupole current. In this case, a three-dimensional scan might be helpful.

Just like tune scans and octupole scans, they are usually done in two generations: the first one allows to convert the Mad sequence to a Xsuite collider (single job), while the second one enables to configure the collider and do the scan for whatever multidimensiontal parametric analysis you want to do. Let's give an example with the `config_hllhc13.yaml` configuration template (that you can find [here](../template_files/configurations/config_hllhc13.md)).

## Study configuration

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

