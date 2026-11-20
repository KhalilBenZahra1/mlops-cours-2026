"""The data gate rejects corrupt input without changing the project's dataset."""

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.dataset_config import load_config
from src.validate_data import run_checks

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def sample(make_frame):
    cfg = load_config(ROOT / "dataset.yaml")
    path = ROOT / "data/processed/train.csv"
    if path.exists():
        return cfg, pd.read_csv(path)
    # CI sans DVC : fabriquer un lot conforme aux domaines GX déjà versionnés.
    # La suite reste figée : aucune expectation ni référence n'est régénérée.
    df = make_frame(cfg)
    suite = json.loads((ROOT / "gx/expectations/scoring_contract.json").read_text())
    expectations = suite["expectations"]
    for expectation in expectations:
        kwargs = expectation["kwargs"]
        column = kwargs.get("column")
        if expectation["type"] == "expect_column_values_to_be_between":
            df[column] = np.linspace(kwargs["min_value"], kwargs["max_value"], len(df))
        elif expectation["type"] == "expect_column_values_to_be_in_set" and (
            column != cfg.target or "mostly" not in kwargs
        ):
            values = kwargs["value_set"]
            df[column] = [values[i % len(values)] for i in range(len(df))]
    positive = next(
        e["kwargs"]
        for e in expectations
        if e["type"] == "expect_column_values_to_be_in_set"
        and e["kwargs"].get("column") == cfg.target
        and e["kwargs"].get("value_set") == [cfg.positive_class]
    )
    rate = 2 * positive["mostly"]  # génération de la suite : borne = taux de référence / 2
    others = df.loc[df[cfg.target] != cfg.positive_class, cfg.target].unique()
    count = round(rate * len(df))
    df[cfg.target] = [cfg.positive_class] * count + [others[0]] * (len(df) - count)
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
