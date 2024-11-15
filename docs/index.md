# Introduction

The **study-DA** package is a comprehensive suite of tools designed to analyze the dynamic aperture of particle accelerators built with [Xsuite](https://github.com/xsuite/xsuite). It serves as an advanced replacement for the [DA study template](https://github.com/xsuite/DA_study_template), offering enhanced capabilities for collider configuration, tracking, and analysis without requiring parametric scans.

The package is organized into four key components:

1. **Study Generation**:  
   Enables the creation of dynamic aperture studies through template scripts and configuration files, structured as a multi-generational tree representing various layers of a parametric scan. Alternatively, single jobs can be created for tasks such as collider configuration and tracking, bypassing the need for a full scan.

2. **Study Submission**:  
   Simplifies the submission of studies to local systems or computing clusters (primarily HTCondor) and automates the retrieval of results.

3. **Study Postprocessing**:  
   Offers tools to transform raw results (typically `.parquet` files from tracking) into a Pandas `DataFrame` for easy analysis and aggregation.

4. **Study Plotting**:  
   Provides functions to generate 2D and 3D heatmaps for visualizing postprocessed results effectively.

For installation instructions and tutorials, please refer to the [Getting Started](getting_started.md) guide.
