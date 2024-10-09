# ==================================================================================================
# --- Imports
# ==================================================================================================
# Import standard library modules
import logging
from typing import Any

# Import third-party modules
import numpy as np
from cpymad.madx import Madx
from xmask.lhc import install_errors_placeholders_hllhc


# ==================================================================================================
# --- Functions specific to each (HL-)LHC version
# ==================================================================================================
def check_madx_lattices(mad: Madx) -> None:  # sourcery skip: extract-method
    """Check the consistency of the MAD-X lattice for the (HL-)LHC.

    Args:
        mad (Madx): The MAD-X object used to build the sequence.

    Returns:
        None
    """
    assert mad.globals["qxb1"] == mad.globals["qxb2"]
    assert mad.globals["qyb1"] == mad.globals["qyb2"]
    assert mad.globals["qpxb1"] == mad.globals["qpxb2"]
    assert mad.globals["qpyb1"] == mad.globals["qpyb2"]

    assert np.isclose(mad.table.summ.q1, mad.globals["qxb1"], atol=1e-02)
    assert np.isclose(mad.table.summ.q2, mad.globals["qyb1"], atol=1e-02)

    try:
        assert np.isclose(mad.table.summ.dq1, mad.globals["qpxb1"], atol=1e-01)
        assert np.isclose(mad.table.summ.dq2, mad.globals["qpyb1"], atol=1e-01)

        df = mad.table.twiss.dframe()
        for my_ip in [1, 2, 5, 8]:
            assert np.isclose(df.loc[f"ip{my_ip}"].betx, mad.globals[f"betx_IP{my_ip}"], rtol=1e-02)
            assert np.isclose(df.loc[f"ip{my_ip}"].bety, mad.globals[f"bety_IP{my_ip}"], rtol=1e-02)

        assert df["x"].std() < 1e-6
        assert df["y"].std() < 1e-6
    except AssertionError:
        logging.warning("WARNING: Some sanity checks have failed during the madx lattice check")


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

    # Fix for hllhc16
    mad.input("""
    l.mbh = 0.001000;
    ACSCA, HARMON := HRF400;
    
    ACSCA.D5L4.B1, VOLT := VRF400/8, LAG := LAGRF400.B1, HARMON := HRF400;
    ACSCA.C5L4.B1, VOLT := VRF400/8, LAG := LAGRF400.B1, HARMON := HRF400;
    ACSCA.B5L4.B1, VOLT := VRF400/8, LAG := LAGRF400.B1, HARMON := HRF400;
    ACSCA.A5L4.B1, VOLT := VRF400/8, LAG := LAGRF400.B1, HARMON := HRF400;
    ACSCA.A5R4.B1, VOLT := VRF400/8, LAG := LAGRF400.B1, HARMON := HRF400;
    ACSCA.B5R4.B1, VOLT := VRF400/8, LAG := LAGRF400.B1, HARMON := HRF400;
    ACSCA.C5R4.B1, VOLT := VRF400/8, LAG := LAGRF400.B1, HARMON := HRF400;
    ACSCA.D5R4.B1, VOLT := VRF400/8, LAG := LAGRF400.B1, HARMON := HRF400;
    ACSCA.D5L4.B2, VOLT := VRF400/8, LAG := LAGRF400.B2, HARMON := HRF400;
    ACSCA.C5L4.B2, VOLT := VRF400/8, LAG := LAGRF400.B2, HARMON := HRF400;
    ACSCA.B5L4.B2, VOLT := VRF400/8, LAG := LAGRF400.B2, HARMON := HRF400;
    ACSCA.A5L4.B2, VOLT := VRF400/8, LAG := LAGRF400.B2, HARMON := HRF400;
    ACSCA.A5R4.B2, VOLT := VRF400/8, LAG := LAGRF400.B2, HARMON := HRF400;
    ACSCA.B5R4.B2, VOLT := VRF400/8, LAG := LAGRF400.B2, HARMON := HRF400;
    ACSCA.C5R4.B2, VOLT := VRF400/8, LAG := LAGRF400.B2, HARMON := HRF400;
    ACSCA.D5R4.B2, VOLT := VRF400/8, LAG := LAGRF400.B2, HARMON := HRF400;
    """)

    mad.input("""
      ! Slice nominal sequence
      exec, myslice;
      """)

    if mylhcbeam < 3:
        mad.input("""
      nrj=7000;
      beam,particle=proton,sequence=lhcb1,energy=nrj,npart=1.15E11,sige=4.5e-4;
      beam,particle=proton,sequence=lhcb2,energy=nrj,bv = -1,npart=1.15E11,sige=4.5e-4;
      """)

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


def apply_optics(mad: Madx, optics_file: str) -> None:
    """Apply the optics to the MAD-X model.

    Args:
        mad (Madx): The MAD-X object used to build the sequence.
        optics_file (str): The path to the optics file to apply.

    Returns:
        None
    """
    mad.call(optics_file)
    # A knob redefinition
    mad.input("on_alice := on_alice_normalized * 7000./nrj;")
    mad.input("on_lhcb := on_lhcb_normalized * 7000./nrj;")
