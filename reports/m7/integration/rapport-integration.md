# Lab 7 — Vérifications d'intégration avant fusion

Observations du **21 novembre 2026**, horodatages en UTC (Tunis : UTC+1).
Branche `lab/m7-integration` issue de `lab/m7-observabilite`. Cette démonstration isolée
ne constitue pas la validation officielle du Lab 7 sur la production.

## 1. Périmètre et ressources préservées

Namespace et InferenceService : `scoring-integration`. Le service dispose de deux
révisions Knative : `scoring-integration-predictor-00001` et `scoring-integration-predictor-00002`, trafic 90/10.
Elles servent **le même code et le même modèle**, avec un identifiant `APP_VERSION`
distinct pour provoquer deux révisions réelles. Aucune recommandation de promotion appliquée.

Image locale : `localhost:5001/scoring-api:m7-integration-db3668ce7ab8`, utilisateur `10001:10001`, taille retournée par
`docker image inspect` : 106854635 octets. Digest :
`sha256:e35b9fe6726b8249d2c22130088a14ad7bf3e93c69ba01528f7d32c20abd415b`.
Modèle embarqué : version **19**, seuil **0.3182**,
SHA-256 ONNX `4b7517525ab6398be391bb58404f8584bdb49502cace1ca070d43b99ddaa222e` ; métadonnées et modèle versionnés inchangés.
Le PodMonitor, les règles, le dashboard UID `scoring-integration`, le CronJob et le
groupe Pushgateway portent des noms et sélecteurs d'intégration distincts.

Le label Evidently `model="scoring-model-integration"` isole les séries dans la stack
partagée ; il ne renomme aucun modèle MLflow. Les rapports HTML ont un préfixe S3 séparé.
CT est explicitement désactivé dans le job et le CronJob reste suspendu.

Les [comparaisons d'état](preserved.json) confirment les PR #11/#12/#13 inchangées
(titre, corps, base, commit, état), les Applications Argo CD et les specs/révisions de
`scoring`/`scoring-staging` inchangées, Synced/Healthy. Overlays, workflow, contrats,
verrou, modèle et preuves antérieures sont inchangés. Production : 2.1.8 / modèle 19 /
révision 00006 à 100 %. KFP reste à 14 déploiements disponibles ; aucune pause nécessaire.
Airflow n'a pas été redémarré. Aucun push sur `main`, entraînement ou changement d'alias.

## 2. Trafic et observabilité réellement vérifiés

Les requêtes viennent de vraies lignes de `data/processed/test.csv`, rejouées par
`monitoring/traffic.py` avec les colonnes de `dataset.yaml`. Il s'agit d'un trafic de
test HTTP réel, pas de demandes de clients en production.

| Scénario | Début UTC | Durée mesurée du processus | Prédictions | Erreurs | Décisions positives | Score moyen |
|---|---|---:|---:|---:|---:|---:|
| Normal | 2026-11-21T16:35:28.493334+00:00 | 180.669 s | 3586 | 0 | 58.4 % | 0.413 |
| Numériques ×1,5 | 2026-11-21T16:42:50.189510+00:00 | 300.751 s | 5977 | 0 | 81.3 % | 0.585 |

Cible : 20 requêtes/s, lots d'une ligne, graine 42. Le second scénario utilise le
comportement par défaut du guide : toutes les variables numériques déclarées dans le
contrat sont multipliées par 1,5. Il diffère donc du scénario illustratif « âge ×0,6 /
montant ×2,5 » ; aucune valeur de l'exemple n'est reprise comme résultat.

Vérifications : `/health`, `/metadata`, `/metrics` direct 200 et erreur 422 sur lot vide ;
deux cibles Prometheus `up=1`, compteurs par révision et groupes sensibles présents.
Loki/Alloy reçoit les événements JSON avec les bonnes colonnes, sans export de lignes
brutes dans Git. Grafana charge le dashboard dédié et ses **18/18 panneaux** ont des
données après Evidently ; une requête métier via le proxy de source Grafana réussit.
Voir [normal](observability-normal.json) et [après dérive](observability-drift.json).

Limite observée de collecte : instantané stdout **9564 événements**, requête de
comptage Loki **9560** sur une heure, soit un écart de 4.
La cause n'est pas établie ; aucune garantie d'ingestion sans perte n'est revendiquée.
Les deux calculs Evidently disposent néanmoins du volume réel requis dans Loki.
Les données sources et journaux restent hors Git, avec la rétention Loki du guide.

## 3. Evidently sur les demandes relues dans Loki

Référence DVC S3 : **800 lignes**. Normal : **3586 demandes**,
20 scores, aucune dérive, PSI maximal **0.129070**.
Après injection isolée : **5000 demandes récentes** (limite MAX_ROWS=5000),
**7/20 variables en dérive**, seuil PSI **0,25** inchangé.
Les métriques après dérive ont été relues après vérification de la fraîcheur du push et
du compteur de lignes ; elles ne sont pas celles de l'exécution normale précédente.

| Variable du contrat | PSI normal | PSI dérivé | Dérive après injection |
|---|---:|---:|---|
| `age` | 0.083350 | 3.146946 | Oui |
| `checking_status` | 0.003014 | 0.000864 | Non |
| `credit_amount` | 0.129070 | 0.502235 | Oui |
| `credit_history` | 0.015340 | 0.016583 | Non |
| `duration` | 0.062092 | 1.365302 | Oui |
| `employment` | 0.050837 | 0.055107 | Non |
| `existing_credits` | 0.018724 | 6.480172 | Oui |
| `foreign_worker` | 0.000493 | 0.001102 | Non |
| `housing` | 0.000059 | 0.000042 | Non |
| `installment_commitment` | 0.022970 | 5.952967 | Oui |
| `job` | 0.013201 | 0.012956 | Non |
| `num_dependents` | 0.003810 | 9.755959 | Oui |
| `other_parties` | 0.014669 | 0.014268 | Non |
| `other_payment_plans` | 0.001215 | 0.001788 | Non |
| `own_telephone` | 0.001201 | 0.000437 | Non |
| `personal_status` | 0.019918 | 0.024306 | Non |
| `property_magnitude` | 0.002802 | 0.002286 | Non |
| `purpose` | 0.068258 | 0.076011 | Non |
| `residence_since` | 0.019098 | 5.297526 | Oui |
| `savings_status` | 0.032063 | 0.038703 | Non |

Jobs Complete : `scoring-drift-integration-normal-20261121` (2026-11-21T16:39:47Z → 2026-11-21T16:40:04Z) et
`scoring-drift-integration-shift-20261121` (2026-11-21T16:48:34Z → 2026-11-21T16:48:48Z). Les rapports HTML ont été téléchargés
depuis S3 et vérifiés, mais ne sont pas commités :

- Normal : `s3://monitoring/integration/drift-reports/drift-20261121T163956Z.html` ; 4362047 octets ; SHA-256 `07903c1816ac4b93aa99ce38af151da75a9eae251f2001abfe363152325b53c4`.
- Dérivé : `s3://monitoring/integration/drift-reports/drift-20261121T164842Z.html` ; 4362846 octets ; SHA-256 `fe436f7d1bb106db241b2c89fd1352ed73d4a7aaba47df742860608a8bc7182c`.

Les [scores normaux](evidently-normal.json) et [dérivés](evidently-drift.json) sont des
agrégats observés, pas des données de demande. Aucun webhook CT appelé.

## 4. Analyse de canary en lecture seule

Le script du professeur a comparé les révisions d'intégration sur cinq minutes, avant
le trafic dérivé : six garde-fous **PASS**, décision **CONTINUE**, code retour 0.
Voir les rapports authentiques [Markdown](canary-analysis.md) et [JSON](canary-analysis.json).

| Indicateur | Stable | Candidate |
|---|---:|---:|
| Requêtes estimées par `increase()` | 3314 | 375 |
| P95 issu des histogrammes | 4.8 ms | 4.8 ms |
| Taux 5xx | 0.00% | 0.00% |
| Décisions positives | 58.49% | 59.35% |

Le PSI des scores est 0,047. Les volumes `increase()` sont extrapolés sur la fenêtre,
ils ne sont pas le décompte exact du générateur. Les quantiles sont estimés depuis les
buckets, pas mesurés à la requête près. Deux révisions identiques valident la plomberie,
pas la supériorité d'un nouveau modèle ni une décision de production sur la durée.

**Ne pas exécuter la commande GitOps suggérée dans le rapport.** Elle viserait les
overlays de production. Aucun `--apply`/`--push` utilisé ; ni promotion ni rollback.
Le spec et le trafic d'intégration sont restés à 90/10 après l'analyse.

## 5. Alertes internes et notifications non activées

Les sept séries `ScoringIntegrationDataDrift`, équipe `ml-integration`, sont passées
Pending (activeAt `2026-11-21T16:49:09.960473346Z`), puis Firing
observé à `2026-11-21T16:54:23.442468+00:00`. Les seuils et `for: 5m` du guide
sont conservés. **Sept alertes reçues par Alertmanager**, configuration effective limitée
au récepteur `null`. Aucun message Slack, appel externe ou déclenchement CT.
Les états et labels agrégés figurent dans [alerts.json](alerts.json).

Le fichier `monitoring/integration/alertmanager-test.yaml` est seulement validé en
dry-run et exclu du Kustomize appliqué. Une URL webhook.site et l'autorisation explicite
du pilote sont nécessaires avant un test externe ; ce point ne dépend pas techniquement
de la fusion. Aucun Secret d'URL n'a été créé. L'environnement reste disponible pour
inspection ; générateurs arrêtés naturellement, CronJobs suspendus, alertes de test
susceptibles de rester Firing tant que les métriques de dérive restent au Pushgateway.

## 6. Tests, validation officielle et suite après revue

- `make lint test` : lint réussi, **83 tests réussis**, dont cinq garde-fous d'isolation.
- Copie sans `.env`, données/modèle DVC, MLflow ou configuration Kubernetes :
  **75 réussis, 8 comportementaux ignorés**, sans nouveau SKIP.
- [Non-régression Lab 6](check-m6.txt) : **18/18**, code Make 0 ; vérification historique,
  elle ne signifie pas qu'un nouveau CT a été exécuté pendant cette expérience.
- [Contrôle officiel Lab 7](check-m7.txt), sélecteurs `scoring/scoring-model` :
  **9/15**, script 6 / Make 2. Aucun critère modifié et aucun résultat d'intégration
  substitué à un résultat de production.

Restent à réaliser après approbation/fusion : publication GHCR et staging depuis `main`,
premier canary instrumenté en production, métriques/logs/PSI de production, démonstration
officielle de drift → alerte → CT → CI → staging, puis analyse et décision GitOps de
canary/promotion/rollback. Les quatre contrôles de données/observabilité de production,
le routage officiel de notifications et le rapport canary officiel restent en attente.
Le rapport d'intégration n'est volontairement pas placé au chemin officiel du canary.

PR dépendante vers `lab/m7-observabilite`, après #12 puis #13 dans l'ordre de revue.
Les bases des PR existantes ne sont pas modifiées dans cette phase. La CI scoring reste
réservée aux PR vers `main` selon le workflow inchangé ; les validations locales sont
rapportées distinctement. Aucun entraînement, changement d'alias, nettoyage global,
suppression de volume ou recréation du cluster.
