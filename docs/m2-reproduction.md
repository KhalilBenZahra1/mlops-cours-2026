# Reproduire le Lab 2 dans Ubuntu WSL2

Le cluster `mlops-lab` existe déjà : ne pas le recréer. Les ports 8080 et 8081 appartiennent
aux autres applications ; KFP utilise 8082 et Airflow 8083.

```bash
cd /home/khalil/mlops-cours-2026
export PATH="$HOME/.local/bin:$PATH"
source .venv/bin/activate
set -a; source .env; set +a
export MLFLOW_ENABLE_PROXY_MULTIPART_DOWNLOAD=false
make pf
make kfp-ui
```

`make kfp-ui` réutilise un forward sain et ne lance plus de `pkill -f` large. Le Makefile
exporte `KFP_HOST=http://localhost:8082` pour le contrôle officiel, sans le modifier.
Les composants parlent à MLflow via son DNS interne ; les clients WSL utilisent le proxy
HTTP pour éviter les URL S3 présignées internes inaccessibles depuis le poste.

## Image et pipeline

L'image validée est `localhost:5001/scoring-pipeline:1.0.1`. La première image locale
1.0.0 avait échoué à l'import KFP faute de dépendances du SDK ; elle n'a pas été publiée.
Le Dockerfile installe maintenant KFP avec ses dépendances. Ne pas reconstruire un tag
publié après changement de code : choisir un nouveau tag dans components.py et dans le DAG,
construire/pousser cette image, puis recompiler.

```bash
python -m pipelines.scoring_pipeline
python - <<'PY'
import kfp
c = kfp.Client(host="http://localhost:8082")
r = c.create_run_from_pipeline_package(
    "scoring_pipeline.yaml", experiment_name="scoring", run_name="scoring-reproduction")
print(c.wait_for_run_completion(r.run_id, timeout=1800).state)
PY
```

L'image embarque src, le contrat, params et pipelines.stage ; les fonctions des composants
sont dans le YAML compilé. Une modification de composant demande recompilation/publication,
une modification embarquée demande aussi une nouvelle image.

## Airflow

```bash
make airflow
docker compose --project-directory infra/airflow exec -T airflow-scheduler airflow dags list-import-errors -o json
docker compose --project-directory infra/airflow exec -T airflow-scheduler airflow dags unpause scoring_dag
docker compose --project-directory infra/airflow exec -T airflow-scheduler airflow dags trigger scoring_dag
```

UI : http://localhost:8083. L'installateur conserve son fichier .env, crée une clé Fernet
locale si elle manque, et protège .env et kubeconfig en mode 600. Ces fichiers sont ignorés.
Les conteneurs rejoignent le réseau Docker kind ; les tâches reçoivent le secret S3 du
namespace airflow. Les fichiers intermédiaires utilisent un préfixe S3 par run ; seuls de
petits résumés XCom transitent dans Airflow.

Les probes de tests sont manuelles : tests/kfp_probes.py compile les DAGs KFP de corruption
et de branches parallèles ; dags/m2_probes.py fournit les équivalents Airflow. Les préfixes
S3 sont distincts. Ne pas confondre leurs échecs attendus avec ceux du scoring principal.
Les promotions concurrentes peuvent laisser champion et challenger sur deux versions
équivalentes ; sérialiser une promotion de production.

## Validation et preuves

```bash
make lint
make test
make check-m0
make check-m1
make check-m2
```

Résultats observés et identifiants : [vérifications](../reports/m2-verifications.md).
Analyse : [rapport](../reports/rapport-m2.md). Décision : [ADR-0001](adr/0001-reutiliser-image-pipeline.md).
Pour la capture authentique, garder le terminal Ubuntu sur les 19 contrôles réussis et le
message final, puis enregistrer le PNG dans `C:\Users\GIGABYTE\Desktop\cycle ITBS\3GL-A\MLOPS\Lab 2.png`.
Préserver Lab 0.png et Lab 1.png. Aucun rendu artificiel de journal ne remplace cette preuve.
