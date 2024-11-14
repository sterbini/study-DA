# Generation

## Introduction

Generating studies is one of the main functionalities of the study-da package. To understand how this is done, we will play with some dummy example configuration. In this case, we choose to use only two generations as it's enough to illustrate the main concepts, but you can have as many generations as you want.

## Creating the study

### Template scripts

#### Generation 1

First, let's define the scripts from which we would like to generate the jobs. We will start with something very simple and simply add two parameters from the configuration file.

```py title="generation_1_dummy.py" linenums="1"
# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging
import os

# Import third-party modules
# Import user-defined modules
from study_da.utils import (
    load_dic_from_path,
    set_item_in_dic,
    write_dic_to_path,
)

# Set up the logger here if needed


# ==================================================================================================
# --- Script functions
# ==================================================================================================
def add(configuration):
    x = float(configuration["a_random_nest"]["x"])
    z = float(configuration["another_random_nest"]["and_another"]["z"])
    configuration["result"] = {"x_plus_z": x + z}
    return configuration


# ==================================================================================================
# --- Parameters placeholders definition
# ==================================================================================================
dict_mutated_parameters = {}  ###---parameters---###
path_configuration = "{}  ###---main_configuration---###"
# In case the placeholders have not been replaced, use default path
if path_configuration.startswith("{}"):
    path_configuration = "config.yaml"

# ==================================================================================================
# --- Script for execution
# ==================================================================================================

if __name__ == "__main__":
    logging.info("Starting custom script")

    # Load full configuration
    full_configuration, ryaml = load_dic_from_path(path_configuration)

    # Mutate parameters in configuration
    for key, value in dict_mutated_parameters.items():
        set_item_in_dic(full_configuration, key, value)

    # Add x and z and write to configuration
    full_configuration = add(full_configuration)

    # Dump configuration
    name_configuration = os.path.basename(path_configuration)
    write_dic_to_path(full_configuration, name_configuration, ryaml)

    logging.info("Script finished")
```

##### Jinja2 placeholders

The following part of the script is not really made to be used as is, but to be filled in by the study-da package:

```python
dict_mutated_parameters = {}  ###---parameters---###
path_configuration = "{}  ###---main_configuration---###""
```

The `{}  ###---`and `---###` are used to indicate placeholders for the actual values that will be filled in by the study-da package, using [jinja2](https://jinja.palletsprojects.com/en/3.1.x/) under the hood. In practice, as it will be shown later in this tutorial, the `{}  ###---parameters---###` will be replaced by a dictionary of parameters (the ones being scanned), and `{}  ###---main_configuration---###` will be replaced by the path to the main configuration file. This allows to mutate selectively some of the parameters in the configuration file, and to write the modified configuration back to the disk. The parameter values are specific to each generated job.

!!! info "Why these placeholders?"

    You may wonder why we use these weird `{}  ###---` and `---###` placeholders, instead of the usual `{{` and `}}` from jinja2. The reason is that we want to keep the template script executable, and this choice of placeholders allows to do so. This is however quite arbitrary.
    

If you don't understand, no worries, it will get clearer as we go along and actually generate some jobs.

##### Understanding the script

The script is quite simple. It loads the main configuration file from a path that is not explicitely given yet, mutates the parameters in the configuration, adds two of them, and writes the modified configuration back to the disk.

It is assumed that the main configuration is always loaded from the above generation, and written back in the current generation. Therefore, each generation relies on the previous one. This is a simple way to chain the generations, and update the configuration with the mutated parameters every time.

???+ warning "Be careful with parameter names"

    As you can see in the script, parameter are accessed only with their names. No key is provided, while the corresponding yaml file might have a nested structure. This is because the `set_item_in_dic` function is used to set the value of the parameter. This function will look for the parameter in the configuration file (everywhere) and set its value. Now, if two parameters have the same name, but are in different parts of the configuration file, the script will not work as expected. This is the price of making the package as simple as possible. If you happen to have two parameters with the same name, you will have to modify one of them in the configuration file.

#### Generation 2

The second generation script is just as simple:

```py title="generation_2_dummy.py" linenums="1"
# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import logging
import os

# Import third-party modules
# Import user-defined modules
from study_da.utils import (
    load_dic_from_path,
    set_item_in_dic,
    write_dic_to_path,
)

# Set up the logger here if needed


# ==================================================================================================
# --- Script functions
# ==================================================================================================
def multiply_and_dump(configuration):
    y = float(configuration["y"])
    x_plus_z = float(configuration["result"]["x_plus_z"])

    # Dump result to txt file
    with open("result.txt", "w") as f:
        f.write(str(x_plus_z * y))


# ==================================================================================================
# --- Parameters placeholders definition
# ==================================================================================================
dict_mutated_parameters = {}  ###---parameters---###
path_configuration = "{}  ###---main_configuration---###"
# In case the placeholders have not been replaced, use default path
if path_configuration.startswith("{}"):
    path_configuration = "config.yaml"

# ==================================================================================================
# --- Script for execution
# ==================================================================================================

if __name__ == "__main__":
    logging.info("Starting custom script")

    # Load full configuration
    full_configuration, ryaml = load_dic_from_path(path_configuration)

    # Mutate parameters in configuration
    for key, value in dict_mutated_parameters.items():
        set_item_in_dic(full_configuration, key, value)

    # Add x and z and write to configuration
    multiply_and_dump(full_configuration)

    # Dump configuration
    name_configuration = os.path.basename(path_configuration)
    write_dic_to_path(full_configuration, name_configuration, ryaml)

    logging.info("Script finished")
```

As you can see, this script multiplies the result of the previous script (stored in the configuration, in the above generation) by a new parameter `y`, and writes the result to a text file.

### Template configuration

The base configuration is always the same for all generations, although it does get modified (mutated) by the scripts. There's nothing special about it, it's just a simple yaml file:

```yaml title="config_dummy.yaml"
a_random_nest:
  x: -1
y: -2
another_random_nest:
  and_another:
    z: -3
```

### Scan configuration

The scan configuration is an essential part of the study generation. It defines what are the parameters that will be scanned, and the values they will take. Here is a possible scan configuration for our dummy example:

```yaml title="config_scan.yaml"
name: example_dummy

# List all useful files that will be used by executable in generations below
# These files are placed at the root of the study
dependencies:
  main_configuration: custom_files/config_dummy.yaml
  # - custom_files/other_file.yaml
  # - custom_files/module.py
structure:
  # First generation is always at the root of the study
  # such that config_dummy.yaml is accessible as ../config_dummy.yaml
  generation_1:
    executable: custom_files/generation_1_dummy.py
    scans:
      x:
        # Values taken by x using a list
        list: [1, 2]

  # Second generation depends on the config from the first generation
  generation_2:
    executable: custom_files/generation_2_dummy.py
    scans:
      y:
        # Values taken by y using a linspace
        linspace: [1, 100, 3]
```

Let's exlain the different fields in the scan configuration:

- name: the name of the study, which will also correspond to the name of the rood folder of the study
- dependencies: a list of files that are needed by the executable scripts. These files will be copied to the root of the study, so that they can be accessed by the scripts. Note that some configuration files are already provided by the package, and can be used directly (see e.g. [1_simple_collider](../../case_studies/1_simple_collider.md) and [2_tune_scan](../../case_studies/2_tune_scan.md) for examples)
- structure: the structure of the study, with the different generations:
  - Each generation has an `executable` field, which is the path to the script that will be executed. These paths can correspond to local files (as in here), or to predefined templates (as, for instance, in the [case studies](../../case_studies/2_tune_scan.md), in which case just the name of the template is enough)
  - The `scans` field is a dictionary of parameters that will be scanned, and the values they will take. The values can be given as a list, a linspace or a logspace. Other possibilities (e.g. scanning generated string names, using nested variables, defining parameter in terms of other through mathematical expression) are all presented in the [Case studies](../../case_studies/index.md).

By default (if no specific keyword is provided), the cartesian product of all the parameter values will be considered to generate the jobs. This means that the number of jobs will be the product of the number of values for each parameter. In the example above, the number of jobs will be 6 (2 values for `x` and 3 values for `y`).

Conversely, one can decide to scan two parameters at the same time (useful, for instance, when scanning the tune diagonal in a collider) using the `concomitant` keyword. This is also used in tune scan [case studie](../../case_studies/2_tune_scan.md).

## Generating the study

Everything is now in place to generate our dummy study. A one line-command is enough to do it for us:

```py title="generate.py" linenums="1"
from study_da import create
create(path_config_scan="config_scan.yaml")
```

You should now see the corresponding study folder appear in the current directory.

### Arguments of the `create` function

We will detail the structure soon, but let's first have a look at the other possible arguments of the `create` function. The full signature of the function is:

```py
def create(
    path_config_scan: str = "config_scan.yaml",
    force_overwrite: bool = False,
    dic_parameter_all_gen: Optional[dict[str, dict[str, Any]]] = None,
    dic_parameter_all_gen_naming: Optional[dict[str, dict[str, Any]]] = None,
) -> tuple[str, str]:
```

Let's detail the arguments:

- `force_overwrite` can be useful if you want to overwrite an existing study. However, in most of the case, we submit the study in the same script, meaning that we might have to run the script several times. In this case, the `force_overwrite` argument must be set to `False`, otherwise the study will be overwritten at each run, and you will lose whatever has already been computed.
- `dic_parameter_all_gen` is a dictionary that allows to specify the parameters that will be scanned for each generation, instead of defining them the scan configuration file. This doesn't free you from defining the structure of the study in the scan configuration file! This can be useful when the way to define your parameters is more complex than a simple list, linspace or logspace, or if your parameters are functions of each other. This is explained in [one of the case studies](../../case_studies/6_3_generational_scan.md).
- `dic_parameter_all_gen_naming` is similar to `dic_parameter_all_gen`, but allows to specify the parameters that will be scanned for each generation, and the way they will be named in the study folder. This is useful when you want to have a specific naming for your parameters, or if parameters are nested. This is also explained in [the same case study](../../case_studies/6_3_generational_scan.md).

### The tree and study structure

The following study structure should have been generated (not all files are shown):

```bash
📁 example_dummy/
├─╴📁 x_1/
│   ├── 📁 y_1.0/
│   ├── 📁 y_50.5/
│   ├── 📁 y_100.0/
│   │   └── 📄 generation_2.py
│   └── 📄 generation_1.py
├─╴📁 x_2/
├─ 📄 tree.yaml
└─ 📄 config_dummy.yaml
```

And similarly, in the `tree.yaml` file:

```yaml
x_1:
  generation_1:
    file: example_dummy/x_1/generation_1.py
  y_1.0:
    generation_2:
      file: example_dummy/x_1/y_1.0/generation_2.py
  ...
```

As you can observe, by default, each folder corresponds to a given generation, and is named after the parameter value it corresponds to. In each folder, an executable script (a `.py` file) has been created, along with potential subgenerations. If you open a given script, you will see that the placeholders have been replaced by the actual values of the parameters. For instance, for the parameter definition in the `generation_1.py` script in the `x_1` folder now looks like:

```py
dict_mutated_parameters = {
    "x": 1,
}
path_configuration = "../config_dummy.yaml"
```

This type of structure is very useful to keep track of the different jobs that have been generated, and to easily access the results of each job. Each job has its own executable, and only depends on the previous generation. Therefore, the jobs can be run independently, or in parallel, and can be individually debugged.

The tree file will be very useful to keep track of the state of each job, as illustrated in the [second part of this tutorial](2_submission.md).
