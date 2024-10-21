# Dynamics Aperture Study Package

This package consists of a collection of tools to study the dynamics aperture of a particle accelerator with [Xsuite](https://github.com/xsuite/xsuite). In a sense, it is a replacement of the [DA study template](https://github.com/xsuite/DA_study_template), but much more advanced. It also allows to configure colliders and do tracking without necessarily running parametric scans.

 The package is divided into four main parts:

- **Study Generation**: Provides functions to generate, from template scripts and a configuration file, the dynamics aperture study as a multi-generational tree representing the various layers of the corresponding parametric scan. Alternatively, one can generate a single job from configuring a collider and running some tracking (or any other type of job), without doing a scan.
- **Study Submission**: Allows seamless submission of the generated study locally and/or to computing clusters (mainly HTCondor), and the automatic retrieval of the results.
- **Study Postprocessing**: Provides functions to postprocess the raw results (usually `.parquet` files from tracking) and aggregate them into a Pandas `DataFrame`.
- **Study Plotting**: Provides functions to visualize the postprocessed results as 2D and 3D heatmaps.

The whole project is described in details in the [full documentation](https://colasdroin.github.io/study-DA/), along with tutorials and description of the implemented functions.

Note that this package is still under development. Consequently, this README might evolve in the near future.

## Installation

### Simple usage

The package is available on PyPI and can be installed using `pip`.

```bash
pip install study-da
```

### Advanced usage (for developers or users needing to modify the package)

For a local installation, you will need first to clone the repository and install the dependencies. We recommend using [Poetry](https://python-poetry.org/) for managing the dependencies, but you can also use `pip` directly in editable mode.

```bash
git clone https://github.com/ColasDroin/study-DA.git
cd study-DA
poetry install # or pip install -r requirements.txt -e .
```

## Usage

A very brief overview of the main functionalities is given below. However, only a few functions are presented here, with only a small portion of their arguments. For more details, please refer to the [full documentation](https://colasdroin.github.io/study-DA/).

### Study Generation

You can generate a study from a configuration file using the `create` function. This function will create a tree of generations, each representing a layer of the scan.

An example of a configuration file, using the template scripts from the package for a tune scan, could be:

```yaml
name: example_tune_scan
dependencies:
  main_configuration: config_hllhc16.yaml
structure:
  generation_1:
    executable: generation_1.py
  generation_2:
    executable: generation_2_level_by_nb.py
    scans:
      qx:
        subvariables: [lhcb1, lhcb2]
        linspace: [62.31, 62.32, 11]
      qy:
        subvariables: [lhcb1, lhcb2]
        linspace: [60.31, 60.32, 11]
```

You can check the template scripts in the `study-da/generate/template_scripts` folder.

After creating the configuration file, you can generate the study using the following code:

```python
from study_da import create

path_tree, name_main_config = create(path_config="config_scan.yaml")
```

The tree will be generated in the specified folder, with the requested structure.

### Study Submission

You can submit the generated study to a computing cluster using the ```submit``` function. 

```python
from dynamics_aperture.study_submission import SubmitScan
submit(
    path_tree=path_tree,
    path_python_environment='.venv/bin/python',
    path_python_environment_container=None # You can specify a Python environment inside of a container instead
    path_container_image=None, # Path to the container image
    name_config=name_main_config,
    keep_submit_until_done=True,
    wait_time=15,
)
```

This code will ask you what type of submission you want to do (local, HTCondor, or Slurm) for each generation and and will submit the study accordingly. It will try resubmitting the jobs whose dependencies are fulfilled until all the jobs are done (or failed).

### Study Postprocessing

When the jobs are finished, one can retrieve the raw tracking results and postprocess them using the provided function.

```python
from study_da import aggregate_output_data

df_final = aggregate_output_data(
    "path_tree",
    l_group_by_parameters=["qx_b1", "qy_b1"],
    generation_of_interest=2 # Generation form which to retrieve the output,
    name_output="output_particles.parquet",    
)
```

### Study Analysis

Finally, one can plot the aggregated results using the provided plotting function.

```python
title = get_title_from_configuration(
    df_final,
    betx_value=0.15,
    bety_value=0.15,
    display_tune=False,
)

fig, ax = plot_heatmap(
    df_final,
    horizontal_variable = "qx_b1",
    vertical_variable="qy_b1",
    color_variable="normalized amplitude in xy-plane",
    link="www.this-link-will-be-added-as-a-qrcode-in-the-plot.com",
    plot_contours=True,
    xlabel=r'Horizontal tune $Q_x$',
    ylabel=r'Vertical tune $Q_y$',
    title=title,
    vmin=4.5,
    vmax=7.5,
    green_contour = 6.0,
    output_path="output.pdf",
)
```

## Contributing

We welcome contributions to the Dynamics Aperture Study Package. If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.

1. Fork the repository
2. Create a new branch (`git checkout -b feature/yourfeature`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add your feature'`)
5. Push to the branch (`git push origin feature/yourfeature`)
6. Create a new Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
