#!/bin/bash
# Load the environment
source /afs/cern.ch/work/c/cdroin/private/study-DA/.venv/bin/activate

# Move into the job folder and run it
cd /afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/single_collider_hllhc16/single_job_study_hllhc16/generation_1

python generation_1.py > output_python.txt 2> error_python.txt

# Ensure job run was successful and tag as finished
if [ $? -eq 0 ]; then
    python -m study_da.submit.scripts.log_finish /afs/cern.ch/work/c/cdroin/private/study-DA/tests/generate_and_submit/single_collider_hllhc16/single_job_study_hllhc16/tree.yaml generation_1 generation_1
fi

# Store abs path as a variable in case it's needed for additional commands
path_job=$(pwd)
# Optional user defined command to run
rm -rf final_* modules optics_repository optics_toolkit tools tracking_tools temp mad_collider.log __pycache__ twiss* errors fc* optics_orbit_at* 

