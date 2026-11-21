# Analyse du canary

- Date : 2026-11-21T18:57:53+00:00 · fenêtre `5m` · ISVC `scoring-model` (namespace `scoring`)
- Trafic canary : 50 %
- **Décision : PROMOTE** → `uv run python -m pipelines.gitops promote`

| Mesure | Stable | Canary |
|---|---|---|
| Révision | `scoring-model-predictor-00007` | `scoring-model-predictor-00008` |
| model_version | 19 | 19 |
| api_version | 2.1.15 | 2.1.16 |
| threshold | 0.3182 | 0.3182 |
| requests | 4304 | 1680 |
| predictions | 4304 | 1680 |
| error_rate | 0.000 | 0.000 |
| p95_ms | 4.800 | 4.800 |
| positive_rate | 0.587 | 0.570 |
| mean_score | 0.413 | 0.409 |

| Garde-fou | Statut | Détail |
|---|---|---|
| observabilité | PASS | métriques du canary scrapées (up=1) |
| volume | PASS | stable 4304 / canary 1680 requêtes /predict (minimum 100) |
| erreurs | PASS | 5xx canary 0.00% (stable 0.00%, max 1.00%) |
| latence | PASS | P95 canary 4.8 ms (stable 4.8 ms, max 30 ms) |
| scores | PASS | PSI des scores canary/stable 0.018 (max 0.25) |
| décisions | PASS | taux de décision positive canary 57.0% vs stable 58.7% (écart -1.7%, max ±10%) |

Requêtes PromQL :

- requests : `sum by (revision) (increase(http_requests_total{namespace="scoring",isvc="scoring-model",handler="/predict"}[5m]))`
- errors : `sum by (revision) (increase(http_requests_total{namespace="scoring",isvc="scoring-model",handler="/predict",code=~"5.."}[5m]))`
- predictions : `sum by (revision) (increase(ml_predictions_total{namespace="scoring",isvc="scoring-model"}[5m]))`
- positives : `sum by (revision) (increase(ml_predictions_total{namespace="scoring",isvc="scoring-model",outcome="1"}[5m]))`
- score_sum : `sum by (revision) (increase(ml_prediction_score_sum{namespace="scoring",isvc="scoring-model"}[5m]))`
- p95_seconds : `histogram_quantile(0.95, sum by (revision, le) (rate(ml_inference_latency_seconds_bucket{namespace="scoring",isvc="scoring-model"}[5m])))`
- score_buckets : `sum by (revision, le) (increase(ml_prediction_score_bucket{namespace="scoring",isvc="scoring-model"}[5m]))`
- model_info : `max by (revision, model_version, api_version, threshold) (ml_model_info{namespace="scoring",isvc="scoring-model"})`
- up : `max by (revision) (up{namespace="scoring",isvc="scoring-model"})`
