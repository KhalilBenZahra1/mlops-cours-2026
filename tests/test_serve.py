# Fichier : tests/test_serve.py
"""Tests de l'API de scoring (packaging/app/serve.py), avec le mini-modèle de conftest.py."""

import json
from pathlib import Path

import onnxruntime as ort
import pytest

from pipelines.gitops import payload

ROOT = Path(__file__).resolve().parents[1]


def test_health(api):
    r = api.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "model_loaded": True}


def test_metadata_et_version(api, contract):
    meta = api.get("/metadata").json()
    assert meta["api_version"] == "9.9.9"  # APP_VERSION, posée au build de l'image
    assert meta["threshold"] == 0.4  # seuil lu dans metadata.json
    assert meta["features"] == {"numeric": contract.numeric, "categorical": contract.categorical}
    assert api.get("/version").json() == {"version": "9.9.9", "model_version": "test"}


def test_predict_coherent_avec_le_seuil(api, contract):
    r = api.post("/predict", json=payload(n=3))
    assert r.status_code == 200
    body = r.json()
    assert body["positive_class"] == str(contract.positive_class)
    assert len(body["predictions"]) == 3
    for p in body["predictions"]:
        assert 0.0 <= p["probability"] <= 1.0
        assert p["prediction"] == int(p["probability"] >= body["threshold"])


def test_valeur_manquante_acceptee(api, contract):
    row = payload()["instances"][0] | {contract.features[0]: None}
    assert api.post("/predict", json={"instances": [row]}).status_code == 200


def _invalid_bodies():
    """Requêtes invalides : une colonne manquante, un mauvais type, une colonne en trop…"""
    row = payload()["instances"][0]
    first = next(iter(row))
    return {
        "colonne manquante": {"instances": [{k: v for k, v in row.items() if k != first}]},
        "nombre en texte": {"instances": [row | {first: "12"}]},
        "colonne inconnue": {"instances": [row | {"colonne_inconnue": 1}]},
        "liste vide": {"instances": []},
        "objet nu": row,
    }


@pytest.mark.parametrize("case", list(_invalid_bodies()))
def test_requete_invalide_refusee(api, case):
    assert api.post("/predict", json=_invalid_bodies()[case]).status_code == 422


def test_modele_versionne_conforme_au_contrat(contract):
    """Le modèle de packaging/model/ (celui que la CI met dans l'image) suit dataset.yaml."""
    folder = ROOT / "packaging" / "model"
    if not (folder / "model.onnx").exists():
        pytest.skip("packaging/model/ absent : modèle exporté au Lab 4 (export_onnx.py)")
    meta = json.loads((folder / "metadata.json").read_text())
    assert meta["features"] == {"numeric": contract.numeric, "categorical": contract.categorical}
    assert meta["positive_class"] == str(contract.positive_class)
    assert 0.0 < meta["threshold"] < 1.0
    session = ort.InferenceSession(str(folder / "model.onnx"), providers=["CPUExecutionProvider"])
    assert sorted(i.name for i in session.get_inputs()) == sorted(contract.features)
    assert "probabilities" in [o.name for o in session.get_outputs()]


def test_mini_modele_et_modele_versionne_isoles(api, api_client):
    """Les deux clients peuvent coexister sans échanger modèle, seuil ou métadonnées."""
    import hashlib
    import importlib

    mini_module = importlib.import_module("app.serve")
    folder = ROOT / "packaging/model"
    metadata = json.loads((folder / "metadata.json").read_text())
    with api_client(folder / "model.onnx", "integration-test") as (real, real_module):
        assert real_module is not mini_module
        actual = real.get("/metadata").json()
        digest = hashlib.sha256((folder / "model.onnx").read_bytes()).hexdigest()
        assert actual["model"]["onnx_sha256"] == metadata["onnx_sha256"] == digest
        assert actual["model"]["model_version"] == metadata["model_version"]
        assert actual["threshold"] == metadata["threshold"]
        assert api.get("/version").json()["model_version"] == "test"
        assert api.get("/metadata").json()["threshold"] == 0.4
    assert importlib.import_module("app.serve") is mini_module
