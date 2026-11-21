"""Les ressources de démonstration ne doivent pas viser la production GitOps."""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1] / "monitoring/integration"


def document(name):
    return yaml.safe_load((ROOT / name).read_text())


def test_integration_serving_isolated_and_same_model():
    base, candidate = document("inferenceservice.yaml"), document("candidate.yaml")
    for obj in (base, candidate):
        assert obj["metadata"]["namespace"] == "scoring-integration"
        assert obj["metadata"]["name"] != "scoring-model"
        image = obj["spec"]["predictor"]["containers"][0]["image"]
        assert image.startswith("localhost:5001/scoring-api:m7-integration-")
        variables = obj["spec"]["predictor"]["containers"][0]["env"]
        assert not any(e["name"] in {"MODEL_PATH", "DECISION_THRESHOLD"} for e in variables)
    assert (
        base["spec"]["predictor"]["containers"][0]["image"]
        == candidate["spec"]["predictor"]["containers"][0]["image"]
    )


def test_integration_monitor_has_no_production_namespace():
    monitor = document("podmonitor.yaml")
    assert monitor["metadata"]["name"] != "scoring-api"
    assert monitor["spec"]["namespaceSelector"]["matchNames"] == ["scoring-integration"]
    assert (
        monitor["spec"]["selector"]["matchLabels"]["serving.kserve.io/inferenceservice"]
        == "scoring-integration"
    )


def test_integration_drift_cannot_publish_production_metrics_or_trigger_ct():
    cron = document("evidently-cronjob.yaml")
    assert cron["metadata"]["name"] != "scoring-drift"
    assert cron["spec"]["suspend"] is True
    variables = cron["spec"]["jobTemplate"]["spec"]["template"]["spec"]["containers"][0]["env"]
    env = {v["name"]: v.get("value") for v in variables}
    assert env["MODEL_NAME"] == "scoring-model-integration"
    assert env["PUSH_JOB"] == "scoring-drift-integration"
    assert 'namespace="scoring-integration"' in env["LOKI_QUERY"]
    assert env["REPORTS_URI"].startswith("s3://monitoring/integration/")
    assert env["CT_WEBHOOK_URL"] == env["CT_WEBHOOK_TOKEN"] == ""


def test_integration_dashboard_and_rules_do_not_mix_environments():
    dashboard = json.loads((ROOT / "dashboards/scoring-integration.json").read_text())
    assert dashboard["uid"] != "scoring-overview"
    assert dashboard["templating"]["list"][0]["query"] == "scoring-integration"
    expressions = [t["expr"] for p in dashboard["panels"] for t in p.get("targets", [])]
    for expr in expressions:
        assert 'isvc="scoring-model"' not in expr
        assert 'model="scoring-model"' not in expr
        assert 'job="scoring-drift"' not in expr
    rules = document("alerts.yaml")
    assert rules["metadata"]["name"] != "scoring-alerts"
    for group in rules["spec"]["groups"]:
        for rule in group["rules"]:
            assert 'namespace="scoring"' not in rule["expr"]
            if "alert" in rule:
                assert rule["labels"]["team"] == "ml-integration"
                assert "ct_trigger" not in rule["labels"]


def test_external_notification_is_not_activated_by_integration_apply():
    resources = document("kustomization.yaml")["resources"]
    assert "alertmanager-test.yaml" not in resources
    notification = document("alertmanager-test.yaml")
    assert notification["spec"]["route"]["matchers"] == [
        {"name": "team", "value": "ml-integration", "matchType": "="}
    ]
    receivers = notification["spec"]["receivers"]
    assert all("slackConfigs" not in r for r in receivers)
    webhook = receivers[0]["webhookConfigs"][0]
    assert "url" not in webhook
    assert webhook["urlSecret"] == {"name": "integration-test-webhook", "key": "url"}
