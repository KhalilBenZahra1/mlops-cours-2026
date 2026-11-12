"""Contrat de serving offline du modèle ONNX versionné au Lab 4."""

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest
from app import serve
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def client():
    with TestClient(serve.app) as api:
        yield api


@pytest.fixture(scope="module")
def rows():
    data = pd.read_csv(ROOT / "data/processed/test.csv")[serve.cfg.features]
    return data.astype(object).where(data.notna(), None).to_dict("records")


@pytest.mark.parametrize("batch", [1, 3, None], ids=["unit", "batch", "all-test-rows"])
def test_predictions_follow_contract(client, rows, batch):
    instances = rows if batch is None else rows[:batch]
    response = client.post("/predict", json={"instances": instances})
    assert response.status_code == 200
    out = response.json()
    assert len(out["predictions"]) == len(instances)
    assert out["model_version"] == serve.metadata["model_version"]
    assert out["positive_class"] == str(serve.cfg.positive_class)
    for prediction in out["predictions"]:
        assert 0 <= prediction["probability"] <= 1
        assert prediction["prediction"] == int(prediction["probability"] >= out["threshold"])


@pytest.mark.parametrize(
    "case", ["missing", "extra", "numeric", "categorical", "empty", "oversized", "batch-type"]
)
def test_invalid_requests_are_rejected(client, rows, case):
    row = rows[0].copy()
    instances = [row]
    if case == "missing":
        row.pop(serve.cfg.features[0])
    elif case == "extra":
        row["__unexpected_feature__"] = 1
    elif case == "numeric":
        row[serve.cfg.numeric[0]] = "invalid"
    elif case == "categorical":
        row[serve.cfg.categorical[0]] = 123
    elif case == "empty":
        instances = []
    elif case == "oversized":
        instances = [row] * (serve.MAX_BATCH + 1)
    else:
        instances = "invalid"
    assert client.post("/predict", json={"instances": instances}).status_code == 422


def test_null_values_are_imputed(client):
    row = dict.fromkeys(serve.cfg.features)
    response = client.post("/predict", json={"instances": [row]})
    assert response.status_code == 200
    assert 0 <= response.json()["predictions"][0]["probability"] <= 1


def test_metadata_identifies_embedded_model(client):
    metadata = json.loads((ROOT / "packaging/model/metadata.json").read_text())
    digest = hashlib.sha256((ROOT / "packaging/model/model.onnx").read_bytes()).hexdigest()
    out = client.get("/metadata").json()
    assert out["model"]["onnx_sha256"] == metadata["onnx_sha256"] == digest
    assert out["model"]["model_version"] == metadata["model_version"]
    assert out["threshold"] == metadata["threshold"]
    assert out["dataset"] == serve.cfg.name
    assert client.get("/health").json() == {"status": "ok", "model_loaded": True}


def test_docs_publish_dataset_schema(client):
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()["components"]["schemas"]["Instance"]
    assert set(schema["required"]) == set(serve.cfg.features)
    assert schema["additionalProperties"] is False
