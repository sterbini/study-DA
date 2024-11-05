# Working with a single collider

The special function ```create_single_job()``` can be used to build and configure a collider without having to manually configure an irrelevant scan.

Assuming you'd like to work with the template [`hllhc16` configuration](../template_files/configurations/config_hllhc16.md), along with the template scripts [`generation_1.py`](../template_files/scripts/generation_1.md) and [`generation_2_level_by_nb.py`](../template_files/scripts/generation_2_level_by_nb.md), saving the collider before tracking and only track for 1000 turns, you could proceed as follows:

```py title="single_collider.py"
# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import os

# Import user-defined modules
from study_da.utils import load_template_configuration_as_dic, write_dic_to_path

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================

# Load the configuration from hllhc16
name_template_config = "config_hllhc16.yaml"
config, ryaml = load_template_configuration_as_dic(name_template_config)

# Update the location of acc-models
config["config_mad"]["links"]["acc-models-lhc"] = (
    "../../../../../external_dependencies/acc-models-lhc"
)

# Adapt the number of turns
config["config_simulation"]["n_turns"] = 1000

# Save the collider produced after the configuration step
config["config_collider"]["save_output_collider"] = True

# Drop the configuration locally
local_config_name = "local_config.yaml"
write_dic_to_path(config, local_config_name, ryaml)

# Now generate the study in the local directory
path_tree = create_single_job(
    name_main_configuration=local_config_name,
    name_executable_generation_1="generation_1.py",
    name_executable_generation_2="generation_2_level_by_nb.py",
    name_study="single_job_study_hllhc16",
)

# Delete the configuration file (it's copied in the study folder anyway)
os.remove(local_config_name)
```

At this point, the following directory structure will be created:

```bash
📁 single_job_study_hllhc16/
├─╴📁 generation_1/
│   ├── 📄 generation_1.py
│   └── 📁 generation_2/
│        ├── 📄 generation_2.py
├─ 📄 tree.yaml
└─ 📄 local_config.yaml
```

The ```tree.yaml```, later used for submission, contains exactly this simple structure:

```yaml
generation_1:
  generation_1:
    file: single_job_study_hllhc16/generation_1/generation_1.py
  generation_2:
    generation_2:
      file: single_job_study_hllhc16/generation_1/generation_2/generation_2.py
```

From here, you can run the two generations one after the other using the ```submit``` function:

```py title="single_collider.py"
from study_da import submit

# Define the variables of interest for the submission
path_python_environment = "path/to/python/environment"

# Preconfigure submission to local, so that you don't get prompted for the submission type
dic_config_jobs = {
    "generation_1" + ".py": {
        "context": "cpu",
        "submission_type": "local",
    },
    "generation_2" + ".py": {
        "context": "cpu",
        "submission_type": "local",
    },
}

# Since gen_1 is submitted locally, add a command to remove unnecessary files
dic_additional_commands_per_gen = {
    1: "rm -rf final_* modules optics_repository optics_toolkit tools tracking_tools temp "
    "mad_collider.log __pycache__ twiss* errors fc* optics_orbit_at* \n",
    2: "",
}

# Submit the study
submit(
    path_tree=path_tree, # path to the study tree
    path_python_environment=path_python_environment, # path to the python environment
    name_config=local_config_name, # configuration file for the execution
    dic_config_jobs=dic_config_jobs, # preconfigure submission to local
    dic_additional_commands_per_gen=dic_additional_commands_per_gen, # remove unnecessary files
    keep_submit_until_done=True, # keep submitting until all jobs are done
    wait_time=1, # wait 1mn before checking the status of the jobs and resubmitting
)
```

This will complete the tree with the submission settings, generate the run files to launch the jobs, and the study will be executed in the local environment. Everytime a generation job is launched, the configuration file is mutated copied from the above generation folder, before being mutated at the end of the generation job, with the requested parameters (in this case, none, since no scan is being performed).

After running the jobs, the directory should therefore looks like something like this (ignoring the intermediate and temporary files):

```bash
📁 single_job_study_hllhc16/
├─╴📁 generation_1/
│   ├── 📄 generation_1.py
│   ├── 📄 run.sh
│   ├── 📁 particles/
│   │   └── 📄 xx.parquet
│   ├── 📄 local_config.yaml
│   └── 📁 generation_2/
│        ├── 📄 generation_2.py
│        ├── 📄 run.sh
│        ├── 📄 local_config.yaml
│        ├── output_particles.parquet
│        └── collider_file_for_tracking.json
├─ 📄 tree.yaml
└─ 📄 local_config.yaml
```

And the final tree will be (the paths will be different for you):

```yaml
generation_1:
  generation_1:
    file: single_job_study_hllhc16/generation_1/generation_1.py
    context: cpu
    submission_type: local
    status: finished
    path_run: 
      /afs/cern.ch/work/u/user/private/study-DA/tests/generate_and_submit/single_collider_hllhc16/single_job_study_hllhc16/generation_1/run.sh
  generation_2:
    generation_2:
      file: single_job_study_hllhc16/generation_1/generation_2/generation_2.py
      context: cpu
      submission_type: local
      status: finished
      path_run: 
        /afs/cern.ch/work/u/user/private/study-DA/tests/generate_and_submit/single_collider_hllhc16/single_job_study_hllhc16/generation_1/generation_2/run.sh
python_environment: /afs/cern.ch/work/u/user/private/study-DA/.venv/bin/activate
container_image:
absolute_path: 
  /afs/cern.ch/work/u/user/private/study-DA/tests/generate_and_submit/single_collider_hllhc16
status: finished
configured: true
```

From here, one can load the collider file ```collider_file_for_tracking.json``` with Xsuite and/or check the result of the tracking using the file ```output_particles.parquet```. If you want to inspect the collider object, you can use the [collider-dashboard package](https://github.com/ColasDroin/collider-dashboard), which should be fully compatible with the collider file produced here:

```bash
python -m collider_dashboard -c /path_to_adapt/single_collider_hllhc16/single_job_study_hllhc16/generation_1/generation_2/collider_file_for_configuration.json
```
