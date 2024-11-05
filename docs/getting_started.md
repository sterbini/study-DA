# Getting started

You can simply `pip install` the package:

```bash
pip install study-da
```

And then move to the [tutorials](tutorials/index.md) to get started with the package, or directly to the [case studies](case_studies/index.md) to see some actual useful examples of what can be done with the package. Note that you will need the repositories for the optics (e.g. run III or HL-LHC) to be available somewhere on your machine, or on AFS if you're at CERN, if you want to run the tracking examples.

In case you need more guidance for the installation, or if you want to contribute to the package, please refer to the [installation](installation/installing_python.md) section.

!!! warning "HTCondor must be installed and properly configured"

    To submit large scans to HTCondor, the corresponding batch service must be installed and properly configured. If you don't have access, you can still run the script locally, but you won't be able to submit the jobs to the clusters. You can read more [here](https://abpcomputing.web.cern.ch/computing_resources/cernbatch/).
