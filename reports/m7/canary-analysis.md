# Analyse du canary

- Date : 2026-11-21T19:03:31+00:00 · fenêtre `5m` · ISVC `scoring-model` (namespace `scoring`)
- Trafic canary : 10 %
- **Décision : ROLLBACK** → `uv run python -m pipelines.gitops rollback`

| Mesure | Stable | Canary |
|---|---|---|
| Révision | `scoring-model-predictor-00008` | `scoring-model-predictor-00009` |
| model_version | 19 | — |
| api_version | 2.1.16 | — |
| threshold | 0.3182 | — |
| requests | 5703 | 0 |
| predictions | 5703 | 0 |
| error_rate | 0.000 | 0.000 |
| p95_ms | 4.800 | — |
| positive_rate | 0.591 | — |
| mean_score | 0.412 | — |

| Garde-fou | Statut | Détail |
|---|---|---|
| observabilité | FAIL | canary non scrapé (up=0) : /metrics absent ou en erreur |
| volume | WAIT | stable 5703 / canary 0 requêtes /predict (minimum 100) |
| erreurs | WAIT | 5xx canary 0.00% (stable 0.00%, max 1.00%) |
| latence | WAIT | P95 indisponible (pas de trafic sur une révision ?) |
| scores | WAIT | histogramme des scores indisponible |
| décisions | WAIT | aucune décision sur une des révisions |

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
