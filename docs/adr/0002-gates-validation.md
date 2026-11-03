# ADR-0002 — Figer le contrat et bloquer les étapes ML par trois gates

- **Statut :** proposé
- **Date :** 2026-11-03
- **Auteur :** @KhalilBenZahra1
- **Relu par :** en attente de la revue croisée du binôme
- **Périmètre :** Lab 3, compatibilité Labs 0 à 2
- **Liens :** `labs/m3-validation/README.md`, `docs/adr/0001-reutiliser-image-pipeline.md`

## Contexte

Le pipeline du Lab 2 réutilise les modules `src` dans une image commune à KFP et Airflow.
Le Lab 3 doit refuser les données incorrectes, le drift bloquant et les modèles invalides
avant les étapes concernées, en conservant le contrat du dataset et l'historique MLflow.

## Options envisagées

| Option | Avantages | Inconvénients |
|---|---|---|
| Contrôles uniquement locaux | Diagnostic rapide | Aucun blocage garanti sur le cluster |
| Gates du guide et contrat GX versionné | Contrat reproductible, dépendances explicites, rapports typés | Image plus lourde et ressources mémoire adaptées |
| Réécrire les traitements dans les composants | Chaque composant se suffit | Logique dupliquée et divergence avec DVC |

## Décision

Nous appliquons les trois gates du guide. GX 1.23.2 génère les 67 expectations depuis
`dataset.yaml` et les 800 lignes d'entraînement ; l'image transporte cette suite figée.
La validation utilise le checkpoint versionné sans reconstruire la suite depuis son entrée.
La préparation attend GX, l'entraînement attend le drift, et l'enregistrement attend
l'évaluation et le gate du modèle. L'entraînement conserve son cache désactivé.

Le drift combine significativité (KS ou χ², p-value < 0,05) et magnitude (PSI ≥ 0,25).
Le gate bloque à partir de 10 % de colonnes déplacées. Wasserstein normalisé et le rapport
Evidently restent des éléments de diagnostic. La démonstration utilise `fail_on_drift=False`.
Le modèle passe les deux tests explicites Evidently 0.7.23 et les huit tests pytest du guide.

Les composants délèguent à `pipelines.stage` et `src`. Une erreur copie les rapports locaux
existants puis est propagée ; un composant KFP en échec peut ne pas publier ces sorties.
Les credentials du stockage interne KFP sont lus en mémoire pour télécharger les rapports,
distincts du stockage S3 du cours. Les sorties générées et `gx/uncommitted/` restent hors Git.

L'image finale est `localhost:5001/scoring-pipeline:1.2.0` dans les trois compilations et le
DAG Airflow. Celui-ci conserve les six tâches du Lab 2 ; sa validation GX dispose de 1 GiB.
Les dépendances complètes du SDK, correction du Lab 2, sont conservées. Les seuls ajustements
au guide sont les délais/tentatives pip pour le réseau observé, l'exclusion explicite du
répertoire GX généré pour yamllint, et la fixture des anciens tests utilisant désormais
des données d'entraînement conformes au contrat figé. Les seuils restent ceux du guide.

## Conséquences et vérification

- **Positives :** code métier du Lab 1 conservé, contrat figé, rapports HTML et métriques
  publiés, enregistrement après réussite des trois gates et traçabilité `kfp_run_id`.
- **Limites :** les téléchargements externes dépendent du réseau ; deux tentatives initiales
  ont échoué à l'ingestion sur une erreur DNS et sont conservées dans l'historique KFP.
  Les sondes DNS ont ensuite réussi ; aucune modification du DNS ou de `src/download.py`.
- **Contrôles :** `make check-m3` 20/20 ; contrôle final Lab 2 19/19 ; Labs 0 et 1 19/19
  et 18/18 ; lint et 23 tests réussis. Airflow est chargé sans erreur avec le tag 1.2.0 ;
  son DAG complet n'a pas été relancé pour ce Lab 3.

| Scénario réel | Run KFP | État observé |
|---|---|---|
| `scoring-pipeline` | `6565f288-46c4-460f-b1af-e6d748e97d1e` | SUCCEEDED |
| `scoring-bad-data-test` | `2e099ed3-7a04-44bb-a233-ebdfc6427bbe` | FAILED |
| `scoring-drift-demo` | `8c03d890-e5d8-43cc-87ce-c53e90af423a` | SUCCEEDED |

Le scénario corrompu échoue à `validate-data` (3 violations), avec préparation non déclenchée.
Le scénario déplacé signale 3 colonnes sur 21 (14,29 %) et réussit. Les rapports téléchargés
comprennent `reports/kfp/drift.html`, vérifié dans le bucket `mlpipeline` du service
`kubeflow/seaweedfs`. Les JSON confirment 67 contrôles GX et 10 contrôles modèle sans échec.

MLflow : run `7bf737a9c38b43b5b7c0c9bce7d92ab9`, version **17**, tags
`launched_by=kfp` et `kfp_run_id=6565f288-46c4-460f-b1af-e6d748e97d1e`, ROC AUC **0,8094**,
coût métier **108**, alias `champion` et `challenger` sur cette version. Le hash des données
reste `24b8e38b9c8688d495afc8eb5cb40127`. Les données, le modèle DVC et `dvc.lock` sont préservés.
