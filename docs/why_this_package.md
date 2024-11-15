# Why this package?

Conducting a parametric scan for a dynamic aperture study can be a challenging and time-consuming task, especially when dealing with a large number of parameters. Previously, we developed the [DA study template](https://github.com/xsuite/DA_study_template), which remains a solid starting point. However, it comes with several significant drawbacks:

- **Difficult maintenance**:  
  Managing multiple versions of the template to accommodate different LHC configurations required extensive use of `git rebase` and `git cherry-pick`. This approach often led to frequent merge conflicts, synchronization issues, and duplication of largely similar code.

- **Lack of user-friendliness**:  
  Users needed to directly modify template scripts for new studies, increasing the likelihood of errors.

- **Redundancy**:  
  Parameters were often declared both in the configuration file and the generating script, creating opportunities for inconsistencies.

- **Limited scalability**:  
  The template was not well-suited for studies involving more than two generations, especially when using HTCondor.

- **Cumbersome workflow**:  
  Tasks like creating jobs, submitting them, retrieving results, postprocessing, and plotting had to be performed manually using separate scripts for each step.

- **Restricted functionality**:  
  The template did not explicitly support configuring and tracking a single collider without conducting a full scan.

- **Lack of standardization**:  
  The postprocessing workflow varied among users, leading to inconsistent results and plotting.

- **No integrated analysis or plotting**:  
  Users were responsible for performing their own analysis and visualization.

- **Compatibility issues with Xsuite**:  
  Frequent Xsuite updates made it challenging to maintain compatibility, as setting up a Continuous Integration (CI) pipeline for open scripts was not straightforward.

- **Complex setup**:  
  The template was not available on PyPI, complicating the installation process.

This package addresses all these issues and more, offering a more user-friendly, flexible, and standardized solution. It is also more robust, thanks to (a simple) CI pipeline testing, and easier to maintain due to the centralization of common code into a cohesive set of classes and functions.

!!! info "Standardization comes with trade-offs"
    Adopting this package requires adherence to its conventions, which may feel more restrictive compared to the DA study template. Additionally, because functions for configuring, tracking, submitting, postprocessing, and plotting are centralized within the package, they are no longer as openly modifiable.

That said, users are encouraged to implement their own functions and template scripts for their specific workflows. The package is also open to contributions to integrate workflows that may benefit the broader community.
