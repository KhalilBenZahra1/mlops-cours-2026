"""Garde-fous du job du guide, sans Loki/S3/CT réels et sans données DVC."""

import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def drift_job(monkeypatch):
    # Un poste peut déjà porter le token du webhook : aucun test ne doit l'utiliser.
    for key in ("CURRENT_PATH", "CT_WEBHOOK_URL", "CT_WEBHOOK_TOKEN", "REFERENCE_URI"):
        monkeypatch.delenv(key, raising=False)
    spec = importlib.util.spec_from_file_location(
        "drift_job_test", ROOT / "monitoring/evidently-job/calc_drift.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_drift_features_follow_contract(drift_job, contract, make_frame):
    frame = make_frame(contract, 10)
    result = drift_job.features_only(frame)
    assert list(result.columns) == contract.features
    assert contract.target not in result
    with pytest.raises(SystemExit, match="absentes"):
        drift_job.features_only(frame.drop(columns=[contract.features[0]]))


def test_drift_waits_for_enough_requests(drift_job, contract, make_frame, monkeypatch):
    frame = make_frame(contract, 10)
    monkeypatch.setattr(drift_job, "read_table", lambda _: frame)
    monkeypatch.setattr(drift_job, "fetch_from_loki", lambda: frame.iloc[:0])
    push, compute, save, trigger = Mock(), Mock(), Mock(), Mock()
    for name, mock in [
        ("push_metrics", push),
        ("compute_drift", compute),
        ("save_report", save),
        ("trigger_ct", trigger),
    ]:
        monkeypatch.setattr(drift_job, name, mock)
    assert drift_job.main() == 0
    push.assert_called_once_with(0, {}, set())
    compute.assert_not_called()
    save.assert_not_called()
    trigger.assert_not_called()


def test_drift_identical_population_has_all_feature_scores(drift_job, contract, make_frame):
    frame = drift_job.features_only(make_frame(contract, 500))
    scores, detected, snapshot = drift_job.compute_drift(frame, frame.copy())
    assert set(scores) == set(contract.features)
    assert all(value == pytest.approx(0, abs=1e-8) for value in scores.values())
    assert not detected
    assert "html" in snapshot.get_html_str(as_iframe=False).lower()


def test_drift_does_not_call_ct_when_url_unset(drift_job, contract, make_frame, monkeypatch):
    frame = make_frame(contract, 500)
    monkeypatch.setattr(drift_job, "read_table", lambda _: frame)
    monkeypatch.setattr(drift_job, "fetch_from_loki", lambda: frame)
    # Le calcul est simulé ici ; aucun trafic dérivé n'est envoyé à un service.
    scores = dict.fromkeys(contract.features, 1.0)
    snapshot = object()
    monkeypatch.setattr(drift_job, "compute_drift", lambda *_: (scores, set(scores), snapshot))
    push, save, trigger = Mock(), Mock(return_value="s3://test/report.html"), Mock()
    monkeypatch.setattr(drift_job, "push_metrics", push)
    monkeypatch.setattr(drift_job, "save_report", save)
    monkeypatch.setattr(drift_job, "trigger_ct", trigger)
    assert drift_job.CT_WEBHOOK_URL == ""
    assert drift_job.main() == 0
    trigger.assert_not_called()
    assert push.call_args.args[0] == len(frame)
    assert save.call_args.args[0] is snapshot
