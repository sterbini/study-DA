# ==================================================================================================
# --- Imports
# ==================================================================================================
# Import standard library modules
import logging
from typing import Any

# Import third-party modules
import numpy as np
import xmask as xm
from cpymad.madx import Madx

# ==================================================================================================
# --- Functions specific to each (HL-)LHC version
# ==================================================================================================


def check_madx_lattices(mad: Madx) -> None:
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

    try:
        assert np.isclose(mad.table.summ.q1, mad.globals["qxb1"], atol=1e-02)
        assert np.isclose(mad.table.summ.q2, mad.globals["qyb1"], atol=1e-02)
        assert np.isclose(mad.table.summ.dq1, mad.globals["qpxb1"], atol=5e-01)
        assert np.isclose(mad.table.summ.dq2, mad.globals["qpyb1"], atol=5e-01)
    except AssertionError:
        logging.warning(
            "Warning: some of the Qx, Qy, DQx, DQy values are not close to the expected ones"
        )

    df = mad.table.twiss.dframe()
    for my_ip in [1, 2, 5, 8]:
        # assert np.isclose(df.loc[f"ip{my_ip}"].betx, mad.globals[f"betx_IP{my_ip}"], rtol=1e-02)
        # assert np.isclose(df.loc[f"ip{my_ip}"].bety, mad.globals[f"bety_IP{my_ip}"], rtol=1e-02)
        assert np.isclose(df.loc[f"ip{my_ip}"].betx, mad.globals[f"betxIP{my_ip}b1"], rtol=1e-02)
        assert np.isclose(df.loc[f"ip{my_ip}"].bety, mad.globals[f"betyIP{my_ip}b1"], rtol=1e-02)

    mad.twiss()
    df = mad.table.twiss.dframe()

    try:
        assert df["x"].std() < 1e-6
        assert df["y"].std() < 1e-6
    except AssertionError:
        logging.warning("Warning: the standard deviation of x and y are not close to zero")


def build_sequence(
    mad: Madx,
    mylhcbeam: int,
    beam_config: dict[str, Any],
    ignore_cycling: bool = False,
    slice_factor: int | None = 8,
    BFPP: bool = True,
) -> None:
    """Build the sequence for the (HL-)LHC, for a given beam.

    Args:
        mad (Madx): The MAD-X object used to build the sequence.
        mylhcbeam (int): The beam number (1, 2 or 4).
        beam_config (dict[str, Any]): The configuration of the beam from the configuration file.
        ignore_cycling (bool, optional): Whether to ignore cycling to have IP3 at position s=0.
            Defaults to False.
        slice_factor (int | None, optional): The slice factor if optic is not thin. Defaults to 8.
        BFPP (bool, optional): Whether to use the BFPP knob. Defaults to True.

    Returns:
        None
    """
    # Select beam
    mad.input(f"mylhcbeam = {mylhcbeam}")
    mad.input("option, -echo,warn, -info;")

    # optics dependent macros (for splitting)
    mad.call("acc-models-lhc/runII/2018/toolkit/macro.madx")

    assert mylhcbeam in {1, 2, 4}, "Invalid mylhcbeam (it should be in [1, 2, 4])"

    if mylhcbeam in {1, 2}:
        mad.call("acc-models-lhc/runII/2018/lhc_as-built.seq")
    else:
        mad.call("acc-models-lhc/runII/2018/lhcb4_as-built.seq")

    # New IR7 MQW layout and cabling
    mad.call("acc-models-lhc/runIII/RunIII_dev/IR7-Run3seqedit.madx")

    # Makethin part
    if slice_factor is not None and slice_factor > 0:
        # the variable in the macro is slice_factor
        mad.input(f"slicefactor={slice_factor};")
        mad.call("acc-models-lhc/runII/2018/toolkit/myslice.madx")
        if mylhcbeam == 1:
            xm.attach_beam_to_sequence(mad.sequence["lhcb1"], 1, beam_config["lhcb1"])
            xm.attach_beam_to_sequence(mad.sequence["lhcb2"], 2, beam_config["lhcb2"])
        elif mylhcbeam == 4:
            xm.attach_beam_to_sequence(mad.sequence["lhcb2"], 4, beam_config["lhcb2"])
        else:
            raise ValueError("Invalid mylhcbeam")
        # mad.beam()
        for my_sequence in ["lhcb1", "lhcb2"]:
            if my_sequence in list(mad.sequence):
                mad.input(
                    f"use, sequence={my_sequence}; makethin,"
                    f"sequence={my_sequence}, style=teapot, makedipedge=true;"
                )
    else:
        logging.warning("WARNING: The sequences are not thin!")

    # Cycling w.r.t. to IP3 (mandatory to find closed orbit in collision in the presence of errors)
    if not ignore_cycling:
        for my_sequence in ["lhcb1", "lhcb2"]:
            if my_sequence in list(mad.sequence):
                mad.input(
                    f"seqedit, sequence={my_sequence}; flatten;"
                    "cycle, start=IP3; flatten; endedit;"
                )

    # BFPP
    if mylhcbeam == 1 and BFPP:
        apply_BFPP(mad)


def apply_optics(mad: Madx, optics_file: str) -> None:
    """Apply the optics to the MAD-X model.

    Args:
        mad (Madx): The MAD-X object used to build the sequence.
        optics_file (str): The path to the optics file to apply.

    Returns:
        None
    """
    mad.call(optics_file)
    apply_ir7_strengths(mad)
    mad.input("on_alice := on_alice_normalized * 7000. / nrj;")
    mad.input("on_lhcb := on_lhcb_normalized * 7000. / nrj;")


def apply_ir7_strengths(mad: Madx) -> None:
    """Apply the IR7 strengths fix to the MAD-X model.

    Args:
        mad (Madx): The MAD-X object used to build the sequence.

    Returns:
        None
    """
    mad.input("""!***IR7 Optics***
            KQ4.LR7     :=    0.131382724100E-02 ;
            KQT4.L7     :=    0.331689344000E-03 ;
            KQT4.R7     :=    0.331689344000E-03 ;
            KQ5.LR7     :=   -0.133553657300E-02 ;
            KQT5.L7     :=    0.000000000000E+00 ;
            KQT5.R7     :=    0.000000000000E+00 ;

            !Beam1
            KQ6.L7B1    :=    0.332380383100E-02 ;
            KQ6.R7B1    :=   -0.281821059300E-02 ;
            KQTL7.L7B1  :=    0.307231360100E-03 ;
            KQTL7.R7B1  :=    0.411775382800E-02 ;
            KQTL8.L7B1  :=    0.535631538200E-03 ;
            KQTL8.R7B1  :=    0.180061251400E-02 ;
            KQTL9.L7B1  :=    0.104649831600E-03 ;
            KQTL9.R7B1  :=    0.316515736800E-02 ;
            KQTL10.L7B1 :=    0.469149843300E-02 ;
            KQTL10.R7B1 :=    0.234006504200E-03 ;
            KQTL11.L7B1 :=    0.109300381500E-02 ;
            KQTL11.R7B1 :=   -0.129517571700E-03 ;
            KQT12.L7B1  :=    0.203869506000E-02 ;
            KQT12.R7B1  :=    0.414855502900E-03 ;
            KQT13.L7B1  :=   -0.647047560500E-03 ;
            KQT13.R7B1  :=    0.163470209700E-03 ;

            !Beam2
            KQ6.L7B2    :=   -0.278052285800E-02 ;
            KQ6.R7B2    :=    0.330261896100E-02 ;
            KQTL7.L7B2  :=    0.391109869200E-02 ;
            KQTL7.R7B2  :=    0.307913213400E-03 ;
            KQTL8.L7B2  :=    0.141328062600E-02 ;
            KQTL8.R7B2  :=    0.139274871000E-02 ;
            KQTL9.L7B2  :=    0.363516060400E-02 ;
            KQTL9.R7B2  :=    0.692028108000E-04 ;
            KQTL10.L7B2 :=    0.156243369200E-03 ;
            KQTL10.R7B2 :=    0.451207010600E-02 ;
            KQTL11.L7B2 :=    0.360602594900E-03 ;
            KQTL11.R7B2 :=    0.131920025500E-02 ;
            KQT12.L7B2  :=   -0.705199531300E-03 ;
            KQT12.R7B2  :=   -0.138620184600E-02 ;
            KQT13.L7B2  :=   -0.606647736700E-03 ;
            KQT13.R7B2  :=   -0.585571959400E-03 ;""")


def apply_BFPP(mad: Madx) -> None:
    """Apply the BFPP knob to the MAD-X model.

    Args:
        mad (Madx): The MAD-X object used to build the sequence.

    Returns:
        None
    """
    mad.input("""acbch8.r2b1        :=   6.336517325e-05 * ON_BFPP.R2 / 7.8;
                acbch10.r2b1       :=   2.102863759e-05 * ON_BFPP.R2 / 7.8;
                acbh12.r2b1        :=   4.404997133e-05 * ON_BFPP.R2 / 7.8;

                acbch7.r1b1        :=   4.259479019e-06 * ON_BFPP.R1 / 2.5;
                acbch9.r1b1        :=   1.794045373e-05 * ON_BFPP.R1 / 2.5;
                acbh13.r1b1        :=   1.371178403e-05 * ON_BFPP.R1 / 2.5;

                acbch7.r5b1        :=   2.153161387e-06 * ON_BFPP.R5 / 1.3;
                acbch9.r5b1        :=   9.314782805e-06 * ON_BFPP.R5 / 1.3;
                acbh13.r5b1        :=   7.12996247e-06 * ON_BFPP.R5 / 1.3;

                acbch8.r8b1        :=   3.521812667e-05 * ON_BFPP.R8 / 4.6;
                acbch10.r8b1       :=   1.064966564e-05 * ON_BFPP.R8 / 4.6;
                acbh12.r8b1        :=   2.786990521e-05 * ON_BFPP.R8 / 4.6;
            """)
