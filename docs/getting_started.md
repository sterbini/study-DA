# Getting started

You can simply `pip install` the package:

```bash
pip install study-da
```

You will also have to install `xmask` somewhere as an external dependency since it requires pulling submodules:

```bash
# You can install xmask in the directory of your choice (along with the optics, for instance)... 
# Just ensure it doesn't get deleted
git clone --recurse-submodules https://github.com/xsuite/xmask
pip install -e xmask
```

If you have some optics available on your machine or on AFS (e.g. HL-LHC v1.6), you can directly move to the [tutorials](tutorials/index.md) to get started with the package, or to the [case studies](case_studies/index.md) to see some actual useful examples of what can be done with the package.

Otherwise, please refer to the [installing the optics](installation/installing_the_optics.md) section to get the optics you need.

Do not hesitate to refer to the detailed explanations in case you need more guidance to [install Python](installation/installing_python.md), or if you want to [install locally](installing_locally.md) (for instance to contribute to the package).

!!! warning "HTCondor must be installed and properly configured"

    To submit large scans to HTCondor, the corresponding batch service must be installed and properly configured. If you don't have access, you can still run the script locally, but you won't be able to submit the jobs to the clusters. You can read more [here](https://abpcomputing.web.cern.ch/computing_resources/cernbatch/).
