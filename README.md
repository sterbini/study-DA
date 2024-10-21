# Dynamics Aperture Study Package

This package consists of a collection of tools to study the dynamics aperture of a particle accelerator with [Xsuite](https://github.com/xsuite/xsuite). The package is divided into four main parts:

- **Study Generation**: Provides functions to generate the dynamics aperture study (as a parametric scan) from template scripts and a configuration file.
- **Study Submission**: Allows seamless submission of the generated study to computing clusters (mainly HTCondor) and retrieval of results.
- **Study Postprocessing**: Provides functions to postprocess the raw tracking results.
- **Study Plotting**: Provides functions to visualize the postprocessed results.

A full documentation is available [here](colasdroin.github.io/study-DA).

This package is still experimental and under development. Consequently, this README is bound to evolve a lot in the near future.

## Table of Contents

- [Dynamics Aperture Study Package](#dynamics-aperture-study-package)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Study Generation](#study-generation)
    - [Study Submission](#study-submission)
    - [Study Postprocessing](#study-postprocessing)
    - [Study Analysis](#study-analysis)
  - [Contributing](#contributing)
  - [License](#license)

## Installation

To get started with the Dynamics Aperture Study Package, you need to clone the repository and install the required dependencies.

```bash
git clone https://github.com/yourusername/dynamics-aperture-study.git
cd dynamics-aperture-study
pip install -r requirements.txt
```

## Usage

### Study Generation

To generate a dynamics aperture study, use the provided functions to create a parametric scan from template scripts.

```python
from dynamics_aperture.study_generation import generate_study

generate_study(
    template_script="path/to/template_script.py",
    parameters={"param1": [value1, value2], "param2": [value3, value4]},
    output_folder="path/to/output_folder"
)
```

### Study Submission

You can submit the generated study to a computing cluster using the ```SubmitScan``` class. This class helps you set up and manage job configurations.

```python
from dynamics_aperture.study_submission import SubmitScan

submit_scan = SubmitScan(
    path_tree="path/to/tree",
    path_python_environment="path/to/python/environment",
    path_python_environment_container="path/to/container/environment",
    path_container_image="path/to/container/image"
)

submit_scan.configure_jobs()
submit_scan.submit()
```

### Study Postprocessing

After retrieving the raw tracking results, you can postprocess them using the provided functions.

```python
from dynamics_aperture.study_postprocessing import postprocess_results

postprocess_results(
    raw_results_folder="path/to/raw_results",
    processed_results_folder="path/to/processed_results"
)
```

### Study Analysis

To analyze and visualize the postprocessed results, use the provided functions for generating plots and other visualizations.

```python
from dynamics_aperture.study_analysis import plot_heatmap
import pandas as pd

# Load your data into a DataFrame
data = pd.read_csv("path/to/data.csv")

# Generate a heatmap
fig, ax = plot_heatmap(
    dataframe_data=data,
    horizontal_variable="x_variable",
    vertical_variable="y_variable",
    color_variable="color_variable"
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
