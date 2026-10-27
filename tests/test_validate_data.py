"""The data gate rejects corrupt input without changing the project's dataset."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from src.dataset_config import load_config
from src.validate_data import run_checks

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def sample():
    cfg = load_config(ROOT / "dataset.yaml")
    row = {c: 1.0 for c in cfg.numeric} | {c: "category" for c in cfg.categorical}
    row |= {c: "group" for c in cfg.extra_sensitive}
    df = pd.DataFrame([row, row])
    df[cfg.target] = [cfg.positive_class, "other"]
    return cfg, df


def test_valid_contract_is_accepted(sample):
    cfg, df = sample
    assert all(run_checks(cfg, df).values())


@pytest.mark.parametrize("corruption", ["missing", "empty", "target", "numeric"])
def test_corrupt_contract_is_rejected(sample, corruption):
    cfg, df = sample
    if corruption == "missing":
        df = df.drop(columns=[cfg.features[0]])
    elif corruption == "empty":
        df = df.iloc[:0]
    elif corruption == "target":
        df.loc[0, cfg.target] = None
    else:
        df[cfg.numeric[0]] = "not a number"
    assert not all(run_checks(cfg, df).values())


def test_cli_failure_writes_report_and_nonzero_exit(sample, tmp_path):
    cfg, df = sample
    bad = tmp_path / "bad.csv"
    df.drop(columns=[cfg.features[0]]).to_csv(bad, index=False)
    env = {**os.environ, "PYTHONPATH": str(ROOT), "DATASET_CONFIG": str(ROOT / "dataset.yaml")}
    result = subprocess.run(
        [sys.executable, "-m", "src.validate_data", str(bad)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    report = json.loads((tmp_path / "reports/validation.json").read_text())
    assert report["success"] is False
    assert report["n_failed"] > 0
