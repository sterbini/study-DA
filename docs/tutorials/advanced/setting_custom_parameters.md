# Setting custom parameters

## Introduction

The possibilities offered by study-DA to scan parameters might sometimes be limited. For instance, you might want to input a parameter as a complex function of another parameter. Or you might want to load parametric values from a file. In such cases, you can set custom parameters instead of using a keyword to scan them in the scan configuration file.

## Scan configuration

For this example, we decide to use a scan configuration that is very simple, based on the [template configuration provided for HL-LHC v1.6](../../template_files/configurations/config_hllhc16.md):

```yaml title="config_scan.yaml"
# ==================================================================================================
# --- Structure of the study ---
# ==================================================================================================
name: example_custom_parameters

# List all useful files that will be used by executable in generations below
# These files are placed at the root of the study
dependencies:
  main_configuration: config_hllhc16.yaml

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
```

## Generating script

We're now going to introduce how to input custom parameters in the generating script. In this example, we want to scan the tunes `qx` and `qy` for the LHCb1 and LHCb2 beams. In addition, we have to pay attention not to neglect the `n_split` parameter used for parallelization.

```python title="custom_parameters.py"
# ==================================================================================================
# --- Imports
# ==================================================================================================

from study_da import create

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================
# Generate the arrays of parameters to scan
l_qx = []
l_qy = []
l_qx_for_naming = []
l_qy_for_naming = []
l_n_split = []
l_n_split_for_naming = []

for qx in [62.310, 62.311]:
    for qy in [60.320, 60.321]:
        for n_split in range(5):
            l_qx.append({key: qx for key in ["lhcb1", "lhcb2"]})
            l_qy.append({key: qy for key in ["lhcb1", "lhcb2"]})
            l_qx_for_naming.append(qx)
            l_qy_for_naming.append(qy)
            l_n_split.append(f"{n_split:02d}.parquet")
            l_n_split_for_naming.append(n_split)

# Store the parameters in a dictionary
dic_parameter_all_gen = {
    "generation_2": {
        "qx": l_qx,
        "qy": l_qy,
        "n_split": l_n_split,
    }
}

dic_parameter_all_gen_naming = {
    "generation_2": {
        "qx": l_qx_for_naming,
        "qy": l_qy_for_naming,
        "n_split": l_n_split_for_naming,
    }
}

# Generate the study in the local directory
path_tree, name_main_config = create(
    path_config_scan="config_scan.yaml",
    dic_parameter_all_gen=dic_parameter_all_gen,
    dic_parameter_all_gen_naming=dic_parameter_all_gen_naming,
)

```

As you can see, the first part of the script is used to define the parameter space. We basically do the usual cartesian product of the tunes and n_split parameters manually. Because we don't want the `lhcb1` or `lhcb2` strings to appear in the filenames when generating the study, we also define a dictionnary of parameters for the naming of the files.

In practice, you can customize the parameters as you wish, as long as you respect the structure of the dictionary `dic_parameter_all_gen` and `dic_parameter_all_gen_naming` (although the latter is optional, but can lead to very long or inconstistent filenames if not used).

You can then generate your study as usual.
