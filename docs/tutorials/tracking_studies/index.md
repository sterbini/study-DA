# A dummy tracking study

## Introduction

Now that the concepts have been introduced, let's see how to use the package for a dummy tracking study. This will help you understand how the package works and how to use it for an actual collider configuration.

## Creating the study

### Template scripts

The tracking is usually done in two generations to optimize the process. In the first generation, the collider is created from a MAD-X sequence. In the second generation, the tracking is performed. We will use one script per generation, and the same configuration file for both generations (although it will be mutated in the second generation to scan over some parameters).

#### Generation 1

Generation 1 usually corresponds to the step in which the Xsuite collider is created from a MAD-X sequence, and the particle distribution is created. At this step, only a few checks are performed, and the collider is not yet ready for tracking studies. For this example, we will work with the [template script provided in the package to create the collider](../../template_files/scripts/generatation_1.md).

This script should very much be self-explanatory, especially if you have understood the concepts explained in the previous sections, and already have a basic knowledge of Mad-X and Xsuite. Basically, it loads the configuration file, mutates it with the parameters provided in the scan configuration (explained a bit below), and then builds the particle distribution and the collider. You are invited to check the details of the functions (e.g. on the [GitHub repository](https://github.com/ColasDroin/study-DA/tree/master/study_da/generate/master_classes) of the package) to better understand what is happening.

The collider configuration file is then saved with the mutated parameters, so that the subsequent generation can use it.

!!! info "These template scripts should be adapted to your needs"

    The template scripts provided in the package are just that: templates. They should be adapted to your needs, especially if you have a more complex collider configuration. For example, you might want to add some checks to ensure that the collider is correctly built, or that the particle distribution is correctly generated. You might also want to add some logging to keep track of what is happening in the script. You're basically free to not use at all the convenience functions provided with the package. 

#### Generation 2

Generation 2 corresponds to the step in which the collider is configured and the tracking is performed. For this example, we will still work with the [template script provided in the package to perform the tracking](../../template_files/scripts/generatation_2_level_by_nb.md).

Again, this script should be relatively self-explanatory. Basically, it loads the configuration file, mutates it with the parameters provided in the scan configuration, and then configures the collider and tracks the particles.

The collider configuration is itself done in several steps:

    - The collider is loaded from the file created in the first generation
    - The beam-beam elements are installed (but remain inactive for now)
    - The trackers are built for running Xsuite Twiss
    - The knobs are set. This is where the mutation of the parameters usually has some impact, for instance when you scan the tune, you modify the knobs here.
    - The tune and chromaticity are matched
    - The filling scheme is set
    - The number of collisions in the IPs is computed
    - The leveling is done if requested
    - The linear coupling is added
    - The tune and chromaticity are rematched
    - The beam-beam is computed and activated if needed
    - The final luminosity is recorded
    - The collider is saved to disk
  
Again, you are invited to check the details of the functions if you want to know more. After this configuration step, the particles are tracked and the output is saved to disk.

### Template configuration

The configuration file is a YAML file that contains all the parameters needed to configure the collider and run the tracking. It is loaded in both generations, and mutated in the second generation to scan over some parameters. In this example, we will work with the [template configuration provided for LHC run III](../../template_files/configurations/config_runIII.yaml).

Although it's probably better if you understand the role of each individual parameter in the file, all you have to know for now is that this is a fairly standard configuration for an end-of-levelling tracking. However, you will *definitely* have to adapt it to your needs for your own scans.

### Scan configuration

The scan configuration is not provided as a template since this is completely dependent on the study. We provide here an example in the case of a scan over the horizontal tune for a varying number of turns.

```yaml title="config_scan.yaml"
# ==================================================================================================
# --- Structure of the study ---
# ==================================================================================================
name: example_dummy_scan

# List all useful files that will be used by executable in generations below
# These files are placed at the root of the study
dependencies:
  main_configuration: config_runIII.yaml

structure:
  # First generation is always at the root of the study
  # such that config_hllhc16.yaml is accessible as ../config_hllhc16.yaml
  generation_1:
    executable: generation_1.py
    common_parameters:
      # Needs to be redeclared as it's used for parallelization
      # And re-used ine the second generation
      n_split: 2

  # Second generation depends on the config from the first generation
  generation_2:
    executable: generation_2_level_by_nb.py
    scans:
      distribution_file:
        # Number of paths is set by n_split in the main config
        path_list: ["____.parquet", n_split]
      qx:
        subvariables: [lhcb1, lhcb2]
        linspace: [62.305, 62.330, 6]
      n_turns:
        list: [1000, 20000, 50000, 100000]
```

!!! info "Scanning the number of turns makes no sense"

    This is just an example to show you how to scan over some parameters. In practice, scanning the number of turns makes no sense, as you could just do one scan with a large number of turns and regularly save the output to disk (e.g. every 1000 turns).

Thre are several things to notice. First, and contrary to the dummy studies presented in the concepts, we don't run an parametric scan in the first generation: we just take the collider with the configuration as it is. However, there is an exception for the `n_split` parameter, which is used for parallelization. This parameter is redeclared in the `common_parameters` of the first generation, and then used in the second generation. This is because it is used for parallelization and needs to be re-used in the second generation (in this case, each job will track one half of the particles distribution, which corresponds to the files ```00.parquet``` and ```01.parquet```).

Then, in this case, the executables ```generation_1.py``` and ```generation_2_level_by_nb.py``` are directly provided by the package (we don't need to place them in the same folder as the configuration, altough we could).

Finally, you might notice that two parameters are being scanned in the second generation (the horizontal tune and the number of turns). In this case, if no specific keyword is provided (see the [case studies](../../case_studies/index.md) for example of keywords), it's the cartesian product of all the parameters that is being scanned.