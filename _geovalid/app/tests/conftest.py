"""Shared fixtures: the synthetic database with injected errors and its clean twin, each validated once per session."""
import glob
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from geovalid_pro import synth  # noqa: E402
from geovalid_pro.engine import ProjectSpec, load_inputs, run  # noqa: E402


def _run(folder):
    ins = [i for i in load_inputs(sorted(glob.glob(f"{folder}/*.csv"))) if i.kind != "ignore"]
    return run(ProjectSpec(ins, dem_path=f"{folder}/dem.asc", licence_path=f"{folder}/licence.csv",
                           crm_path=f"{folder}/crm_standards.csv", project_name="test"))


@pytest.fixture(scope="session")
def injected(tmp_path_factory):
    d = tmp_path_factory.mktemp("err")
    synth.generate(str(d), inject=True)
    return d, _run(str(d))


@pytest.fixture(scope="session")
def clean(tmp_path_factory):
    d = tmp_path_factory.mktemp("clean")
    synth.generate(str(d), inject=False)
    return d, _run(str(d))
