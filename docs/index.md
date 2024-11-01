# Introduction

The study-DA package consists of a collection of tools to study the dynamics aperture of a particle accelerator with [Xsuite](https://github.com/xsuite/xsuite). In a sense, it is a replacement of the [DA study template](https://github.com/xsuite/DA_study_template), but much more advanced. It also allows to configure colliders and do tracking without necessarily running parametric scans.

 The package is divided into four main parts:

- **Study Generation**: Provides functions to generate, from template scripts and a configuration file, the dynamics aperture study as a multi-generational tree representing the various layers of the corresponding parametric scan. Alternatively, one can generate a single job from configuring a collider and running some tracking (or any other type of job), without doing a scan.
- **Study Submission**: Allows seamless submission of the generated study locally and/or to computing clusters (mainly HTCondor), and the automatic retrieval of the results.
- **Study Postprocessing**: Provides functions to postprocess the raw results (usually `.parquet` files from tracking) and aggregate them into a Pandas `DataFrame`.
- **Study Plotting**: Provides functions to visualize the postprocessed results as 2D and 3D heatmaps.

## Why this package?

Doing a parametric scan for a dynamics aperture study can be a tedious task, especially when the number of parameters is large. In the past, we developped the [DA study template](https://github.com/xsuite/DA_study_template), which is still an excellent starting point. However, this template has a
lof of drawbacks, such as:

- being hard to maintain, since several versions of the template would be needed to cover all the possible LHC versions. However, most of the code was the same, and an extensive use of `git rebase` and/or `git cherry-pick` was needed to keep the different versions up-to-date, bringing with them frequent merge issues and problems of synchronization across versions.
- not being user friendly, since the user had to extensively modify the template scripts directly when doing a new study, which could be a source of errors.
- being redundant, since most parameters were declared both in the configuration file and in the generating script, leading to potential inconsistencies.
- not being easy to adapt for studies having more than 2 generations. Especially when using HTCondor.
- being tedious to work with, since the user had to manually create the jobs, submit the jobs, retrieve the results, postprocess them, and plot them, each time running a different script.
- not explicitely allowing the user to do configure and track a single collider, without doing a scan.
- being not standardized regarding the way the postprocessing was done, leading to potential inconsistencies in the results to plot.
- not having a plotting and/or analysis module, letting each user doing the analysis by themselves.
- having frequent compatibility issues with Xsuite, since it was not trivial to setup a Continuous Integration (CI) pipeline for such open scripts, while Xsuite is being updated frequently.
- being harder to set up, since the template was not available on PyPI.

This package aims at solving all these issues, and more. It is more user-friendly and easily flexible  while being more standardized. It is also more robust, since it is tested with a CI pipeline, and more easily maintainable, since all the common code is now centralized in a given set of classes and functions.

!!! info "Standardizing has a cost"

    The user has to follow the package's conventions, which might be a bit more restrictive than the DA study template. In addition, since all the functions to configure/track/submit/postprocess/plot are now centralized as part of the package, they are not openly exposed as they used to, and are therefore not as easy to modify.

This being said, the user should still be able (and is encouraged) to implement his own functions and/or template scripts in the context of his own work, and the package is always open to contributions if a given workflow might be useful to others.

## Getting started

You can simply `pip install` the package:

```bash
pip install study-da
```

And then move to the [tutorials](tutorials/index.md) to get started with the package, or directly to the [case studies](case_studies/index.md) to see some actual useful examples of what can be done with the package. Note that you will need the repositories for the optics (e.g. run III or HL-LHC) to be available somewhere on your machine, or on AFS if you're at CERN, if you want to run the tracking examples.

In case you need more guidance for the installation, or if you want to contribute to the package, please refer to the [installation](installation.md) section.

!!! warning "HTCondor must be installed and properly configured"

    To submit large scans to HTCondor, the corresponding batch service must be installed and properly configured. If you don't have access, you can still run the script locally, but you won't be able to submit the jobs to the clusters. You can read more [here](https://abpcomputing.web.cern.ch/computing_resources/cernbatch/).
