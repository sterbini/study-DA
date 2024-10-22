# Doing a tune scan

Tune scans are usually done in two generations: the first one allows to convert the Mad sequence to a Xsuite collider (single job), while the second one enables to configure the collider and do the tracking (scan, since many tunes are tested). Let's give an example with the ```config_hllhc16.yaml``` configuration template.

First, let's configure our scan:

```yaml title="config_scan.yaml"
# ==================================================================================================
# --- Structure of the study ---
# ==================================================================================================
name: example_tune_scan

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
    scans:
      distribution_file:
        # Number of paths is set by n_split in the main config
        path_list: ["____.parquet", n_split]
      qx:
        subvariables: [lhcb1, lhcb2]
        linspace: [62.31, 62.32, 11]
      qy:
        subvariables: [lhcb1, lhcb2]
        linspace: [60.31, 60.32, 11]
```

Here, ```generation_1.py``` and ```generation_2_level_by_nb.py``` are the same template scripts as in the [1_simple_collider.md](1_simple_collider.md) case study. The only difference is that the second generation will now be mutated in each job of generation 2 to scan the tunes. If no specific keyword is provided (as in here), it's the cartesian product of all the variables that will be scanned.

In addition, you might notice that the ```n_split```parameters is declared as a "common_parameters" in the first generation. This is because it is used for parallelization and needs to be re-used in the second generation (in this case, each job will track 1/5th of the particles distribution, which corresponds to the files ```00.parquet```, ```01.parquet```, etc.).

Therefore, there we will scan 11 tunes in both the horizontal and vertical planes, and each of the 121 combinations will be tracked on a partial particle distribution in five separate jobs (for parallelization).

We can now write the script to generate the study:

```py title="tune_scan.py"
# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import os

# Import third-party modules
# Import user-defined modules
from study_da import create
from study_da.utils import write_dic_to_path, load_template_configuration_as_dic

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================

# Load the configuration from hllhc16
name_template_config = "config_hllhc16.yaml"
config, ryaml = load_template_configuration_as_dic(name_template_config)

# Update the location of acc-models
config["config_mad"]["links"]["acc-models-lhc"] = "path/to/acc-models-lhc"

# Adapt the number of turns
config["config_simulation"]["n_turns"] = 200000

# Drop the configuration locally
write_dic_to_path(config, "config_hllhc16.yaml", ryaml)

# Now generate the study in the local directory
path_tree, name_main_config = create(path_config_scan="config_scan.yaml", force_overwrite=True)

# Delete the configuration
os.remove("config_hllhc16.yaml")
```

At this point, the directory with all the jobs should be created, along with the corresponding tree file.

We can now submit the jobs. Ideally, we would like to submit the first generation 