import os
import shutil
from collections import OrderedDict
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import BioSimSpace.Sandpit.Exscientia as BSS

# Make sure AMBER is installed.
if BSS._amber_home is not None:
    exe = "%s/bin/sander" % BSS._amber_home
    if os.path.isfile(exe):
        has_amber = True
    else:
        has_amber = False
else:
    has_amber = False

# Store the tutorial URL.
url = BSS.tutorialUrl()


@pytest.fixture(scope="session")
def system():
    """Re-use the same molecuar system for each test."""
    return BSS.IO.readMolecules(["tests/input/ala.top", "tests/input/ala.crd"])


@pytest.mark.skipif(has_amber is False, reason="Requires AMBER to be installed.")
def test_minimise(system):
    """Test a minimisation protocol."""

    # Create a short minimisation protocol.
    protocol = BSS.Protocol.Minimisation(steps=100)

    # Run the process, check that it finished without error, and returns a system.
    run_process(system, protocol)


@pytest.mark.skipif(has_amber is False, reason="Requires AMBER to be installed.")
@pytest.mark.parametrize("restraint", ["backbone", "heavy", "all", "none"])
def test_equilibrate(system, restraint):
    """Test an equilibration protocol."""

    # Create a short equilibration protocol.
    protocol = BSS.Protocol.Equilibration(
        runtime=BSS.Types.Time(0.001, "nanoseconds"), restraint=restraint
    )

    # Run the process, check that it finished without error, and returns a system.
    run_process(system, protocol)


@pytest.mark.skipif(has_amber is False, reason="Requires AMBER to be installed.")
def test_heat(system):
    """Test a heating protocol."""

    # Create a short heating protocol.
    protocol = BSS.Protocol.Equilibration(
        runtime=BSS.Types.Time(0.001, "nanoseconds"),
        temperature_start=BSS.Types.Temperature(0, "kelvin"),
        temperature_end=BSS.Types.Temperature(300, "kelvin"),
    )

    # Run the process, check that it finished without error, and returns a system.
    run_process(system, protocol)


@pytest.mark.skipif(has_amber is False, reason="Requires AMBER to be installed.")
def test_cool(system):
    """Test a cooling protocol."""

    # Create a short heating protocol.
    protocol = BSS.Protocol.Equilibration(
        runtime=BSS.Types.Time(0.001, "nanoseconds"),
        temperature_start=BSS.Types.Temperature(300, "kelvin"),
        temperature_end=BSS.Types.Temperature(0, "kelvin"),
    )

    # Run the process, check that it finished without error, and returns a system.
    run_process(system, protocol)


@pytest.mark.skipif(has_amber is False, reason="Requires AMBER to be installed.")
def test_production(system):
    """Test a production protocol."""

    # Create a short production protocol.
    protocol = BSS.Protocol.Production(runtime=BSS.Types.Time(0.001, "nanoseconds"))

    # Run the process, check that it finished without error, and returns a system.
    run_process(system, protocol, check_data=True)


@pytest.mark.skipif(has_amber is False, reason="Requires AMBER to be installed.")
def test_args(system):
    """Test setting an manipulation of command-line args."""

    # Create a default minimisation protocol. This doesn't matter since
    # we're going to clear the default arguments anyway.
    protocol = BSS.Protocol.Minimisation()

    # Create the process object.
    process = BSS.Process.Amber(system, protocol, name="test")

    # Clear the existing arguments.
    process.clearArgs()

    # Now add some arguments. Firstly one-by-one, using a mixture of
    # arguments and flags.
    process.setArg("-a", "A")  # Regular argument.
    process.setArg("-b", "B")  # Regular argument.
    process.setArg("-c", True)  # Boolean flag.
    process.setArg("-d", "D")  # Regular argument.
    process.setArg("-e", True)  # Boolean flag.
    process.setArg("-f", 6)  # Argument value is an integer.

    # Get the arguments and the string representation.
    args = process.getArgs()
    arg_string = process.getArgString()
    arg_string_list = process.getArgStringList()

    # Make sure there is the correct number of arguments.
    assert len(args) == 6

    # Make sure the string is correct.
    assert len(arg_string_list) == 10
    assert arg_string == "-a A -b B -c -d D -e -f 6"

    # Turn off one of the flags.
    process.setArg("-c", False)

    # Get the updated arguments and the string representation.
    args = process.getArgs()
    arg_string = process.getArgString()
    arg_string_list = process.getArgStringList()

    # Make sure there is the same number of arguments.
    assert len(args) == 6

    # Make sure the new string is correct. (The "False" flag should be missing.)
    assert len(arg_string_list) == 9
    assert arg_string == "-a A -b B -d D -e -f 6"

    # Create a new dictionary of extra arguments. This could be a regular
    # dictionary, but we use an OrderedDict for testing purposes.
    extra_args = OrderedDict()

    # Populate the arguments.
    extra_args["-g"] = True
    extra_args["-h"] = "H"
    extra_args["-i"] = False
    extra_args["-k"] = "K"

    # Add the arguments.
    process.addArgs(extra_args)

    # Get the updated arguments and the string representation.
    args = process.getArgs()
    arg_string = process.getArgString()
    arg_string_list = process.getArgStringList()

    # Make sure there is the correct number of arguments.
    assert len(args) == 10

    # Make sure the new string is correct.
    assert len(arg_string_list) == 14
    assert arg_string == "-a A -b B -d D -e -f 6 -g -h H -k K"

    # Now we'll delete an argument.
    process.deleteArg("-d")

    # Get the updated arguments and the string representation.
    args = process.getArgs()
    arg_string = process.getArgString()
    arg_string_list = process.getArgStringList()

    # Make sure there is the correct number of arguments.
    assert len(args) == 9

    # Make sure the new string is correct.
    assert len(arg_string_list) == 12
    assert arg_string == "-a A -b B -e -f 6 -g -h H -k K"

    # Now test insertion of additional arguments.
    process.insertArg("-x", "X", 0)  # Insert at beginning.
    process.insertArg("-y", True, 4)  # Insert at middle.
    process.insertArg("-z", "Z", 11)  # Insert at end.

    # Get the updated arguments and the string representation.
    args = process.getArgs()
    arg_string = process.getArgString()
    arg_string_list = process.getArgStringList()

    # Make sure there is the correct number of arguments.
    assert len(args) == 12

    # Make sure the new string is correct.
    assert len(arg_string_list) == 17
    assert arg_string == "-x X -a A -b B -y -e -f 6 -g -h H -k K -z Z"


def run_process(system, protocol, check_data=False):
    """Helper function to run various simulation protocols."""

    # Initialise the AMBER process.
    process = BSS.Process.Amber(system, protocol, name="test")

    # Start the AMBER simulation.
    process.start()

    # Wait for the process to end.
    process.wait()

    # Make sure the process didn't error.
    assert not process.isError()

    # Make sure that we get a molecular system back.
    assert process.getSystem() is not None

    # Make sure the correct amount of data is generated.
    if check_data:
        # Get the config from the process.
        config = process.getConfig()

        # Parse the config to get the report frequency and total number of steps.
        freq = None
        nsteps = None
        for line in config:
            if "ntpr" in line:
                freq = int(line.split("=")[1].split(",")[0])
            elif "nstlim" in line:
                nsteps = int(line.split("=")[1].split(",")[0])

        if freq and nsteps:
            # Work out the number of records. (Add one since the zero step is recorded.)
            nrec = int(nsteps / freq) + 1

            # Get the record data.
            data = process.getRecords()

            for k, v in data.items():
                assert len(v) == nrec


@pytest.mark.skip(
    "Wait for the fix of https://github.com/OpenBioSim/biosimspace/issues/78."
)
@pytest.mark.parametrize(
    "protocol",
    [
        BSS.Protocol.FreeEnergy(temperature=298 * BSS.Units.Temperature.kelvin),
        BSS.Protocol.FreeEnergyMinimisation(),
    ],
)
def test_parse_fep_output(system, protocol):
    """Make sure that we can correctly parse AMBER FEP output."""

    # Copy the system.
    system_copy = system.copy()

    # Decouple a single molecule in the system.
    mol = system_copy[0]
    mol = BSS.Align.decouple(mol)
    system_copy.updateMolecule(0, mol)

    # Create a process using any system and the protocol.
    process = BSS.Process.Amber(system_copy, protocol)

    # Copy the existing output file into the working directory.
    shutil.copyfile(
        "tests/Sandpit/Exscientia/output/amber_fep.out",
        process.workDir() + "/amber.out",
    )

    # Update the stdout record dictionaries.
    process.stdout(0)

    # Get back the records for each degree of freedom.
    records0 = process.getRecords(dof=0)
    records1 = process.getRecords(dof=1)
    records2 = process.getRecords(dof=2)

    # Make sure NSTEP is present.
    assert "NSTEP" in records0

    # Get the number of records.
    num_records = len(records0["NSTEP"])

    # Now make sure that the records for the two TI regions contain the
    # same number of values.
    for v0, v1 in zip(records0.values(), records1.values()):
        assert len(v0) == len(v1) == num_records

    # Now check that are records for the softcore region contain the correct
    # number of values.
    for v in records2.values():
        assert len(v) == num_records


class TestsaveMetric:
    @staticmethod
    @pytest.fixture()
    def setup(system):
        # Copy the system.
        system_copy = system.copy()

        # Decouple a single molecule in the system.
        mol = system_copy[0]
        mol = BSS.Align.decouple(mol)
        system_copy.updateMolecule(0, mol)

        # Create a process using any system and the protocol.
        process = BSS.Process.Amber(
            system_copy,
            BSS.Protocol.FreeEnergy(temperature=298 * BSS.Units.Temperature.kelvin),
        )
        shutil.copyfile(
            "tests/Sandpit/Exscientia/output/amber_fep.out",
            process.workDir() + "/amber.out",
        )
        process.saveMetric()
        return process

    def test_metric_parquet_exist(self, setup):
        assert Path(f"{setup.workDir()}/metric.parquet").exists()

    def test_metric_parquet(self, setup):
        df = pd.read_parquet(f"{setup.workDir()}/metric.parquet")
        assert np.isclose(df["PotentialEnergy (kJ/mol)"][20.0], -90086.461304)
        assert np.isclose(df["Volume (nm^3)"][20.0], 65.7242169)
        assert np.isclose(df["Pressure (bar)"][20.0], 0.0)
        assert np.isclose(df["Temperature (kelvin)"][20.0], 303.01)

    def test_u_nk_parquet_exist(self, setup):
        assert Path(f"{setup.workDir()}/u_nk.parquet").exists()

    def test_u_nk_parquet(self, setup):
        df = pd.read_parquet(f"{setup.workDir()}/u_nk.parquet")
        assert df.shape == (50, 16)
