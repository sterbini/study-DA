# Submission

## Introduction

Submitting studies is one of the main functionalities of the study-da package. To understand how this is done, we will keep playing with the dummy example presented in the [first part of this tutorial](./1_generation.md).

## Submitting the study

Each job can be either submitted locally or on a cluster. Similarly, each job can be submitted to run on the CPU or on the GPU through a given context. When not configured, study-DA will prompt the user about the configuration of job at submission.

### Submitting locally

To start simple, let's submit the jobs locally. Have a look at the following code:

```py title="generate_and_submit.py" linenums="1"
from study_da import create, submit
path_tree, main_configuration_file = create(path_config_scan="config_scan.yaml", force_overwrite=False)
submit(
    path_tree=path_tree,
    path_python_environment="/afs/cern.ch/work/u/user/private/study-DA/.venv",
    name_config=main_configuration_file,
    keep_submit_until_done=True,
    wait_time=0.1,
)
```

The first part of this code is identical to what was done in the first part of this tutorial (except that we now explictely ask not to recreate the study everytime we re-run the script). The second part is the submission of the study. The `submit` function takes the following arguments:

- `path_tree` is the path to the study folder. We get this directly from the `create` function.
- `path_python_environment` is the path to the python environment that will be used to run the jobs. You have to configure this path according to your own environment.
- name_config is the name of the main configuration file for your study. This is also directly returned by the `create` function, from the configuration scan file.
- keep_submit_until_done is a boolean that allows to keep the submission script running until all jobs are done. This is useful when you want to submit a study and wait for it to be completed.
- wait_time is the time in seconds between each check of the status of the jobs. This is useful to avoid overloading the system with too many checks. We asked for 0.1 minutes here, meaning that the jobs will be checked and potentially re-submitted every 6 seconds.

When running this script, you get prompted to configure the submission for each job. In this case, we assume that we run all the jobs locally, on the CPU. Directly after the submission, you should get the following output:

```bash
State of the jobs:
********************************
Generation 1
Jobs left to submit later: 0
Jobs running or queuing: 0
Jobs submitted now: 2
Jobs finished: 0
Jobs failed: 0
Jobs on hold due to failed dependencies: 0
********************************
********************************
Generation 2
Jobs left to submit later: 6
Jobs running or queuing: 0
Jobs submitted now: 0
Jobs finished: 0
Jobs failed: 0
Jobs on hold due to failed dependencies: 0
********************************
```

No need to explain more here as this is quite explicit, but you can observe that the status of each individual job is tracked and recorded at each (re)-submission. This is very useful when making large, multi-generational studies, in which some of the jobs will inexorably fail for various reasons.

You can also observe that, in the study folder, run files have appeared as `run.sh`, basically instructing the machine that will run the job (here, the local machine) how to proceed:

```bash title="run.sh"
#!/bin/bash
# Load the environment
source /afs/cern.ch/work/c/cdroin/private/study-DA/.venv/bin/activate

# Move into the job folder
cd /afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/dummy_custom_template/example_dummy/x_1

# Run the job and tag
python generation_1.py > output_python.txt 2> error_python.txt

# Ensure job run was successful and tag as finished, or as failed otherwise
if [ $? -eq 0 ]; then
    touch /afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/dummy_custom_template/example_dummy/x_1/.finished
else
    touch /afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/dummy_custom_template/example_dummy/x_1/.failed
fi

# Store abs path as a variable in case it's needed for additional commands
path_job=$(pwd)
# Optional user defined command to run
```

There's nothing too fancy here: the script loads the python environment, moves to the job folder, runs the python script, and tags the job as finished or failed depending on the return code of the python script. As soon as the job reach completion, some `.finished` files appear in the study folder (or `failed`if they fail). This is a way to keep track of the jobs that have been completed, and to avoid re-submitting them.

The optional user defined command to run at the end can be provided through an argument called `dic_additional_commands_per_gen`, which takes the generation number as key, and the additional command as value. This is useful when you want to run some additional commands after the completion of a generation, such as cleaning the output folder from temporary files, copying the results to a specific folder, or sending an email to the user. This will be illustrated in the [Configuration and Tracking section](../configuration_tracking/practical_example.md).

After a dozen seconds, the script should finish for good. When checking the tree, you should get the following output (cropped for clarity):

```yaml title="tree.yaml"
x_1:
  generation_1:
    file: example_dummy/x_1/generation_1.py
    context: cpu
    submission_type: local
    htc_flavor:
    status: finished
    path_run: 
      /afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/dummy_custom_template/example_dummy/x_1/run.sh
  y_1.0:
    generation_2:
      file: example_dummy/x_1/y_1.0/generation_2.py
      context: cpu
      submission_type: local
      htc_flavor:
      status: finished
      path_run: 
        /afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/dummy_custom_template/example_dummy/x_1/y_1.0/run.sh
    ...
python_environment: /afs/cern.ch/work/c/cdroin/private/study-DA/.venv/bin/activate
container_image:
absolute_path: 
  /afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/dummy_custom_template
status: finished
configured: true
```

As you can see, the tre file keeps track of everything that has been done, and the status of each job. When the status of each individual job is finished, the tree itself gets tagged as finished. From here, one can actually retrieve the results of the study, and analyze them. This will be part of the next section of this tutorial: [Analysis](3_analysis.md).

### Submitting to HTCondor

The procedure for submitting to HTCondor (or Slurm) is fairly similar, but there are a few tricky points to consider:

- If you don't use an (externally hosted) Docker distribution, you might want to ensure that your Python environment is available from the cluster. Otherwise, the cluster will not be able to run the scripts.
- You have to ensure that the dependencies for each file are correctly defined in the configuration file. This is crucial for them to be copied on the cluster node, so that the jobs can run correctly.
- The relative paths in the main configuration should get mutated to fit the cluster environment. This is done automatically by the `submit` function for all the dependencies that are specified in the `dic_dependencies_per_gen` argument (not requested in the current example since the only dependency is the configuration, that is handled by default), but keep in mind that this might be a source of errors.

Here is the same example as before, this time submitting to HTCondor using a Docker container:

```py title="generate_and_submit.py" linenums="1"
from study_da import create, submit

# Generate the study in the local directory
path_tree, main_configuration_file = create(
    path_config_scan="config_scan.yaml", force_overwrite=False
)

path_python_environment_container = "/usr/local/DA_study/miniforge_docker"
path_container_image = (
    "/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cdroin/da-study-docker:0b46f2bb"
)

# Dic copy_back_per_gen (only for HTC)
dic_copy_back_per_gen = {
    2: {"txt": True},
}

# Preconfigure submission to HTC
dic_config_jobs = {
    "generation_1" + ".py": {
        "context": "cpu",
        "submission_type": "htc_docker",
        "htc_flavor": "espresso",
    },
    "generation_2" + ".py": {
        "context": "cpu",
        "submission_type": "htc_docker",
        "htc_flavor": "espresso",
    },
}

# Submit the study
submit(
    path_tree=path_tree,
    name_config=main_configuration_file,
    path_python_environment_container=path_python_environment_container,
    path_container_image=path_container_image,
    dic_copy_back_per_gen=dic_copy_back_per_gen,
    dic_config_jobs=dic_config_jobs,
    keep_submit_until_done=True,
    wait_time=2,
)
```

Some new variables and/or arguments are introduced here:

- `path_python_environment_container` is the path to the python environment that will be used to run the jobs. This time, we use a Docker container, so the path is different from the local one.
- `path_container_image` is the path to the Docker image that will be used to run the jobs. This is a specific image that has been built for the study-da package.
- `dic_copy_back_per_gen` is a dictionary that allows to specify which files will be copied back from the cluster to the local machine after the completion of the jobs. This is useful when you want to retrieve the results of the study, or some intermediate files that have been generated during the study. In this case, a text file has been produced during the second generation, so we set the value to `True` for `txt` for the second generation. Possible file extensions are `parquet`, `yaml`, `txt`, `json`, `zip` and `all` (in which case all files will be copied back).
- dic_config_jobs is a dictionary that allows to preconfigure the submission of the jobs. This is useful when you don't want to get prompted for each job. In this case, we set the context to `cpu`, the submission type to `htc`, and the flavor to `espresso` for all the jobs, since our scripts are very simple.

!!! warning "Copying back large file is not recommended"

    Copying back large files on AFS can easily throttle the network, especially when you're running thousands of jobs at the same time.

!!! bug "Don't forget to provide an environment if you don't use a Docker container"

    If you submit on HTC but don't use a Docker container (or submit locally), you have to provide the path to the python environment on the cluster using the `path_python_environment` argument.

You should get more or less the same output as before, except that your jobs are now most likely queued on the cluster (for confirmation, you can check the status of your jobs using the `condor_q` command). In the meanwhile, we can have a look at one of the new run files, for instance for the second generation (if you run the script above, remember that you have to wait for the second generation to be submitted to have the run files created):

```bash title="dummy_custom_template/example_dummy/x_2/y_1.0/run.sh"
#!/bin/bash
# Load the environment
source /usr/local/DA_study/miniforge_docker/bin/activate

# Copy config in (what will be) the level above
cp -f /afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/dummy_custom_template/example_dummy/x_2/y_1.0/../config_dummy.yaml .

# Create local directory on node and cd into it
mkdir y_1.0
cd y_1.0

# Mutate the paths in config to be absolute

# Run the job and tag
python /afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/dummy_custom_template/example_dummy/x_2/y_1.0/generation_2.py > output_python.txt 2> error_python.txt


# Ensure job run was successful and tag as finished, or as failed otherwise
if [ $? -eq 0 ]; then
    touch /afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/dummy_custom_template/example_dummy/x_2/y_1.0/.finished
else
    touch /afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/dummy_custom_template/example_dummy/x_2/y_1.0/.failed
fi

# Delete the config file from the above directory, otherwise it will be copied back and overwrite the new config
rm ../config_dummy.yaml
# Copy back output, including the new config
cp -f *.parquet *.yaml *.txt /afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/dummy_custom_template/example_dummy/x_2/y_1.0

# Store abs path as a variable in case it's needed for additional commands
path_job=/afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/dummy_custom_template/example_dummy/x_2/y_1.0

# Optional user defined command to run

```

The file should have self-explanatory comments. There are however severla difference:

    - The environment is loaded from the Docker container
    - The configuration file is copied in the job folder on the node (and the output configuration file is copied back to the local machine after the completion of the job)
    - Some paths in the configuration file (declared as ```dependencies```) are mutated to be absolute, so that they can be accessed from the cluster node. In this case, there are no dependencies. 
    - The output files are copied back to the local machine after the completion of the job. By default, only light files are copied back (parquet, yaml, txt). In we had set the ```dic_copy_back_per_gen``` argument to ```{"txt": False}```, the output would not have been copied back.
  
# ! TODO: Give a link to a case with dependencies

If all goes well, after a while (this depends on the load on the cluster), the `result.txt` should be copied back to the local machine for each leaf of the tree that has been tagged as finished (all, normally). We now have to automatically retrieve all these results, this is part of the next section of this tutorial: [Analysis](3_analysis.md).
