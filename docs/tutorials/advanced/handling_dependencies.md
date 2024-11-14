# Handling dependencies

Two types of dependencies might be required by a given study: data or configuration (i.e. files ending `.parquet`, `.txt`, `.yaml`, etc.), and python modules. There are various ways of handling these dependencies, but we're just going to provide the simpler approach here.

## Data dependencies

Data dependencies are files that are required by the study to run. In the approach we suggest, these files should be:

1. Declared as dependencies in the study's scan configuration (optional, but better for portability).
2. Declared as parameters in the study's main configuration, with relative or absolute paths.
3. If running the study on a cluster, declared in the dictionary of dependencies `dic_dependencies_per_gen` which is passed to the `submit()` function.

Indeed, dependencies which are declared in the study scan configuration will be automatically copied and placed at the root of the study. This way, the study can access them using relative paths (which must be adapted for each generation, of course. You can do that either by having several paths in the configuration, or by prefixing appropriately the path using '../' in the template script), or absolute path (simpler, but less portable). In any case, if the study is run on a cluster, the relative paths will be mutated to be absolute paths.

For instance, your scan configuration could look like something like this:

```yaml
# ==================================================================================================
# --- Structure of the study ---
# ==================================================================================================
name: example_tune_scan

# List all useful files that will be used by executable in generations below
# These files are placed at the root of the study
dependencies:
  main_configuration: config_hllhc16.yaml
  - other_config.yaml
  - input_data.parquet

structure:
  # First generation is always at the root of the study
  # such that config_hllhc16.yaml is accessible as ../config_hllhc16.yaml
  generation_1:
    executable: generation_1.py

  # Second generation depends on the config from the first generation
  generation_2:
    executable: generation_2_level_by_nb.py
    scans:
      qx:
        subvariables: [lhcb1, lhcb2]
        linspace: [62.305, 62.330, 26]
```

In this case, your main configuration should be adapted to have the following field (in the appropriate section):

```yaml
# Assuming other config will be called from generation 1
other_config: ../other_config.yaml
# Assuming input data will be called from generation 2
input_data: ../../input_data.parquet
```

If you run this simulation on a cluster, dont forget to declare the dependencies in the dictionary `dic_dependencies_per_gen`:

```python
dic_dependencies_per_gen = {
    1: ['other_config.yaml'],
    2: ['input_data.parquet']
}
submit(
    ...
    dic_dependencies_per_gen=dic_dependencies_per_gen,
    ...
)
```

Note that we don't need to put the main main_configuration (here `config_hllhc16.yaml`) in the dictionary of dependencies, as its path doesn't need to be mutated since the file is already copied to the job folder _on the node_ by the `run.sh` file. In practice, we could copy all the dependencies on the node (avoiding to mutate paths in the config), but it is at the cost of a more complex `run.sh` file. We chose to keep it simple.

## Python dependencies

Python dependencies are modules that are required by the study to run. They could be dealt with just like data dependencies, but they are not parameters of the study and don't really belong in the study configuration file.

Most likely, the simplest approach is to add the path of the folder containing them in your `sys.path` in the template script. For instance, if you have a folder `my_modules` containing the modules `module1.py` and `module2.py`, you could add the following lines at the beginning of your template script:

```python
import sys
sys.path.append('path/to/my_modules')
```

This path can be relative (more portable, but you need to adapt the path for each generation) or absolute. When submitting your study on a cluster, you need to use an absolute path to the folder containing the modules, as the script will be executed on the node.

Note that, if you add the python modules as dependencies to the config scan (just like for data dependencies), they will also be copied to the root of the job folder, which can be still be useful to have simpler relative paths in your template scripts. And in practice, nothing prevents you to follow the same workflow as with data dependencies, i.e. add the path to these modules to the main configuration file, and add them to the dictionary of dependencies `dic_dependencies_per_gen` when submitting the study on a cluster to mutate the paths to absolute. You can then load them in your template script by adding the path from the configuration file in your `sys.path`:

```python
import sys
sys.path.append(config['path_to_modules'])
```
