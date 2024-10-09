"""This class is used to inspect and compute some properties of the filling scheme."""

# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import json
import os

# Import third-party modules
import numpy as np

# Import user-defined modules


# ==================================================================================================
# --- Function definition
# ==================================================================================================


def reformat_filling_scheme_from_lpc(
    filling_scheme_path: str, filling_scheme_path_converted: str
) -> tuple[np.ndarray, np.ndarray]:
    """
    This function is used to convert the filling scheme from the LPC to the format used in the
    xtrack library. The filling scheme from the LPC is a list of bunches for each beam, where each
    bunch is represented by a 1 in the list. The function converts this list to a list of indices
    of the filled bunches. The function also returns the indices of the filled bunches for each beam.

    Args:
        filling_scheme_path (str): Path to the filling scheme file.
        filling_scheme_path_converted (str): Path to the converted filling scheme file.

    Returns:
        tuple[np.ndarray, np.ndarray]: Indices of the filled bunches for each beam.
    """

    # Load the filling scheme directly if json
    with open(filling_scheme_path, "r") as fid:
        data = json.load(fid)

    # Take the first fill number
    fill_number = list(data["fills"].keys())[0]

    # Do the conversion (Matteo's code)
    B1 = np.zeros(3564)
    B2 = np.zeros(3564)
    l_lines = data["fills"][f"{fill_number}"]["csv"].split("\n")
    for idx, line in enumerate(l_lines):
        # First time one encounters a line with 'Slot' in it, start indexing
        if "Slot" in line:
            # B1 is initially empty
            if np.sum(B1) == 0:
                for line_2 in l_lines[idx + 1 :]:
                    l_line = line_2.split(",")
                    if len(l_line) > 1:
                        slot = l_line[1]
                        B1[int(slot)] = 1
                    else:
                        break

            elif np.sum(B2) == 0:
                for line_2 in l_lines[idx + 1 :]:
                    l_line = line_2.split(",")
                    if len(l_line) > 1:
                        slot = l_line[1]
                        B2[int(slot)] = 1
                    else:
                        break
            else:
                break

    data_json = {"beam1": [int(ii) for ii in B1], "beam2": [int(ii) for ii in B2]}

    with open(filling_scheme_path_converted, "w") as file_bool:
        json.dump(data_json, file_bool)
    return B1, B2


def load_and_check_filling_scheme(filling_scheme_path: str) -> str:
    """Load and check the filling scheme from a JSON file. Convert the filling scheme to the correct
    format if needed.

    Args:
        filling_scheme_path (str): Path to the filling scheme file.

    Returns:
        str: Path to the converted filling scheme file.
    """
    if not filling_scheme_path.endswith(".json"):
        raise ValueError("Filling scheme must be in json format")

    # Check that the converted filling scheme doesn't already exist
    filling_scheme_path_converted = filling_scheme_path.replace(".json", "_converted.json")
    if os.path.exists(filling_scheme_path_converted):
        return filling_scheme_path_converted

    with open(filling_scheme_path, "r") as fid:
        d_filling_scheme = json.load(fid)

    if "beam1" in d_filling_scheme.keys() and "beam2" in d_filling_scheme.keys():
        # If the filling scheme not already in the correct format, convert
        if "schemebeam1" in d_filling_scheme.keys() or "schemebeam2" in d_filling_scheme.keys():
            d_filling_scheme["beam1"] = d_filling_scheme["schemebeam1"]
            d_filling_scheme["beam2"] = d_filling_scheme["schemebeam2"]
            # Delete all the other keys
            d_filling_scheme = {
                k: v for k, v in d_filling_scheme.items() if k in ["beam1", "beam2"]
            }
            # Dump the dictionary back to the file
            with open(filling_scheme_path_converted, "w") as fid:
                json.dump(d_filling_scheme, fid)

            # Else, do nothing

    else:
        # One can potentially use b1_array, b2_array to scan the bunches later
        b1_array, b2_array = reformat_filling_scheme_from_lpc(
            filling_scheme_path, filling_scheme_path_converted
        )
        filling_scheme_path = filling_scheme_path_converted

    return filling_scheme_path


def _compute_LR_per_bunch(
    _array_b1: np.ndarray,
    _array_b2: np.ndarray,
    _B1_bunches_index: np.ndarray,
    _B2_bunches_index: np.ndarray,
    number_of_LR_to_consider: int | list[int],
    beam: str = "beam_1",
) -> list[int]:
    # Reverse beam order if needed
    if beam == "beam_1":
        factor = 1
    elif beam == "beam_2":
        _array_b1, _array_b2 = _array_b2, _array_b1
        _B1_bunches_index, _B2_bunches_index = _B2_bunches_index, _B1_bunches_index
        factor = -1
    else:
        raise ValueError("beam must be either 'beam_1' or 'beam_2'")

    B2_bunches = np.array(_array_b2) == 1.0

    # Define number of LR to consider
    if isinstance(number_of_LR_to_consider, int):
        number_of_LR_to_consider = [
            number_of_LR_to_consider,
            number_of_LR_to_consider,
            number_of_LR_to_consider,
        ]

    l_long_range_per_bunch = []
    number_of_bunches = 3564

    for n in _B1_bunches_index:
        # First check for collisions in ALICE

        # Formula for head on collision in ALICE is
        # (n + 891) mod 3564 = m
        # where n is number of bunch in B1, and m is number of bunch in B2

        # Formula for head on collision in ATLAS/CMS is
        # n = m
        # where n is number of bunch in B1, and m is number of bunch in B2

        # Formula for head on collision in LHCb is
        # (n + 2670) mod 3564 = m
        # where n is number of bunch in B1, and m is number of bunch in B2

        colide_factor_list = [891, 0, 2670]
        # i == 0 for ALICE
        # i == 1 for ATLAS and CMS
        # i == 2 for LHCB
        num_of_long_range = 0
        l_HO = [False, False, False]
        for i in range(3):
            collide_factor = colide_factor_list[i]
            m = (n + factor * collide_factor) % number_of_bunches

            # if this bunch is true, then there is head on collision
            l_HO[i] = B2_bunches[m]

            ## Check if beam 2 has bunches in range  m - number_of_LR_to_consider to m + number_of_LR_to_consider
            ## Also have to check if bunches wrap around from 3563 to 0 or vice versa

            bunches_ineraction_temp = np.array([])
            positions = np.array([])

            first_to_consider = m - number_of_LR_to_consider[i]
            last_to_consider = m + number_of_LR_to_consider[i] + 1

            if first_to_consider < 0:
                bunches_ineraction_partial = np.flatnonzero(
                    _array_b2[(number_of_bunches + first_to_consider) : (number_of_bunches)]
                )

                # This represents the relative position to the head-on bunch
                positions = np.append(positions, first_to_consider + bunches_ineraction_partial)

                # Set this varibale so later the normal syntax wihtout 
                # the wrap around checking can be used
                first_to_consider = 0

            if last_to_consider > number_of_bunches:
                bunches_ineraction_partial = np.flatnonzero(
                    _array_b2[: last_to_consider - number_of_bunches]
                )

                # This represents the relative position to the head-on bunch
                positions = np.append(positions, number_of_bunches - m + bunches_ineraction_partial)

                last_to_consider = number_of_bunches

            bunches_ineraction_partial = np.append(
                bunches_ineraction_temp,
                np.flatnonzero(_array_b2[first_to_consider:last_to_consider]),
            )

            # This represents the relative position to the head-on bunch
            positions = np.append(positions, bunches_ineraction_partial - (m - first_to_consider))

            # Substract head on collision from number of secondary collisions
            num_of_long_range_curren_ip = len(positions) - _array_b2[m]

            # Add to total number of long range collisions
            num_of_long_range += num_of_long_range_curren_ip

        # If a head-on collision is missing, discard the bunch by setting LR to 0
        if False in l_HO:
            num_of_long_range = 0

        # Add to list of long range collisions per bunch
        l_long_range_per_bunch.append(num_of_long_range)
    return l_long_range_per_bunch


def get_worst_bunch(
    filling_scheme_path: str, number_of_LR_to_consider: int = 26, beam="beam_1"
) -> int:
    """
    # Adapted from https://github.com/PyCOMPLETE/FillingPatterns/blob/5f28d1a99e9a2ef7cc5c171d0cab6679946309e8/fillingpatterns/bbFunctions.py#L233
    Given a filling scheme, containing two arrays of booleans representing the trains of bunches for
    the two beams, this function returns the worst bunch for each beam, according to their collision
    schedule.

    Args:
        filling_scheme_path (str): Path to the filling scheme file.
        number_of_LR_to_consider (int): Number of long range collisions to consider. Defaults to 26.
        beam (str): Beam for which to compute the worst bunch. Defaults to "beam_1".

    Returns:
        int: The worst bunch for the specified beam.

    """

    if not filling_scheme_path.endswith(".json"):
        raise ValueError("Only json filling schemes are supported")

    with open(filling_scheme_path, "r") as fid:
        filling_scheme = json.load(fid)
    # Extract booleans beam arrays
    array_b1 = np.array(filling_scheme["beam1"])
    array_b2 = np.array(filling_scheme["beam2"])

    # Get bunches index
    B1_bunches_index = np.flatnonzero(array_b1)
    B2_bunches_index = np.flatnonzero(array_b2)

    # Compute the number of long range collisions per bunch
    l_long_range_per_bunch = _compute_LR_per_bunch(
        array_b1, array_b2, B1_bunches_index, B2_bunches_index, number_of_LR_to_consider, beam=beam
    )

    # Get the worst bunch for both beams
    if beam == "beam_1":
        worst_bunch = B1_bunches_index[np.argmax(l_long_range_per_bunch)]
    elif beam == "beam_2":
        worst_bunch = B2_bunches_index[np.argmax(l_long_range_per_bunch)]
    else:
        raise ValueError("beam must be either 'beam_1' or 'beam_2")

    # Need to explicitly convert to int for json serialization
    return int(worst_bunch)
