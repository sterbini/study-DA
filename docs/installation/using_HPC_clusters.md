# Using High-Performance Computing (HPC) Clusters w or w/o Docker

## Setting up the clusters

study-DA should allow for an easy deployment of the simulations on HTCondor (CERN cluster) and Slurm (CNAF.INFN cluster). Please consult the corresponding tutorials ([here](https://abpcomputing.web.cern.ch/guides/htcondor/), and [here](https://abpcomputing.web.cern.ch/computing_resources/hpc_cnaf/)) to set up the clusters on your machine.

You will get prompted on which machine the jobs should run (HTC, Slurm or locally) when submitting your study.

## Using Docker images

For reproducibility purposes and/or limiting the load on AFS drives (for CERN user), one can use Docker images to run the simulations. A registry of Docker images is available at ```/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/```, and some ready-to-use for DA simulations Docker images on HTC or Slurm are available at ```/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cdroin/da-study-docker```.

To learn more about building Docker images and hosting them on the CERN registry, please consult the [corresponding tutorial](https://abpcomputing.web.cern.ch/guides/docker_on_htcondor/) abd the [corresponding repository](https://gitlab.cern.ch/unpacked/sync).

### With HTCondor

When running simulations on HTCondor, Docker images are being pulled directly from CVMFS by the node. No more configuration than the usual arguments of the `submit` function is needed.

### With Slurm

Things are a bit tricker with Slurm, as the Docker image must first be manually pulled from CVMFS, and then loaded on the node after Singularity-ize it. The pulling of the image is only needed the first time, and can be done with e.g. (for the image ```cdroin/da-study-docker```):
  
  ```bash
  singularity pull docker://gitlab-registry.cern.ch/cdroin/da-study-docker:568403e2
  ```

!!! warning "Some nodes might not want to pull the image"

    Due to unknown reason, only some nodes of INFN-CNAF will correctly execute this command. For instance, it didn't work on the default CPU CERN node (```hpc-201-11-01-a```), but it did on an alternative one (```hpc-201-11-02-a```). We recommand using either ```hpc-201-11-02-a``` or a GPU node (e.g. ```hpc-201-11-35```) to pull the image. Once the image is pulled, it will be accessible from any node.

For testing purposes, one can then run the image with Singularity directly on the node (not required):
  
  ```bash
  singularity run da-study-docker_568403e2.sif
  ```

Once this is configured, you can just provide the path of the image to the `submit` function, and the script will take care of the rest.

!!! bug "The slurm docker scripts are kind of experimental"

    At the time of writing this documentation, symlinks path in the front-end node of INFN-CNAF are currently broken, meaning that some temporary fixs are implemented. This will hopefully be fixed byt the CNAF.INFN team in the future, and the fixs should not prevent the scripts from running anyway.
