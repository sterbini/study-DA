# Installing the optics

Optics are the heart of any collider simulation. In this section, we will explain how to install the optics that are available for the package: HL-LHC v1.6, HL-LHC v1.3, Run III, and Run III ions.

First, move to or create the directory where you want to install the optics.

## HL-LHC v1.6 optics

To clone the HL-LHC optics v1.6, run the following command:

```bash
git clone https://gitlab.cern.ch/acc-models/acc-models-lhc.git -b hl16
```

## HL-LHC v1.3 optics

To clone the HL-LHC optics v1.3, run the following command:

```bash
git clone https://github.com/ColasDroin/hllhc13.git
```

## Run III and Run III ions optics

Unfortunately, the Run III and Run III ions optics are not available as public repositories yet. They might be added to the [https://github.com/lhcopt](https://github.com/lhcopt) organization in the future. In the meanwhile, you will need to use the optics [directly from AFS](/afs/cern.ch/eng/lhc/optics/runIII) (you can copy the directory wherever you like of course, but that's not needed), as already done in the [template configuration files](../template_files/configurations/config_runIII.md).