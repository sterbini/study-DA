# Dynamics aperture study package

This package is a collection of tools to study the dynamics aperture of a particle accelerator with [Xsuite](https://github.com/xsuite/xsuite). The package is divided in four main parts:

- **Study generation**: provides some functions to generate the dynamics aperture study (as a parametric scan) from template scripts
- **Study submission**: allows to seamlessly submit the generated study to computing clusters (mainly HTCondor) and get back the results
- **Study postprocessing**: provides some functions to postprocess the raw tracking results
- **Study analysis**: provides some functions to analyze and visualize the postprocessed results

This package is still experimental and under development. Consequently, this README is bound to evolve a lot in the near future.
