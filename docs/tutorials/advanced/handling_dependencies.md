# Handling dependencies

Two types of dependencies might be required by a given study: data or configuration (i.e. files ending `.parquet`, `.txt`, `.yaml`, etc.), and python modules. There are various ways of handling these dependencies, but we're just going to provide the simpler approach here.

## Data dependencies

Data dependencies are files that are required by the study to run. In the approach we suggest, these files should be:

1. Declared as dependencies in the study's scan configuration (optional, but better for portability).
2. Declared as parameters in the study's main configuration, with relative or absolute paths.
3. If running the study on a cluster, declared in the dictionary of dependencies `dic_dependencies_per_gen` which is passed to the `submit()` function.

Indeed, dependencies which are declared in the study scan configuration will be automatically copied and placed at the root of the study. This way, the study can access them using relative paths (which must be adapted for each generation, of course. 

You can do that either by having several paths in the configuration, or by prefixing appropriately the path using `../` in the template script), or absolute path (simpler, but less portable). In any case, if the study is run on a cluster, the relative paths will be mutated to be absolute paths.

For instance, your scan configuration could look like something like this:

```yaml title="config_scan.yaml"
# ==================================================================================================
# --- Structure of the study ---
# ==================================================================================================
name: example_tune_scan

# List all useful files that will be used by executable in generations below
# These files are placed at the root of the study
dependencies:
  main_configuration: config_hllhc16.yaml
  others:
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

```yaml title="config_hllhc16.yaml"
# Assuming other config will be called from generation 1
other_config: ../other_config.yaml
# Assuming input data will be called from generation 2
input_data: ../../input_data.parquet
```

If you run this simulation on a cluster, dont forget to declare the dependencies in the dictionary `dic_dependencies_per_gen`:

```python title="submit.py"
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

Most likely, the simplest approach is to simply add your python modules as dependencies in the scan configuration, and to import them in your template script. Indeed, the python modules will be copied to the root of the study, and, in the provided template scripts, the path to the root of the study is automatically added to the `sys.path` of the python script. This way, you can import your modules directly in your template script (after the lines corresponding to adding the path to the root of the study to the `sys.path`, of course).

For instance, your scan configuration could look like something like this:

```yaml title="config_scan.yaml"
# ==================================================================================================
# --- Structure of the study ---
# ==================================================================================================
name: example_tune_scan

# List all useful files that will be used by executable in generations below
# These files are placed at the root of the study
dependencies:
  main_configuration: config_hllhc16.yaml
  others:
    - modules/my_module.py

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

In this case, you can import your module directly in your template script (providing also the placeholder to be replaced by the path to the root of the study):

```python
...
path_root_study = "{}  ###---path_root_study---###"
sys.path.append(path_root_study)
import my_module
```

This import will also work from clusters since the path to the root of the study is absolute.
