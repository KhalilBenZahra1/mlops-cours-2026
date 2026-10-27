# ADR-0001 — Réutiliser une image projet pour KFP et Airflow

- **Statut :** proposé
- **Date :** 2026-10-27
- **Auteur :** @KhalilBenZahra1
- **Relu par :** en attente de la revue croisée du binôme
- **Périmètre :** socle, Lab 2
- **Liens :** `labs/m2-pipelines/README.md`, `reports/rapport-m2.md`

## Contexte

Le Lab 1 contient un pipeline DVC validé et un contrat `dataset.yaml`. Le Lab 2 doit
exécuter les mêmes étapes sous deux orchestrateurs, dans le cluster kind existant.
Réécrire le prétraitement ou les métriques créerait plusieurs implémentations divergentes.
Le poste Windows utilise Ubuntu WSL2 ; 8080 et 8081 sont déjà occupés.

## Options envisagées

| Option | Avantages | Inconvénients |
|---|---|---|
| Composants autonomes | Peu de préparation initiale | Logique dupliquée, installations à chaque pod |
| Image projet commune | Même code, contrat et dépendances dans chaque pod | Reconstruction et nouveau tag à chaque changement embarqué |
| DVC seul | Pipeline déjà validé | Ne répond pas à la comparaison des orchestrateurs demandée |

## Décision

Nous utilisons une image projet versionnée. `pipelines.stage` lance les modules `src`
dans des dossiers temporaires qui reproduisent les chemins DVC. Les composants KFP relient
les fichiers aux artefacts typés ; les tâches KubernetesPodOperator utilisent un préfixe S3
propre au run et limitent XCom aux identifiants et métriques. MLflow conserve le tracking et
le registre communs. Aucun identifiant S3 n'est nécessaire aux composants KFP : ils parlent
au proxy MLflow. Airflow reçoit le secret Kubernetes du stockage du cours.

L'interface KFP utilise 8082 et Airflow 8083. Le port-forward KFP réutilise un service sain,
sans recherche de processus par un motif `pkill -f` qui pourrait correspondre au shell Make.
L'hôte de validation KFP est transmis par la variable documentée `KFP_HOST`, sans modifier
les contrôles officiels.

## Conséquences

- **Positives :** le code métier du Lab 1 reste la référence ; les runs conservent leur
  traçabilité et les modèles historiques restent disponibles.
- **Négatives :** une modification embarquée impose un nouveau tag puis une recompilation ;
  le SDK KFP et ses dépendances augmentent la taille de l'image.
- **Vérification :** pipeline local, récupération réelle de l'image par Kubernetes, runs
  KFP avec cache, DAG Airflow, liens MLflow et `make check-m2`. Les résultats sont consignés
  dans le rapport, sans assimiler la compilation à une exécution Kubernetes.
