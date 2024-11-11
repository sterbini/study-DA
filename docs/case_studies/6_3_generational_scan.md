# Doing an 3-generational scan

In this case study, we will perform a 3-generational scan. Because the parameter space grows exponentially, we will just do a dummy scan with very few points, and no final plotting. The idea is just to demonstrate how to adapt the files to perform a 3-generational scan.

## Scan configuration

The scan configuration is as follows:

```yaml title="config_scan.yaml"
# ==================================================================================================
# --- Structure of the study ---
# ==================================================================================================
name: example_scan_3_gen

# List all useful files that will be used by executable in generations below
# These files are placed at the root of the study
dependencies:
  main_configuration: custom_files/config_hllhc16_3_gen.yaml

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
    executable: custom_files/generation_2_configure.py
    scans:
      distribution_file:
        # Number of paths is set by n_split in the main config
        path_list: ["____.parquet", n_split]
      qx:
        subvariables: [lhcb1, lhcb2]
        linspace: [62.31, 62.32, 2]

  # Third generation depends on the config from the second generation
  generation_3:
    executable: custom_files/generation_3_track.py
    scans:
      delta_max:
        list: [27.e-5, 28.e-5]
```

Nothing fancy here, except that, as you can see, we now have split our usual generation_2 into two generations, `generation_2_configure.py` and `generation_3_track.py`. In the tracking generation, we will scan the `delta_max` (initial off-momentum) parameter.

## Template scripts

The first generation template script is [the usual](../template_files/scripts/generation_1.md), so I'm not going to show it here. The second generation template script is as follows:

```python title="generation_2_configure.py"
"""This is a template script for generation 1 of simulation study, in which ones generates a
particle distribution and a collider from a MAD-X model."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import contextlib
import logging
import os

# Import third-party modules
# Import user-defined modules
from study_da.generate import XsuiteCollider
from study_da.utils import (
    load_dic_from_path,
    set_item_in_dic,
    write_dic_to_path,
)

# Set up the logger here if needed


# ==================================================================================================
# --- Script functions
# ==================================================================================================
def configure_collider(full_configuration):
    # Get configuration
    config_collider = full_configuration["config_collider"]
    ver_hllhc_optics = full_configuration["config_mad"]["ver_hllhc_optics"]
    ver_lhc_run = full_configuration["config_mad"]["ver_lhc_run"]
    ions = full_configuration["config_mad"]["ions"]
    collider_filepath = full_configuration["config_collider"][
        "path_collider_file_for_configuration_as_input"
    ]

    # Build object for configuring collider
    xc = XsuiteCollider(config_collider, collider_filepath, ver_hllhc_optics, ver_lhc_run, ions)

    # Load collider
    collider = xc.load_collider()

    # Install beam-beam
    xc.install_beam_beam_wrapper(collider)

    # Build trackers
    # For now, start with CPU tracker due to a bug with Xsuite
    # Refer to issue https://github.com/xsuite/xsuite/issues/450
    collider.build_trackers()  # (_context=context)

    # Set knobs
    xc.set_knobs(collider)

    # Match tune and chromaticity
    xc.match_tune_and_chroma(collider, match_linear_coupling_to_zero=True)

    # Set filling scheme
    xc.set_filling_and_bunch_tracked(ask_worst_bunch=False)

    # Compute the number of collisions in the different IPs
    n_collisions_ip1_and_5, n_collisions_ip2, n_collisions_ip8 = xc.compute_collision_from_scheme()

    # Do the leveling if requested
    if "config_lumi_leveling" in config_collider and not config_collider["skip_leveling"]:
        xc.level_ip1_5_by_bunch_intensity(collider, n_collisions_ip1_and_5)
        xc.level_ip2_8_by_separation(n_collisions_ip2, n_collisions_ip8, collider)
    else:
        logging.warning(
            "No leveling is done as no configuration has been provided, or skip_leveling"
            " is set to True."
        )

    # Add linear coupling
    xc.add_linear_coupling(collider)

    # Rematch tune and chromaticity
    xc.match_tune_and_chroma(collider, match_linear_coupling_to_zero=False)

    # Assert that tune, chromaticity and linear coupling are correct one last time
    xc.assert_tune_chroma_coupling(collider)

    # Configure beam-beam if needed
    if not xc.config_beambeam["skip_beambeam"]:
        xc.configure_beam_beam(collider)

    # Update configuration with luminosity now that bb is known
    l_n_collisions = [
        n_collisions_ip1_and_5,
        n_collisions_ip2,
        n_collisions_ip1_and_5,
        n_collisions_ip8,
    ]
    xc.record_final_luminosity(collider, l_n_collisions)

    # Save collider to json (flag to save or not is inside function)
    xc.write_collider_to_disk(collider, full_configuration)

    # Get fingerprint
    fingerprint = xc.return_fingerprint(collider)

    return collider, fingerprint


def clean():
    # Remote the correction folder, and potential C files remaining
    with contextlib.suppress(Exception):
        os.system("rm -rf correction")
        os.system("rm -f *.cc")


# ==================================================================================================
# --- Parameters definition
# ==================================================================================================
dict_mutated_parameters = {} ###---parameters---###
path_configuration = "{} ###---main_configuration---###"

# ==================================================================================================
# --- Script for execution
# ==================================================================================================

if __name__ == "__main__":
    logging.info("Starting script to configure collider")

    # Load full configuration
    full_configuration, ryaml = load_dic_from_path(path_configuration)

    # Mutate parameters in configuration
    for key, value in dict_mutated_parameters.items():
        set_item_in_dic(full_configuration, key, value)

    # Configure collider
    collider, fingerprint = configure_collider(full_configuration)

    # Drop updated configuration
    name_configuration = os.path.basename(path_configuration)
    write_dic_to_path(full_configuration, name_configuration, ryaml)

    # Clean temporary files
    clean()

    logging.info("Script finished")
```

As you can see, not much changed compared to the initial generation_2 script: we basically removed everything that relates to the tracking.

The third generation template script is as follows:

```python title="generation_3_track.py"
"""This is a template script for generation 1 of simulation study, in which ones generates a
particle distribution and a collider from a MAD-X model."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import contextlib
import logging
import os
import time

# Import third-party modules
import numpy as np
import pandas as pd
import xtrack as xt

# Import user-defined modules
from study_da.generate import XsuiteCollider, XsuiteTracking
from study_da.utils import (
    load_dic_from_path,
    set_item_in_dic,
    write_dic_to_path,
)

# Set up the logger here if needed


# ==================================================================================================
# --- Script functions
# ==================================================================================================


def load_collider(full_configuration):
    collider = XsuiteCollider._load_collider(
        full_configuration["config_simulation"]["path_collider_file_for_tracking_as_input"]
    )
    collider.build_trackers()
    return collider


def track_particles(full_configuration, collider):
    # Get emittances
    n_emitt_x = full_configuration["config_collider"]["config_beambeam"]["nemitt_x"]
    n_emitt_y = full_configuration["config_collider"]["config_beambeam"]["nemitt_y"]
    xst = XsuiteTracking(full_configuration["config_simulation"], n_emitt_x, n_emitt_y)

    # Prepare particle distribution
    particles, particle_id, l_amplitude, l_angle = xst.prepare_particle_distribution_for_tracking(
        collider
    )

    # Track
    particles_dict = xst.track(collider, particles)

    # Convert particles to dataframe
    particles_df = pd.DataFrame(particles_dict)

    # ! Very important, otherwise the particles will be mixed in each subset
    # Sort by parent_particle_id
    particles_df = particles_df.sort_values("parent_particle_id")

    # Assign the old id to the sorted dataframe
    particles_df["particle_id"] = particle_id

    # Register the amplitude and angle in the dataframe
    particles_df["normalized amplitude in xy-plane"] = l_amplitude
    particles_df["angle in xy-plane [deg]"] = l_angle * 180 / np.pi

    # Add some metadata to the output for better interpretability
    particles_df.attrs["configuration"] = full_configuration
    particles_df.attrs["date"] = time.strftime("%Y-%m-%d %H:%M:%S")

    # Save output
    particles_df.to_parquet(
        full_configuration["config_simulation"]["path_distribution_file_output"]
    )


# ==================================================================================================
# --- Parameters definition
# ==================================================================================================
dict_mutated_parameters = {} ###---parameters---###
path_configuration = "{} ###---main_configuration---###"

# ==================================================================================================
# --- Script for execution
# ==================================================================================================

if __name__ == "__main__":
    logging.info("Starting script to configure collider and track")

    # Load full configuration
    full_configuration, ryaml = load_dic_from_path(path_configuration)

    # Mutate parameters in configuration
    for key, value in dict_mutated_parameters.items():
        set_item_in_dic(full_configuration, key, value)

    # Configure collider
    collider = load_collider(full_configuration)

    # Drop updated configuration
    name_configuration = os.path.basename(path_configuration)
    write_dic_to_path(full_configuration, name_configuration, ryaml)

    # Track particles and save to disk
    track_particles(full_configuration, collider)

    logging.info("Script finished")
```

We had to do a tiny bit more of adaptation here compared to the usual generation 2: rewrite a function to load the collider, and remove the collider configuration configuration part.

## Template configuration

Finally, we have to ensure the template configuration is adapted to the new structure:

```yaml title="config_hllhc16_3_gen.yaml"
config_particles:
  r_min: 4.0
  r_max: 8.0
  n_r: 256
  n_angles: 5
  n_split: 5
  path_distribution_folder_output: particles

config_mad:
  # Links to be made for tools and scripts
  links:
    acc-models-lhc: ../../../../../external_dependencies/acc-models-lhc

  # Optics file
  optics_file: acc-models-lhc/strengths/round/opt_round_150_1500_optphases_thin.madx

  # Beam parameters
  beam_config:
    lhcb1:
      beam_energy_tot: 7000 # [GeV]
    lhcb2:
      beam_energy_tot: 7000 # [GeV]

  # Ions being simulated
  ions: false

  # Enable machine imperfections
  enable_imperfections: false

  # Enable knob synthesis (for coupling correction, if no imperfections)
  enable_knob_synthesis: true

  # Rename the coupling knobs to avoid conflict between b1 and b2
  # (for hllhc using old fortran code to generate the knobs)
  rename_coupling_knobs: true

  # Optics version, for choice of correction algorithms
  # (ver_lhc_run or ver_hllhc_optics)
  ver_hllhc_optics: 1.6
  ver_lhc_run: null

  # Parameters for machine imperfections
  pars_for_imperfections:
    par_myseed: 1
    par_correct_for_D2: 0
    par_correct_for_MCBX: 0
    par_on_errors_LHC: 1
    par_off_errors_Q4_inIP15: 0
    par_off_errors_Q5_inIP15: 0
    par_on_errors_MBH: 1
    par_on_errors_Q4: 1
    par_on_errors_D2: 1
    par_on_errors_D1: 1
    par_on_errors_IT: 1
    par_on_errors_MCBRD: 0
    par_on_errors_MCBXF: 0
    par_on_errors_NLC: 0
    par_write_errortable: 1

  phasing:
    # RF voltage and phases
    vrf400: 16.0 # [MV]
    lagrf400.b1: 0.5 # [rad]
    lagrf400.b2: 0.5 # [rad]

  # To make some specifics checks
  sanity_checks: true

  # Path of the collider file to be saved (usually at the end of the first generation)
  path_collider_file_for_configuration_as_output: collider_file_for_configuration.json
  compress: true # will compress the collider file, filename will end with .zip

# Configuration for tuning of the collider
config_collider:
  # Even though the file doesn't end with .zip, scrip will first try to load it as a zip file
  path_collider_file_for_configuration_as_input: ../collider_file_for_configuration.json
  config_knobs_and_tuning:
    knob_settings:
      # Orbit knobs
      on_x1: 250 # [urad]
      on_sep1: 0 # [mm]
      on_x2: -170 # [urad]
      on_sep2: 0.138 # 0.1443593672910653 # 0.138 # [mm]
      on_x5: 250 # [urad]
      on_sep5: 0 # [mm]
      on_x8h: 0.0
      on_x8v: 170
      on_sep8h: -0.01 # different from 0 so that the levelling algorithm is not stuck
      on_sep8v: 0.01 # idem
      on_a1: 0 # [urad]
      on_o1: 0 # [mm]
      on_a2: 0 # [urad]
      on_o2: 0 # [mm]
      on_a5: 0 # [urad]
      on_o5: 0 # [mm]
      on_a8: 0 # [urad]
      on_o8: 0 # [mm]
      on_disp: 1 # Value to choose could be optics-dependent

      # Crab cavities
      on_crab1: 0 # [urad]
      on_crab5: 0 # [urad]

      # Magnets of the experiments
      on_alice_normalized: 1
      on_lhcb_normalized: 1
      on_sol_atlas: 0
      on_sol_cms: 0
      on_sol_alice: 0

      # Octupoles
      i_oct_b1: -60. # [A]
      i_oct_b2: -60. # [A]

    # Tunes and chromaticities
    qx:
      lhcb1: 62.31
      lhcb2: 62.31
    qy:
      lhcb1: 60.32
      lhcb2: 60.32
    dqx:
      lhcb1: 15
      lhcb2: 15
    dqy:
      lhcb1: 15
      lhcb2: 15

    # Linear coupling
    delta_cmr: 0.001
    delta_cmi: 0.0

    knob_names:
      lhcb1:
        q_knob_1: kqtf.b1
        q_knob_2: kqtd.b1
        dq_knob_1: ksf.b1
        dq_knob_2: ksd.b1
        c_minus_knob_1: c_minus_re_b1
        c_minus_knob_2: c_minus_im_b1
      lhcb2:
        q_knob_1: kqtf.b2
        q_knob_2: kqtd.b2
        dq_knob_1: ksf.b2
        dq_knob_2: ksd.b2
        c_minus_knob_1: c_minus_re_b2
        c_minus_knob_2: c_minus_im_b2

  config_beambeam:
    skip_beambeam: false
    bunch_spacing_buckets: 10
    num_slices_head_on: 11
    num_long_range_encounters_per_side:
      ip1: 25
      ip2: 20
      ip5: 25
      ip8: 20
    sigma_z: 0.0761
    num_particles_per_bunch: 140000000000.0
    nemitt_x: 2.5e-6
    nemitt_y: 2.5e-6
    mask_with_filling_pattern:
      # If not already existing in the study-da package, pattern must have an absolute path or be
      # added as a dependency for the run file
      pattern_fname: 8b4e_1972b_1960_1178_1886_224bpi_12inj_800ns_bs200ns.json
      i_bunch_b1: null # If not specified, the bunch with the worst schedule is chosen
      i_bunch_b2: null # Same. A value for i_bunch_b1 and i_bunch_b2 must be specified if pattern_fname is specified
    cross_section: 81e-27

  config_lumi_leveling_ip1_5:
    skip_leveling: false
    luminosity: 5.0e+34
    num_colliding_bunches: null # This will be set automatically according to the filling scheme
    vary:
      - num_particles_per_bunch
    constraints:
      max_intensity: 2.3e11
      max_PU: 160

  skip_leveling: false
  config_lumi_leveling:
    ip2:
      separation_in_sigmas: 5
      plane: x
      impose_separation_orthogonal_to_crossing: false
      knobs:
        - on_sep2
      bump_range:
        lhcb1:
          - e.ds.l2.b1
          - s.ds.r2.b1
        lhcb2:
          - s.ds.r2.b2
          - e.ds.l2.b2
      preserve_angles_at_ip: true
      preserve_bump_closure: true
      corrector_knob_names:
        # to preserve angles at ip
        - corr_co_acbyvs4.l2b1
        - corr_co_acbyhs4.l2b1
        - corr_co_acbyvs4.r2b2
        - corr_co_acbyhs4.r2b2
          # to close the bumps
        - corr_co_acbyvs4.l2b2
        - corr_co_acbyhs4.l2b2
        - corr_co_acbyvs4.r2b1
        - corr_co_acbyhs4.r2b1
        - corr_co_acbyhs5.l2b2
        - corr_co_acbyvs5.l2b2
        - corr_co_acbchs5.r2b1
        - corr_co_acbcvs5.r2b1
    ip8:
      luminosity: 2.0e+33
      num_colliding_bunches: null # This will be set automatically according to the filling scheme
      impose_separation_orthogonal_to_crossing: true
      knobs:
        - on_sep8h
        - on_sep8v
      bump_range:
        lhcb1:
          - e.ds.l8.b1
          - s.ds.r8.b1
        lhcb2:
          - s.ds.r8.b2
          - e.ds.l8.b2
      preserve_angles_at_ip: true
      preserve_bump_closure: true
      corrector_knob_names:
        # to preserve angles at ip
        - corr_co_acbyvs4.l8b1
        - corr_co_acbyhs4.l8b1
        - corr_co_acbyvs4.r8b2
        - corr_co_acbyhs4.r8b2
          # to close the bumps
        - corr_co_acbyvs4.l8b2
        - corr_co_acbyhs4.l8b2
        - corr_co_acbyvs4.r8b1
        - corr_co_acbyhs4.r8b1
        - corr_co_acbcvs5.l8b2
        - corr_co_acbchs5.l8b2
        - corr_co_acbyvs5.r8b1
        - corr_co_acbyhs5.r8b1

  # Save collider or not (usually at the end of the collider tuning)
  save_output_collider: true
  path_collider_file_for_tracking_as_output: collider_file_for_tracking.json
  compress: true # will compress the collider file, filename will end with .zip

config_simulation:
  # Collider file to load for the tracking
  path_collider_file_for_tracking_as_input: ../collider_file_for_tracking.json

  # Distribution in the normalized xy space
  path_distribution_folder_input: ../../particles
  distribution_file: 00.parquet

  # Output particle file
  path_distribution_file_output: output_particles.parquet

  # Initial off-momentum
  delta_max: 27.e-5

  # Tracking
  n_turns: 100 # number of turns to track

  # Beam to track
  beam: lhcb1 #lhcb1 or lhcb2

  # Context for the simulation
  context: "cpu" # 'cupy' # opencl

  # Device number for GPU simulation
  device_number: # 0
```

We did a couple changes here:

- save the output collider at the end of the configuration
- Adapt the folder for the particles

Also note that we only use a 100 turns for the tracking as this is just a dummy simulation. And that's it! That's how easy it is.

## Study generation and submission

The script to generate and submit the study is also not so different from the usual. We're going to assume that we submit everything to HTCondor this time, without using Docker.

```python title="generate_and_submit.py"
# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging

# Import third-party modules
# Import user-defined modules
from study_da import create, submit

# Set up the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================

# Generate the study in the local directory
path_tree, name_main_config = create(path_config_scan="config_scan.yaml", force_overwrite=False)

# Define the variables of interest for the submission
path_python_environment = "/afs/cern.ch/work/c/cdroin/private/study-DA/.venv"
force_configure = False

# Dependencies for the executable of each generation. Only needed if one uses HTC.
dic_dependencies_per_gen = {
    1: ["acc-models-lhc"],
    2: ["path_collider_file_for_configuration_as_input"],
    3: [
        "path_collider_file_for_tracking_as_input",
        "path_distribution_folder_input",
    ],
}

# Dic copy_back_per_gen (only for HTC)
dic_copy_back_per_gen = {
    1: {"parquet": True, "yaml": True, "txt": True, "json": True, "zip": True},
    2: {"parquet": True, "yaml": True, "txt": True, "json": True, "zip": True},
    3: {"parquet": True, "yaml": True, "txt": True, "json": False, "zip": False},
}

# To bring back the "particles" folder from gen 1
dic_additional_commands_per_gen = {
    1: "cp -r particles $path_job/particles \n",
    2: "",
}


# Preconfigure submission to HTC
dic_config_jobs = {
    "generation_1" + ".py": {
        "context": "cpu",
        "submission_type": "htc",
        "htc_flavor": "microcentury",
    },
    "generation_2" + ".py": {
        "context": "cpu",
        "submission_type": "htc",
        "htc_flavor": "microcentury",
    },
    "generation_3" + ".py": {
        "context": "cpu",
        "submission_type": "htc",
        "htc_flavor": "espresso",
    },
}


# Submit the study
submit(
    path_tree=path_tree,
    path_python_environment=path_python_environment,
    force_configure=force_configure,
    dic_dependencies_per_gen=dic_dependencies_per_gen,
    name_config=name_main_config,
    dic_config_jobs=dic_config_jobs,
    dic_copy_back_per_gen=dic_copy_back_per_gen,
    dic_additional_commands_per_gen=dic_additional_commands_per_gen,
    keep_submit_until_done=True,
    wait_time=15,
)
```

The first thing you can notice is that we use a logger here as it's easier to debug. Then you can see that we add to adapt the `dic_dependencies_per_gen` to ensure all the intermediary files are copied back to the next generation, even though we run everything on HTCondor. We also added a `dic_copy_back_per_gen` to ensure the (large) files (such as the collider) are copied back to the next generation. We also added a `dic_additional_commands_per_gen` to ensure to copy back the particles folder from the first generation to the second generation.

Finally, you can notice that we preconfigured the submission to HTC with the `dic_config_jobs` dictionary, to ease our life and not get prompted for each generation.

Because we do three generations in a row, we set `keep_submit_until_done=True` to ensure we don't have to submit each generation manually. We also set `wait_time=15` to ensure we don't overload the system.

And that's it! You can now run this script and let it run. It will take a bit of time, but it should run smoothly. Some jobs will fail because the matching of the tune and chroma could not be done, but that's expected, and other jobs will get to the end of generation three.

You can now adapt this script to your needs and run your own 3-generational scan.
