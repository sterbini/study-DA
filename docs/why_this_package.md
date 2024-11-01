# Why this package?

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