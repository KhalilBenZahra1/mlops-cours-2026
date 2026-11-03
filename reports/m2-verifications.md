# Vérifications réelles du Lab 2 — 2026-10-27

Les références ci-dessous proviennent des API KFP, Airflow et MLflow ; aucun résultat n’est simulé.

## Runs principaux

| Outil | Identifiant | État | Durée API | Run MLflow |
|---|---|---|---|---|
| KFP | [9e4ffc0e-b379-43b6-8006-627542aa1506](http://localhost:8082/#/runs/details/9e4ffc0e-b379-43b6-8006-627542aa1506) | SUCCEEDED | 307 s | `d4429d72da4544fe8a8639ae9936f786` |
| KFP | [ce8d3878-314f-44c6-8f73-b95cb44d7c89](http://localhost:8082/#/runs/details/ce8d3878-314f-44c6-8f73-b95cb44d7c89) | SUCCEEDED | 136 s | `af49550943ae40b18e7b34c182da8cd8` |
| Airflow | `lab2-airflow-20261027-1` | success | 64.6 s | `72f448b1d90b413d8653a0eeabf3420d` |
| Airflow | `lab2-airflow-20261027-2` | success | 52.7 s | `71e4a964cdf745ee813f5a1c0e54fac1` |

Les six tâches de chacun de ces quatre runs sont réussies. Le DAG `scoring_dag` est activé ; son interface est sur http://localhost:8083.

## Artefacts, métriques et registre

- Dataset : 1 000 lignes, MD5 `24b8e38b9c8688d495afc8eb5cb40127`, identique au verrou DVC.
- Validation : six contrôles réussis ; préparation : 800 lignes train, 200 test.
- ROC AUC : 0,8094 ; seuil de décision : 0,3182 ; coût métier : 108 ; matrice : `[[67,73],[7,53]]`.
- Les logs du lanceur KFP contiennent les métadonnées Metrics et ClassificationMetrics ; le rapport est transporté comme Artifact.
- Les runs KFP portent `launched_by=kfp` et leur vrai `kfp_run_id`. Les logs XCom Airflow relient le DAG au run MLflow et aux métriques.
- Versions historiques 1 à 4 conservées ; version 5 : test local ; versions 6–7 : runs KFP principaux ; 8–9 : branches KFP ; 10–11 : runs Airflow principaux ; 12–13 : branches Airflow.
- Alias observés après l’essai parallèle : `champion=12`, `challenger=13`. Les deux modèles atteignent le seuil de promotion. Les écritures d’alias concurrentes expliquent la différence ; aucun alias n’a été réécrit pour la masquer.

## Robustesse et comparaison

- Le second run KFP produit `cached-decision=true` pour ingest, validate et prepare. Train reste réexécuté, puis evaluate et register.
- Contrôle KFP `985a0b0c-2814-4fbf-88d6-ff316cef58e7` : échec attendu de validation d’une colonne retirée ; aucune exécution de prepare.
- Contrôle parallèle KFP `34815fee-afb1-4241-818d-6709bf5b229e` : succès, deux tâches train démarrées à 14:11:31 UTC ; le second nœud a attendu ses images.
- Airflow `lab2-m2_debug_probe` : échec attendu sur fichier absent ; préparation `upstream_failed`.
- Airflow `lab2-m2_parallel_probe` : douze tâches réussies ; train_a et train_b se chevauchent de 14:23:02 à 14:23:15 UTC, avec préfixes S3 distincts.
- Les DAGs de contrôle restent manuels, sans schedule. Leurs échecs attendus restent visibles dans l’historique.
- Mise à jour KFP : compilation et publication d’une définition en 0,87 s, version `7c20a5fa-7ef4-459a-a932-78b0f5cad127`. Nouveau DAG Airflow observé en moins de 54,3 s ; cette valeur est une borne supérieure de scrutation.
- Mémoire : somme CRI working-set des 14 conteneurs du namespace kubeflow, environ 1,04 Gio ; somme Docker stats des sept services Airflow, environ 2,08 Gio. Instantanés, hors pics et pods de tâches.

## Contrôles finaux

- `make lint` : réussi ; `make test` : 15 tests réussis.
- `make check-m0` : 19/19 ; `make check-m1` : 18/18 ; `make check-m2` : 19/19.
- Les trois scripts officiels check.sh sont identiques au commit de base `6624b9b`. Les sources métier, dataset.yaml, params.yaml, dvc.yaml, dvc.lock et uv.lock sont inchangés.
- Les trois nœuds restent Ready ; les applications de gestion des retours tournent toujours sur leurs ports 8080/8081.
- Aucun commit ou push supplémentaire n’a été effectué après la consigne utilisateur. La PR Draft existante est laissée intacte.

## Capture du terminal

La validation a également été relancée réellement via Ubuntu avec sortie journalisée. La création du PNG exige une fenêtre interactive accessible à la capture ; l’état de cette livraison est indiqué dans le bilan final. Aucun log n’a été transformé en fausse image de terminal.
