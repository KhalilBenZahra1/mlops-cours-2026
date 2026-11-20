"""Contrat de serving offline du modèle ONNX versionné au Lab 4."""

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def packaged_api(api_client):
    """Le vrai modèle Git, distinct du mini-modèle : hash et métadonnées inchangés."""
    with api_client(ROOT / "packaging/model/model.onnx", "1.0.0") as result:
        yield result


@pytest.fixture(scope="module")
def client(packaged_api):
    return packaged_api[0]


@pytest.fixture(scope="module")
def serve(packaged_api):
    return packaged_api[1]


@pytest.fixture(scope="module")
def rows(serve, contract, make_frame):
    path = ROOT / "data/processed/test.csv"
    # Le lot réel reste testé sur le poste ; la CI fabrique ses lignes en mémoire.
    data = pd.read_csv(path) if path.exists() else make_frame(contract, n=200)
    data = data[serve.cfg.features]
    return data.astype(object).where(data.notna(), None).to_dict("records")


@pytest.mark.parametrize("batch", [1, 3, None], ids=["unit", "batch", "all-test-rows"])
def test_predictions_follow_contract(client, rows, batch, serve):
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
def test_invalid_requests_are_rejected(client, rows, case, serve):
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


def test_null_values_are_imputed(client, serve):
    row = dict.fromkeys(serve.cfg.features)
    response = client.post("/predict", json={"instances": [row]})
    assert response.status_code == 200
    assert 0 <= response.json()["predictions"][0]["probability"] <= 1


def test_metadata_identifies_embedded_model(client, serve):
    metadata = json.loads((ROOT / "packaging/model/metadata.json").read_text())
    digest = hashlib.sha256((ROOT / "packaging/model/model.onnx").read_bytes()).hexdigest()
    out = client.get("/metadata").json()
    assert out["model"]["onnx_sha256"] == metadata["onnx_sha256"] == digest
    assert out["model"]["model_version"] == metadata["model_version"]
    assert out["threshold"] == metadata["threshold"]
    assert out["dataset"] == serve.cfg.name
    assert client.get("/health").json() == {"status": "ok", "model_loaded": True}


def test_docs_publish_dataset_schema(client, serve):
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()["components"]["schemas"]["Instance"]
    assert set(schema["required"]) == set(serve.cfg.features)
    assert schema["additionalProperties"] is False
