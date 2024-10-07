# ==================================================================================================
# --- Imports
# ==================================================================================================
# Import standard library modules
from typing import Any

# Import third-party modules
from cpymad.madx import Madx
from xmask.lhc import install_errors_placeholders_hllhc

# Import user-defined modules
from ..hllhc16.optics_specific_tools import apply_optics as apply_optics_hllhc16
from ..hllhc16.optics_specific_tools import (
    check_madx_lattices as check_madx_lattices_hllhc16,
)

# ==================================================================================================
# --- Functions specific to each (HL-)LHC version
# ==================================================================================================


def check_madx_lattices(*args: Any, **kwargs: Any) -> None:
    """Check the consistency of the MAD-X lattice for the (HL-)LHC.

    Args:
        *args (Any): See hllhc16.optics_specific_tools.check_madx_lattices.
        **kwargs (Any): See hllhc16.optics_specific_tools.check_madx_lattices.

    Returns:
        None
    """
    check_madx_lattices_hllhc16(*args, **kwargs)


def build_sequence(
    mad: Madx,
    mylhcbeam: int,
    beam_config: dict[str, Any],  # Not used but important for consistency with other optics
    ignore_cycling: bool = False,
    slice_factor: int | None = None,  # Not used but important for consistency with other optics
    BFPP: bool = False,  # Not used but important for consistency with other optics
) -> None:
    """Build the sequence for the (HL-)LHC, for a given beam.

    Args:
        mad (Madx): The MAD-X object used to build the sequence.
        mylhcbeam (int): The beam number (1, 2 or 4).
        beam_config (dict[str, Any]): The configuration of the beam from the configuration file.
        ignore_cycling (bool, optional): Whether to ignore cycling to have IP3 at position s=0.
            Defaults to False.
        slice_factor (int | None, optional): The slice factor if optic is not thin. Defaults to None.
        BFPP (bool, optional): Whether to use the BFPP knob. Defaults to False.

    Returns:
        None
    """

    # Select beam
    mad.input(f"mylhcbeam = {mylhcbeam}")

    # Build sequence
    mad.input("""
      ! Build sequence
      option, -echo,-warn,-info;
      if (mylhcbeam==4){
        call,file="acc-models-lhc/lhcb4.seq";
      } else {
        call,file="acc-models-lhc/lhc.seq";
      };
      !Install HL-LHC
      call, file=
        "acc-models-lhc/hllhc_sequence.madx";
      ! Get the toolkit
      call,file=
        "acc-models-lhc/toolkit/macro.madx";
      option, -echo, warn,-info;
      """)

    mad.input("""
      ! Slice nominal sequence
      exec, myslice;
      """)

    mad.input("""exec,mk_beam(7000);""")

    install_errors_placeholders_hllhc(mad)

    if not ignore_cycling:
        mad.input("""
        !Cycling w.r.t. to IP3 (mandatory to find closed orbit in collision in the presence of errors)
        if (mylhcbeam<3){
        seqedit, sequence=lhcb1; flatten; cycle, start=IP3; flatten; endedit;
        };
        seqedit, sequence=lhcb2; flatten; cycle, start=IP3; flatten; endedit;
        """)

    # Incorporate crab-cavities
    mad.input("""
    ! Install crab cavities (they are off)
    call, file='acc-models-lhc/toolkit/enable_crabcavities.madx';
    on_crab1 = 0;
    on_crab5 = 0;
    """)

    mad.input("""
        ! Set twiss formats for MAD-X parts (macro from opt. toolkit)
        exec, twiss_opt;
        """)


def apply_optics(*args: Any, **kwargs: Any) -> None:
    """Apply the optics to the MAD-X model.

    Args:
        *args (Any): See hllhc16.optics_specific_tools.apply_optics.
        **kwargs (Any): See hllhc16.optics_specific_tools.apply_optics.

    Returns:
        None
    """
    apply_optics_hllhc16(*args, **kwargs)
