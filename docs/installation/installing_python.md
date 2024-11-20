# Installing Python

Python is probably already available on your machine. You can check by running the following commands:

```bash
which python # Tells you the path to the python executable
python --version # Tells you the version of Python
```

If Python (>=3.11) is not available, you can install it with, for instance, miniforge or miniconda.

To install the latest version of Python with miniforge in your home directory, run the following commands:

```bash
cd
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh -b  -p ./miniforge -f
rm -f Miniforge3-Linux-x86_64.sh
source miniforge/bin/activate
```

!!! warning "Be careful where Python is installed"

    If you're from CERN and intend to submit job to HTCondor without using a CVMFS environment or Docker environment, your environment must be available on AFS (i.e. must be installed on AFS).
