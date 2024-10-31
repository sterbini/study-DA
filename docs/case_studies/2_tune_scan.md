# Doing a tune scan

Tune scans are usually done in two generations: the first one allows to convert the Mad sequence to a Xsuite collider (single job), while the second one enables to configure the collider and do the tracking (scan, since many tunes are tested). Let's give an example with the ```config_hllhc16.yaml``` configuration template.

## Study configuration

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
        linspace: [62.305, 62.330, 26]
      qy:
        subvariables: [lhcb1, lhcb2]
        linspace: [60.305, 60.330, 26]
        condition: qy >= qx - 2 + 0.0039
```

Here, ```generation_1.py``` and ```generation_2_level_by_nb.py``` are the same template scripts as in the [1_simple_collider.md](1_simple_collider.md) case study. The only difference is that the second generation will now be mutated in each job of generation 2 to scan the tunes. If no specific keyword is provided, it's the cartesian product of all the variables that will be scanned. In this case, since we added a condition on the tunes (because we're only interest in the working points above the super-diagonal), the scan will be done on the tune combinations that satisfy the condition.

In addition, you might notice that the ```n_split``` parameter is declared as a "common_parameters" in the first generation. This is because it is used for parallelization and needs to be re-used in the second generation (in this case, each job will track 1/5th of the particles distribution, which corresponds to the files ```00.parquet```, ```01.parquet```, etc.).

## Study generation

We can now write the script to generate the study:

```py title="tune_scan.py"
# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import os

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

# Adapt the number of turns if needed
config["config_simulation"]["n_turns"] = 1000000

# Drop the configuration locally
write_dic_to_path(config, name_template_config, ryaml)

# Now generate the study in the local directory
path_tree, name_main_config = create(path_config_scan="config_scan.yaml")

# Delete the configuration
os.remove(name_template_config)
```

Running this, the directory with all the jobs should be created, along with the corresponding tree file.

## Study submission

We can now submit the jobs. Ideally, we would like to submit the first generation as a local job (since there's only one job, no need to queue on a cluster), and the second generation on a cluster. However, contrarily to the [previous example](1_simple_collider.md), we're going to be lazy this time and not configure in advance the submission of the jobs. Therefore, ```study-da``` will ask you how you want to submit the jobs when you try to submit them. This is all in the following script (continuing from the previous one):

```py title="tune_scan.py"
# ==================================================================================================
# --- Script to submit the study
# ==================================================================================================

# In case gen_1 is submitted locally
dic_additional_commands_per_gen = {
    # To clean up the folder after the first generation if submitted locally
    1: "rm -rf final_* modules optics_repository optics_toolkit tools tracking_tools temp mad_collider.log __pycache__ twiss* errors fc* optics_orbit_at* \n"
    # To copy back the particles folder from the first generation if submitted to HTC
    # "cp -r particles $path_job/particles \n",
}

# Dependencies for the executable of each generation. Only needed if one uses HTC or Slurm.
dic_dependencies_per_gen = {
    1: ["acc-models-lhc"],
    2: ["path_collider_file_for_configuration_as_input", "path_distribution_folder_input"],
}

# Dic copy_back_per_gen (only matters for HTC)
dic_copy_back_per_gen = {
    1: {"parquet": True, "yaml": True, "txt": True, "json": True, "zip": True},
    2: {"parquet": True, "yaml": True, "txt": True, "json": False, "zip": False},
}

# Submit the study
submit(
    path_tree=path_tree,
    path_python_environment="/afs/cern.ch/work/u/user/private/study-DA/.venv",
    path_python_environment_container="/usr/local/DA_study/miniforge_docker",
    path_container_image="/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cdroin/da-study-docker:ad541f20",
    dic_dependencies_per_gen=dic_dependencies_per_gen,
    name_config=name_main_config,
    dic_additional_commands_per_gen=dic_additional_commands_per_gen,
    dic_copy_back_per_gen=dic_copy_back_per_gen,
)
```

In this script, the ```dic_additional_commands_per_gen``` is used to clean up the folder after the first generation (since we're going to submit it locally), but it could also have been use to copy back the particles folder from the first generation if we were to submit to HTC. This is needed since HTC generations run indendently from each other, and the second generation doesn't have access to the files generated by the first generation.

The ```dic_dependencies_per_gen``` is only needed if one uses HTC, and basically specifies which path should be mutated to be absolute in the configuration file of the executable, so that the executable can find the files it needs even if it's being run from a distant node.

The ```dic_copy_back_per_gen``` is also only needed for HTC, and specifies which types files should be copied back to the local folder after the job is done (independently of whatever command has been inserted into the ```dic_additional_commands_per_gen```, which just provides you with more freedom and, in this case, could have been needed for the particles forlder here since the ```dic_copy_back_per_gen``` doesn't handle folders).

Finally, note that we must provide the paths to not only the local python environment (since we're submitting the first generation locally), but also to the container image (to pull the image from the registry) and the python environment in the container. This is because, in this example, we will decide to submit the second generation to HTC with Docker.

Also note that in this case, we didn't specify ```keep_submit_until_done=True``` in the ```submit``` function, so the script will only submit one batch (most likely, generation) of jobs and stop running. However, you can run the script several times with no consequences: jobs that are already finished, or currently running or queuing, will not be resubmitted. When the study is finished, the script simply tells you (and warns you if some jobs were problematic).

## Study post-processing and plotting

The following script shoud allow you to post-process the study (gather all the output data from each individual job) and plot the results:

```py title="postprocess_and_plot.py"

```
