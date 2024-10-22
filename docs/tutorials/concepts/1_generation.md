# Generation

## Introduction

Generating studies is one of the main functionalities of the study-da package. To understand how this is done, we will play with some dummy example configuration. In this case, we choose to use only two generations as it's enough to illustrate the main concepts, but you can have as many generations as you want.

## Template scripts

### Generation 1

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
# --- Parameters definition
# ==================================================================================================
dict_mutated_parameters = {{parameters}}
path_configuration = "{{main_configuration}}"

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

#### Jinja2 placeholders

If you work with a linter, it will probably protest at this point. Indeed, the following part of the script is not valid Python code:

```python
dict_mutated_parameters = {{parameters}}
path_configuration = "{{main_configuration}}"
```

This is not a mistake. The `{{`and `}}` are used to indicate placeholders for the actual values that will be filled in by the study-da package, using [jinja2](https://jinja.palletsprojects.com/en/3.1.x/) under the hood. In practice, as it will be shown later in this tutorial, the `{{parameters}}` will be replaced by a dictionary of parameters (the ones being scanned), and `{{main_configuration}}` will be replaced by the path to the main configuration file. This allows to mutate selectively some of the parameters in the configuration file, and to write the modified configuration back to the disk. The parameter values are specific to each generated job.

If you don't understand, no worries, it will get clearer as we go along and actually generate some jobs.

#### Understanding the script

The script is quite simple. It loads the main configuration file from a path that is not explicitely given yet, mutates the parameters in the configuration, adds two of them, and writes the modified configuration back to the disk.

It is assumed that the main configuration is always loaded from the above generation, and written back in the current generation. Therefore, each generation relies on the previous one. This is a simple way to chain the generations, and update the configuration with the mutated parameters every time.

???+ warning "Be careful with parameter names"

    As you can see in the script, parameter are accessed only with their names. No key is provided, while the corresponding yaml file might have a nested structure. This is because the `set_item_in_dic` function is used to set the value of the parameter. This function will look for the parameter in the configuration file (everywhere) and set its value. Now, if two parameters have the same name, but are in different parts of the configuration file, the script will not work as expected. This is the price of making the package as simple as possible. If you happen to have two parameters with the same name, you will have to modify one of them in the configuration file.

### Generation 2

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
# --- Parameters definition
# ==================================================================================================
dict_mutated_parameters = {{parameters}}
path_configuration = "{{main_configuration}}"

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

As you can see, this script multiplies the result of the previous script (stored in the configuration, in the above generation) by a new parameter `y`, and writes the result to a file.

## Template configuration

The base configuration is always the same for all generations, although it does get modified (mutated) by the scripts. There's nothing special about it, it's just a simple yaml file:

```yaml title="config_dummy.yaml"
a_random_nest:
  x: -1
y: -2
another_random_nest:
  and_another:
    z: -3
```

## Scan configuration

The scan configuration is an essential part of the study generation. It defines what are the parameters that will be scanned, and the values they will take. Here is a possible scan configuration for our dummy example:

```yaml title="config_scan.yaml"
name: example_with_custom_template_and_configuration

# List all useful files that will be used by executable in generations below
# These files are placed at the root of the study
dependencies:
  main_configuration: custom_files/config_dummy.yaml

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
# TODO: explain all the possible types of parameters, and the corresponding keywords. Also explain that the template scripts and/or generation can be taken directly from the package

By default (if no specific keyword is provided), the cartesian product of all the parameter values will be considered to generate the jobs. This means that the number of jobs will be the product of the number of values for each parameter. In the example above, the number of jobs will be 6 (2 values for `x` and 3 values for `y`).
