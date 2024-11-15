# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import user-defined modules
from study_da import create

# ==================================================================================================
# --- Script to generate a study
# ==================================================================================================
# Generate the arrays of parameters to scan
l_qx = []
l_qy = []
l_qx_for_naming = []
l_qy_for_naming = []
l_n_split = []
l_n_split_for_naming = []

for qx in [62.310, 62.311]:
    for qy in [60.320, 60.321]:
        for n_split in range(5):
            l_qx.append({key: qx for key in ["lhcb1", "lhcb2"]})
            l_qy.append({key: qy for key in ["lhcb1", "lhcb2"]})
            l_qx_for_naming.append(qx)
            l_qy_for_naming.append(qy)
            l_n_split.append(f"{n_split:02d}.parquet")
            l_n_split_for_naming.append(n_split)

# Store the parameters in a dictionary
dic_parameter_all_gen = {
    "generation_2": {
        "qx": l_qx,
        "qy": l_qy,
        "n_split": l_n_split,
    }
}

dic_parameter_all_gen_naming = {
    "generation_2": {
        "qx": l_qx_for_naming,
        "qy": l_qy_for_naming,
        "n_split": l_n_split_for_naming,
    }
}

# Generate the study in the local directory
path_tree, name_main_config = create(
    path_config_scan="config_scan.yaml",
    dic_parameter_all_gen=dic_parameter_all_gen,
    dic_parameter_all_gen_naming=dic_parameter_all_gen_naming,
)
