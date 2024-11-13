# Doing GPU tracking

In this case study, we show how to do a small two-generational tune scan using GPU for the tracking with a very large initial distribution for the particles. We're going to do this tracking on HTCondor, but the procedure would be fairly similar when tracking on a local machine. We use the usual HLLHC v1.6 configuration (with a few tweaks for the GPU tracking, shown later).

## Scan configuration

We could use the same type of configuration as in the [tune scan case study](./2_tune_scan.md), but we're going to show a more general case, in which we define the parameters in the generating script. Therefore, the scan configuration will be very simple:

```yaml title="config_scan.yaml"
# ==================================================================================================
# --- Structure of the study ---
# ==================================================================================================
name: example_GPU_scan

# List all useful files that will be used by executable in generations below
# These files are placed at the root of the study
dependencies:
  main_configuration: config_hllhc16_GPU.yaml

structure:
  # First generation is always at the root of the study
  # such that config_hllhc16.yaml is accessible as ../config_hllhc16.yaml
  generation_1:
    executable: generation_1.py

  # Second generation depends on the config from the first generation
  generation_2:
    executable: generation_2_level_by_nb.py
```

Note that we don't even define the `n_split` parameter here, as we won't parallelize the jobs on CPUs by splitting the distribution (the whole point of GPUs is to be able to track many particles in parallel).

## Study configuration

I won't show the whole configuration as it overall very similar to the [template one](../template_files/configurations/config_hllhc16.md), but only the adjustments needed for the GPU tracking. 

First, we want to use a very large initial particles distribution. We use the same type of distribution as in other examples (particles distributed uniformly radially and on a given number of angles), but you're highly encouraged to use a more realistic distribution for your studies (and therefore adapt the configuration for your needs, e.g. define the parameters of a coviariance matrix of a multivariate normal distribution).

```yaml title="config_hllhc16_GPU.yaml"
config_particles:
  r_min: 4.0
  r_max: 8.0
  n_r: 500
  n_angles: 40
  n_split: 1
  path_distribution_folder_output: particles
```

Finally, we want to change the context to use `cupy`:

```yaml title="config_hllhc16_GPU.yaml"
config_simulation:
  context: "cupy" 
```

And we're done. We can now generate the study.

## Study generation

The script to generate the study is a bit trickier than usual since, this time, we decided to define the parameter space inside of the script (and not in the scan configuration file, as usual). 

This is not just for demonstrating the flexibility of the tool, but also because if we were to do this scan locally, we would have to give a `device_number` different for each job. This is not possible with our usual scan configuration file, since one variable will evolve with all the others *at once*.

```python title="GPU_scan.py"
# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import os

# Import third-party modules
# Import user-defined modules
from study_da import create, submit

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================
# Generate the arrays of parameters to scan
l_device_number = []
l_qx = []
l_qy = []
l_qx_for_naming = []
l_qy_for_naming = []
device_number = 0
for qx in [62.310, 62.311]:
    for qy in [60.320, 60.321]:
        # Distribute the simulation over the GPUs, knowing that only 4 GPUs are available
        l_device_number.append(device_number % 4)
        l_qx.append({key: qx for key in ["lhcb1", "lhcb2"]})
        l_qy.append({key: qy for key in ["lhcb1", "lhcb2"]})
        l_qx_for_naming.append(qx)
        l_qy_for_naming.append(qy)
        device_number += 1

# Store the parameters in a dictionary
dic_parameter_all_gen = {
    "generation_2": {
        # "device_number": l_device_number,
        "qx": l_qx,
        "qy": l_qy,
    }
}

dic_parameter_all_gen_naming = {
    "generation_2": {
        # "device_number": l_device_number,
        "qx": l_qx_for_naming,
        "qy": l_qy_for_naming,
    }
}

# Generate the study in the local directory
path_tree, name_main_config = create(
    path_config_scan="config_scan.yaml",
    force_overwrite=False,
    dic_parameter_all_gen=dic_parameter_all_gen,
    dic_parameter_all_gen_naming=dic_parameter_all_gen_naming,
)

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
    2: ["path_collider_file_for_configuration_as_input", "path_distribution_folder_input"],
}


# Preconfigure submission to HTC
dic_config_jobs = {
    "generation_1" + ".py": {
        # We leave CPU for gen 1 context as it doesn't do tracking
        "gpu": False,
        "submission_type": "local",
    },
    "generation_2" + ".py": {
        # We use GPU for gen 2 context as it does tracking
        # Note that the context is also set in the config file
        "gpu": True,
        "submission_type": "htc_docker",
        "htc_flavor": "tomorrow",
    },
}

# Submit the study
submit(
    path_tree=path_tree,
    path_python_environment="/afs/cern.ch/work/c/cdroin/private/study-DA/.venv",
    path_python_environment_container="/usr/local/DA_study/miniforge_docker",
    path_container_image="/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cdroin/da-study-docker:df1378e8",
    dic_dependencies_per_gen=dic_dependencies_per_gen,
    name_config=name_main_config,
    dic_additional_commands_per_gen=dic_additional_commands_per_gen,
    dic_config_jobs=dic_config_jobs,
)
```

As you can see, the first part of the script is used to define the parameter space. We basically do the usual cartesian product of the tunes manually, but we set a new device number every time. Because we don't want the `lhcb1` or `lhcb2` strings to appear in the filenames when generating the study, we also define a dictionnary of parameters for the naming of the files.

!!! info "The device number is commented out"
    
    As you can see, the `device_number` is commented out in the `dic_parameter_all_gen` dictionary. This is because use HTCondor in this simulation, and therefore we don't need to specify the device number in the configuration file. If you were to run this simulation locally, you would need to uncomment this line.

The second part of the script, for the submission, should be straightforward.

## Post-processing

Postprocessing is done as usual, except that we're not going to plot a result this time (since the analysis you want to run with the output data is highly dependent on the study you're doing). The aggregation of the data is done as follows:

```python title="postprocess.py"
from study_da.postprocess import aggregate_output_data

df_final = aggregate_output_data(
    "example_GPU_scan/tree.yaml",
    l_group_by_parameters=["qx_b1", "qy_b1"],
    generation_of_interest=2,
    name_output="output_particles.parquet",
    write_output=True,
    only_keep_lost_particles=False,
)

# Do whatever you want we df_final
```

And that's it! You should now be able to run a GPU tracking study with a very large initial distribution of particles.
