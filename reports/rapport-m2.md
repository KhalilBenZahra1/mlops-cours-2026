# Rapport comparatif — Kubeflow Pipelines et Airflow

## 1. Contexte

Le Lab 2 reprend le scoring German Credit du Lab 1 : 1 000 demandes, 20 variables,
une séparation stratifiée de 800/200 lignes et six étapes, ingest, validate, prepare,
train, evaluate, register. Le contrat reste `dataset.yaml`. Les deux orchestrateurs
exécutent les mêmes modules métier dans `localhost:5001/scoring-pipeline:1.0.1`, sur
le cluster kind existant. MLflow conserve expériences, modèles et historique. Le poste
utilise Ubuntu 24.04 sous WSL2, 16 processeurs logiques et environ 11,5 Gio de RAM.

## 2. Résultats quantitatifs

Mesures du 27 octobre 2026 ; durées calculées depuis les horodatages des orchestrateurs.

| Mesure | KFP | Airflow |
|---|---|---|
| Premier run complet | 307 s | 64,6 s |
| Relance identique | 136 s | 52,7 s |
| Étapes servies depuis le cache | 3 sur 6 | 0 sur 6 |
| Code propre à l'orchestrateur, hors tests | 282 lignes | 75 lignes |
| Mémoire instantanée des services, hors tâches | 1,04 Gio | 2,08 Gio |
| Mise à jour de définition | compilation/upload : 0,87 s | nouveau DAG visible en ≤ 54,3 s |
| Image commune, champ Docker `.Size` | 245,5 Mio | 245,5 Mio |

Le test KFP local des six étapes dure 41,1 s. Le pont Airflow local a réussi ingest
et validate, sans chronométrage dédié. L'installation initiale KFP, terminée manuellement,
n'est pas chronométrée ; la reprise Airflow avec images préchargées prend 96 s et ne
représente pas une installation de zéro.

## 3. Analyse qualitative

KFP demande davantage de préparation : composants typés, compilation et publication.
En contrepartie, l'exécution publie Dataset, Model, Metrics et ClassificationMetrics,
avec leurs métadonnées et leur filiation. Les logs du lanceur confirment la matrice
de confusion `[[67,73],[7,53]]` et une ROC AUC de 0,8094. Airflow fournit un DAG plus
court, mais le transport des fichiers exige notre pont S3 ; seuls l'identifiant MLflow
et les petites métriques passent par XCom. Chaque run possède un préfixe isolé.

Le second run KFP confirme trois décisions de cache positives pour les étapes data.
L'entraînement reste exécuté, avec un nouveau run MLflow et une version enregistrée.
Airflow rejoue ses six tâches. Les horodatages confirment le chevauchement de deux branches dans chaque outil,
sans constituer une mesure de passage à l'échelle.

Le debugging repose sur les états et les logs. Un fichier corrompu fait échouer la
validation KFP avant préparation ; dans un préfixe Airflow vide, la validation échoue
et la préparation devient `upstream_failed`. Les traces identifient la cause. Les secrets
S3 Airflow proviennent de Kubernetes ; KFP joint le proxy MLflow sans identifiants S3.

## 4. Recommandations

Je retiendrais KFP pour une chaîne ML nécessitant artefacts typés, filiation et réutilisation
des calculs data. Airflow convient à l'intégration de traitements hétérogènes et de tâches
planifiées, à condition de maintenir explicitement le transport S3 et la traçabilité MLflow.
Un changement embarqué impose un nouveau tag. L'essai parallèle a laissé
`champion=12` et `challenger=13`, de même qualité : en production, la promotion doit
être sérialisée.

## 5. Limites de la comparaison

Deux runs principaux par outil, un petit dataset et une seule machine ne permettent aucune
généralisation. Le premier run KFP inclut des téléchargements de lanceurs ; l'image Airflow
était préchargée. Les mémoires sont des instantanés, pas des pics. Aucun cluster cloud, autoscaling ou KubernetesExecutor
Airflow n'a été évalué ; Airflow utilise ici CeleryExecutor avec KubernetesPodOperator.
