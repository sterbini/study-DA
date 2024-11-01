# Templates

This directory contains the template files for the HL-LHC and run III configurations, as well as the template scripts to build a Xsuite collider from a MAD-X sequence (generation 1), and the scripts to configure the Xsuite collider and do the tracking (generation 2).

Overall, going from one (HL-)LHC version to another should be very transparent. The only difference worth mentionning are the following:

- The run III optics (ions or not) are usually taken directly from CERN AFS, as you can see in the ```acc-models-lhc``` field in the configurations. This means that they're only accessible if you're at CERN, or if you have a VPN connection to CERN (note that you can probably pull them from the CERN gitlab if really needed). Conversely, it is assumed that the HL-LHC optics are available locally (they should get cloned along with the repo if you install the package in editable mode from GitHub). However, if you install the package from PyPI, you will need to download the optics from the CERN GitHub (or elsewhere) and put the appropriate paths in the configuration file.
- The ions runs levelling are usually done by varying the separation (see [generation_2_level_by_sep](scripts/generation_2_level_by_sep.md)), while the protons runs levelling are done by varying the beta functions. However, in the latter case, since the beta functions can't be changed with a single knob, you will have to update the optics file for each levelling step and optimize the bunch intensity for each optics (see [generation_2_level_nb](scripts/generation_2_level_nb.md)).

Please do not hesitate to add any template you deem interesting for the project, through a pull request.
