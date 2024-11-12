# %%
import logging

from study_da import SubmitScan

# Set up the logger
# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# %%
study_sub = SubmitScan(
    path_tree="example_dummy_stress/tree.yaml",
    path_python_environment="/afs/cern.ch/work/c/cdroin/private/study-DA/.venv",
)

study_sub.configure_jobs(force_configure=True)

# %%
# study_sub.submit()
study_sub.keep_submit_until_done(
    wait_time=1 / 20, name_config="custom_config.yaml", one_generation_at_a_time=True
)
