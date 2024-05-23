# ==================================================================================================
# --- Imports
# ==================================================================================================
# Import standard library modules

# Import third-party modules
from xmask.lhc import install_errors_placeholders_hllhc

# Import user-defined modules
from ..hllhc16.optics_specific_tools import (  # noqa: F401
    apply_optics,
    check_madx_lattices,
)


# ==================================================================================================
# --- Functions specific to each (HL-)LHC version
# ==================================================================================================
def build_sequence(
    mad,
    mylhcbeam,
    beam_config,  # Not used but important for consistency with other optics
    ignore_cycling=False,
    slice_factor=None,  # Not used but important for consistency with other optics
    BFPP=False,  # Not used but important for consistency with other optics
):
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
