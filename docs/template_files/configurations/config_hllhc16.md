# HL-LHC v1.6 configuration

```yaml title="config_hllhc16.yaml"
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
    acc-models-lhc: ../../../../external_dependencies/acc-models-lhc

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
  ver_lhc_run:

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
      i_bunch_b1:      # If not specified, the bunch with the worst schedule is chosen
      i_bunch_b2:      # Same. A value for i_bunch_b1 and i_bunch_b2 must be specified if pattern_fname is specified
    cross_section: 81e-27

  config_lumi_leveling_ip1_5:
    skip_leveling: false
    luminosity: 5.0e+34
    num_colliding_bunches:      # This will be set automatically according to the filling scheme
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
      num_colliding_bunches:      # This will be set automatically according to the filling scheme
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
  save_output_collider: false
  path_collider_file_for_tracking_as_output: collider_file_for_tracking.json
  compress: true # will compress the collider file, filename will end with .zip

config_simulation:
  # Collider file to load for the tracking
  path_collider_file_for_tracking_as_input: ../collider_file_for_tracking.json

  # Distribution in the normalized xy space
  path_distribution_folder_input: ../particles
  distribution_file: 00.parquet

  # Output particle file
  path_distribution_file_output: output_particles.parquet

  # Initial off-momentum
  delta_max: 27.e-5

  # Tracking
  n_turns: 1000000 # number of turns to track

  # Beam to track
  beam: lhcb1 #lhcb1 or lhcb2

  # Context for the simulation
  context: cpu   # 'cupy' # opencl

  # Device number for GPU simulation
  device_number: # 0
```