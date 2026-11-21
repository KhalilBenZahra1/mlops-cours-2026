# Analyse du canary

- Date : 2026-11-21T16:39:35+00:00 · fenêtre `5m` · ISVC `scoring-integration` (namespace `scoring-integration`)
- Trafic canary : 10 %
- **Décision : CONTINUE** → `uv run python -m pipelines.gitops canary 50`

| Mesure | Stable | Canary |
|---|---|---|
| Révision | `scoring-integration-predictor-00001` | `scoring-integration-predictor-00002` |
| model_version | 19 | 19 |
| api_version | m7-integration-db3668ce7ab8-stable | m7-integration-db3668ce7ab8-candidate |
| threshold | 0.3182 | 0.3182 |
| requests | 3314 | 375 |
| predictions | 3314 | 372 |
| error_rate | 0.000 | 0.000 |
| p95_ms | 4.800 | 4.800 |
| positive_rate | 0.585 | 0.593 |
| mean_score | 0.420 | 0.416 |

| Garde-fou | Statut | Détail |
|---|---|---|
| observabilité | PASS | métriques du canary scrapées (up=1) |
| volume | PASS | stable 3314 / canary 375 requêtes /predict (minimum 100) |
| erreurs | PASS | 5xx canary 0.00% (stable 0.00%, max 1.00%) |
| latence | PASS | P95 canary 4.8 ms (stable 4.8 ms, max 30 ms) |
| scores | PASS | PSI des scores canary/stable 0.047 (max 0.25) |
| décisions | PASS | taux de décision positive canary 59.3% vs stable 58.5% (écart +0.9%, max ±10%) |

Requêtes PromQL :

- requests : `sum by (revision) (increase(http_requests_total{namespace="scoring-integration",isvc="scoring-integration",handler="/predict"}[5m]))`
- errors : `sum by (revision) (increase(http_requests_total{namespace="scoring-integration",isvc="scoring-integration",handler="/predict",code=~"5.."}[5m]))`
- predictions : `sum by (revision) (increase(ml_predictions_total{namespace="scoring-integration",isvc="scoring-integration"}[5m]))`
- positives : `sum by (revision) (increase(ml_predictions_total{namespace="scoring-integration",isvc="scoring-integration",outcome="1"}[5m]))`
- score_sum : `sum by (revision) (increase(ml_prediction_score_sum{namespace="scoring-integration",isvc="scoring-integration"}[5m]))`
- p95_seconds : `histogram_quantile(0.95, sum by (revision, le) (rate(ml_inference_latency_seconds_bucket{namespace="scoring-integration",isvc="scoring-integration"}[5m])))`
- score_buckets : `sum by (revision, le) (increase(ml_prediction_score_bucket{namespace="scoring-integration",isvc="scoring-integration"}[5m]))`
- model_info : `max by (revision, model_version, api_version, threshold) (ml_model_info{namespace="scoring-integration",isvc="scoring-integration"})`
- up : `max by (revision) (up{namespace="scoring-integration",isvc="scoring-integration"})`
