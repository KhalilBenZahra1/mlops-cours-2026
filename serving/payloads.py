"""Requêtes construites depuis dataset.yaml et les données de test."""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
from src.dataset_config import load_config  # noqa: E402

cfg = load_config(ROOT / "dataset.yaml")


def load_rows(csv: Path = ROOT / "data/processed/test.csv") -> list[dict]:
    df = pd.read_csv(csv)[cfg.features]
    return df.astype(object).where(df.notna(), None).to_dict("records")


def complete_rows(rows: list[dict]) -> list[dict]:
    return [r for r in rows if all(r[c] is not None for c in cfg.numeric)]


def v1_body(rows: list[dict]) -> dict:
    return {"instances": rows}


def v2_body(rows: list[dict]) -> dict:
    n = len(rows)
    inputs = [
        {"name": c, "shape": [n, 1], "datatype": "FP64", "data": [float(r[c]) for r in rows]}
        for c in cfg.numeric
    ]
    inputs += [
        {"name": c, "shape": [n, 1], "datatype": "BYTES", "data": [r[c] or "" for r in rows]}
        for c in cfg.categorical
    ]
    return {"inputs": inputs, "outputs": [{"name": "probabilities"}]}


def v2_positive_proba(response: dict) -> list[float]:
    out = next(o for o in response["outputs"] if o["name"] == "probabilities")
    return [float(p) for p in out["data"][1::2]]
