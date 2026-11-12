# Benchmark de latence — german-credit, modèle v17

1000 appels par backend, après 10 appels de chauffe · x86_64 · Python 3.12.15

| Backend | P50 (ms) | P95 (ms) | P99 (ms) |
|---|---|---|---|
| sklearn_pipeline | 4.653 | 7.619 | 11.871 |
| onnx_python | 0.077 | 0.118 | 0.231 |
| onnx_batch_100 | 0.347 | 0.652 | 1.000 |

Accélération ONNX vs scikit-learn (P50, 1 ligne) : x60.1

Environnement : 13th Gen Intel(R) Core(TM) i7-13620H, 16 CPU logiques ; Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39.
Lot : 100 lignes. La latence batch mesure le lot entier, sans division par le nombre de lignes.
Microbenchmark Python, hors HTTP ; chargement du modèle et construction des feeds exclus. Services du cours actifs et téléchargements Docker en arrière-plan ; aucune charge Locust exécutée.
