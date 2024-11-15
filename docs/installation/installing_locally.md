# Installing study-DA locally

## Cloning the repository

If you encounter trouble with the pip installation, or if you want to modify and/or contribute to the package, you can install it locally by cloning the repository and installing the dependencies with Poetry. Note, that, if you plan to submit jobs to CERN HTCondor from a local Python installation, you should move to your AFS space first (e.g. ```cd /afs/cern.ch/work/u/username/private```).:

```bash
git clone --recurse-submodules https://github.com/ColasDroin/study-DA.git
```

If you missed this step and clone the repository without the submodules, you can do *a posteriori*:

```bash
git submodule update --init --recursive
```

Cloning the submodules is important as this allows to download the optics for HL-LHC, which are necessary to run the tracking examples. Therefore, you should be able to skip the [Installing the optics](installing_the_optics.md) section.

## Installing with Poetry

### Standard installation with Poetry

If not already done, install Poetry following the tutorial [here](https://python-poetry.org/docs/).

For easier submission later, impose the virtual environment to be created in the repository folder by running the following command:

```bash
poetry config virtualenvs.in-project true
```

!!! warning "Still be careful where Python is installed"

    If you're from CERN and intend to submit jobs to HTCondor from your local Python environment, ensure that the executable that Poetry will use to spawn a virtual environment is available on AFS.

You can check the base executable of Python that Poetry is using by running the following command:

```bash
poetry env info
```

If needed (for instance, if your Python base executable is not on AFS), you can change the exectutable with e.g:

```bash
poetry env use /full/path/to/python
```

If you're not interested in using GPUs, you can jump directly to the [Installing dependencies](#installing-dependencies) section. Otherwise, follow the next section.

### Installing with Poetry for GPUs

Using Poetry along with GPUs is a bit more complicated, as conda is not natively supported by Poetry. However, not all is lost as a simple trick allows to bypass this issue. First, from a conda-compatible Python environment (not the one you used to install Poetry), create a virtual environment with the following command:

```bash
conda create -n gpusim python=3.9
conda activate gpusim
```

⚠️ **Make sure that the Python version is 3.9 as, for now, a bug with Poetry prevents using 3.10 or above.**

Now configure Poetry to use the virtual environment you just created:
  
```bash
poetry config virtualenvs.in-project false
poetry config virtualenvs.path $CONDA_ENV_PATH
poetry config virtualenvs.create false
```

Where ```$CONDA_ENV_PATH``` is the path to the base envs folder (e.g. ```/home/user/miniforge3/envs```).  

You can then install the CUDA toolkit and the necessary packages (e.g. ```cupy```) in the virtual environment (from [Xsuite documentation](https://xsuite.readthedocs.io/en/latest/installation.html#gpu-multithreading-support) ):

```bash
conda install mamba -n base -c conda-forge
mamba install cudatoolkit=11.8.0
```

Don't forget to select the path to your virtual environment for submission with the `submit()`method will be the conda one (e.g. ```home/user/miniforge3/bin/activate```, and add right after ```conda activate gpusim```), i.e.:

```py
submit(
    ...
    path_python_environment="/home/user/miniforge3/bin/activate; conda activate gpusim",
    ...
)
```

You're now good to go with the next section, as Poetry will automatically detect that the conda virtual environment is activated and use it to install the dependencies.

### Installing dependencies

Finally, install the dependencies by running the following command:

```bash
poetry install
```

!!! info "Developer installation"

    If you plan to contribute to the package, you can install the dependencies needed for development (tests, documentation) with:

    ```bash
    poetry install --with test,docs,dev
    ```

At this point, ensure that a `.venv` folder has been created in the repository folder (except if you modified the procedure to use GPUs, as explained above). If not, follow the fix described in the next section.

⚠️ **If you have a bug with nafflib installation, do the following:**
  
  ```bash
  poetry run pip install nafflib
  poetry install
  ```

  ⚠️ **If you have a bug with conda compilers, do the following:**

  ```bash
  poetry shell
  conda install compilers cmake
  ```

Finally, you can make xsuite faster by precompiling the kernel, with:

```bash
poetry run xsuite-prebuild regenerate
```

To run any subsequent Python command, either activate the virtual environment (activate a shell within Poetry) with:

```bash
poetry shell
# you then run a command as simply as `python my_script.py`
```

or run the command directly with Poetry:

```bash
poetry run python my_script.py
```

At this point, the only step left is to install xmask (which is normally already cloned), which is an external dependency that is not handled by Poetry since it requires cloning submodules. You can do so by running the following commands:

```bash
poetry shell
cd external_dependencies
pip install -e xmask
```

## Installing locally without Poetry

It is strongly recommended to use Poetry as it will handle all the packages dependencies and the virtual environment for you. However, if you prefer to install the dependencies manually, you can do so by running the following commands (granted that you have Python installed along with pip):

```bash
pip install -r requirements.txt

# Now install xmask
cd external_dependencies
pip install -e xmask
```
