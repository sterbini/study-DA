"""
This module provides utility functions for file compression.

Functions:
    compress_and_write(path_to_file: str) -> str:
        Compresses a file using ZIP compression and writes it to disk, then removes the original
        uncompressed file.

Imports:
    os: Provides a way of using operating system dependent functionality like reading or writing to
        the file system.
    zipfile: Provides tools to create, read, write, append, and list a ZIP file.
"""
# ==================================================================================================
# --- Imports
# ==================================================================================================

# Import standard library modules
import os
from zipfile import ZIP_DEFLATED, ZipFile

# Import third-party modules

# Import user-defined modules


# ==================================================================================================
# --- Function definition
# ==================================================================================================
def compress_and_write(path_to_file: str) -> str:
    """Compress a file and write it to disk.

    Args:
        path_to_file (str): Path to the file to compress.
    Returns:
        path_to_output (str): Path to the output file.

    """
    with ZipFile(
        f"{path_to_file}.zip",
        "w",
        ZIP_DEFLATED,
        compresslevel=9,
    ) as zipf:
        zipf.write(path_to_file)

    # Remove the uncompressed file
    os.remove(path_to_file)

    return f"{path_to_file}.zip"
