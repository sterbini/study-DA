# Introduction

The study-DA package consists of a collection of tools to study the dynamics aperture of a particle accelerator built with [Xsuite](https://github.com/xsuite/xsuite). In a sense, it is a replacement of the [DA study template](https://github.com/xsuite/DA_study_template), but much more advanced. It also allows to configure colliders and do tracking without necessarily running parametric scans.

 The package is divided into four main parts:

- **Study Generation**: Provides functions to generate, from template scripts and a configuration file, the dynamics aperture study as a multi-generational tree representing the various layers of the corresponding parametric scan. Alternatively, one can generate a single job from configuring a collider and running some tracking (or any other type of job), without doing a scan.
- **Study Submission**: Allows seamless submission of the generated study locally and/or to computing clusters (mainly HTCondor), and the automatic retrieval of the results.
- **Study Postprocessing**: Provides functions to postprocess the raw results (usually `.parquet` files from tracking) and aggregate them into a Pandas `DataFrame`.
- **Study Plotting**: Provides functions to visualize the postprocessed results as 2D and 3D heatmaps.

Please read the [Getting Started](getting_started.md) section to install the package and get started with the tutorials.
