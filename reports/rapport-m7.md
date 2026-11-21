# Rapport — Lab 7 : monitoring du modèle de scoring

État intermédiaire observé le **21 novembre 2026** : deux PR dépendantes, aucune fusion.
L'instrumentation est testée localement et dans la CI ; la stack est installée. Les
démonstrations des étapes 2.2, 9 et 10 restent explicitement à réaliser après les fusions.

## 1. Architecture déployée

Flux du guide : API Knative → PodMonitor → Prometheus → Grafana / Alertmanager ;
API → Alloy → Loki → CronJob Evidently → Pushgateway → Prometheus, avec rapport vers S3.
Le webhook CT du Lab 6 et Argo CD complètent ensuite le cycle de ré-entraînement et GitOps.
Les flux de notifications et CT ne sont pas activés dans cette phase.

Charts installés : kube-prometheus-stack 91.9.0, Pushgateway 3.9.0, Loki 18.13.8 et
Alloy 1.13.0. Les **11 pods de la stack sont Running et prêts**. Grafana 13.2.3 répond
sur [localhost:3000](http://localhost:3000), Prometheus sur
[localhost:9090](http://localhost:9090), Alertmanager sur
[localhost:9093](http://localhost:9093), Loki sur 3100 et Pushgateway sur 9091.
Les cinq contrôles HTTP de disponibilité ont réussi. Les values Loki/Alloy fournies
dans `infra/monitoring/` sont réutilisées ; logs éphémères avec rétention de 72 h,
métriques retenues 24 h. Grafana utilise un Secret local, sans mot de passe dans Git.
Adaptation ciblée : la variante officielle Ubuntu **13.2.3**, à la place du tag
distroless par défaut du même chart, fournit la commande `test` utilisée par le contrôle
officiel pour inspecter le fichier du dashboard. L'API Grafana confirmait déjà ses 18
panneaux ; aucune modification des critères de vérification ni montée de version.

Production préservée : image `2.1.8`, modèle
`19`, seuil `0.3182`,
révision `scoring-model-predictor-00006` à 100 %. Le spec de l'InferenceService est identique
à l'audit initial ; Argo CD staging/prod reste Synced/Healthy. KFP demeure actif avec ses
14 déploiements disponibles, sans pause nécessaire ; Airflow reste arrêté.

Image du job `localhost:5001/scoring-drift:1.0.0`, UID/GID `10001:10001`, 308.9 Mo ; imports et absence de `.env` vérifiés. Digest : `sha256:2ecc6a2b193b105b2b0fbf7e542cabe8aa1113bce8f4d1d90220acd50f263d57`.

## 2. Instrumentation et dashboard

| Métrique | Type / labels métier | Question |
|---|---|---|
| `http_requests_total` | compteur ; method, handler, code | Trafic et erreurs HTTP ? |
| `ml_inference_latency_seconds` | histogramme | Latence des lots de prédiction ? |
| `ml_prediction_score` | histogramme | Distribution des probabilités ? |
| `ml_predictions_total` | compteur ; model, version, outcome | Décisions positives/négatives ? |
| `ml_predictions_by_group_total` | compteur ; attribute, group, outcome | Taux par groupe sensible ? |
| `ml_model_info` | Info ; versions et threshold | Quel modèle est effectivement servi ? |

Le module possède son propre registre : les réimports de tests restent indépendants.
Chemins inconnus, méthodes non standard et modalités catégorielles sont bornés ; les
groupes et bornes numériques viennent de `dataset.yaml`. Le journal JSON est
désactivable avec `LOG_PREDICTIONS=false` ; aucune ligne de prédiction n'est versionnée.

Résultats locaux : **78 tests réussis**, dont 17 monitoring et quatre tests du job ;
`make lint` réussi. Copie sans `.env`, DVC, MLflow ni configuration Kubernetes :
**70 réussis, 8 comportementaux ignorés**, sans élargissement des SKIP. La première PR
[#12](https://github.com/KhalilBenZahra1/mlops-cours-2026/pull/12) a une
[CI verte](https://github.com/KhalilBenZahra1/mlops-cours-2026/actions/runs/44904771652) :
lint/tests, build et smoke test. Publication et commit staging sont normalement ignorés
sur une PR ; aucun déclencheur modifié.

Serveur temporaire réel, arrêté après test : 20 lots de 20 lignes de test, soit
400 prédictions (220 décisions 0,
180 décisions 1), 11 séries de groupes pour les trois attributs
sensibles ; `/metrics` 200 sans redirection, cinq requêtes invalides 422 et imputation
des valeurs nulles vérifiées. 401 événements JSON avec journalisation, zéro sans.
ONNX, métadonnées, seuil et SHA-256 inchangés.

Grafana charge réellement `scoring-overview` et ses **18 panneaux**, avec les sources
Prometheus/Loki. Les deux cibles PodMonitor de scoring sont découvertes, avec les labels
namespace, isvc et revision, mais répondent **404 sur `/metrics`** : les images actuelles
des Labs précédents ne sont pas instrumentées. Les métriques métier et les captures
en trafic normal/drift restent en attente ; aucun graphe de performance n'est inventé.
Loki reçoit déjà les logs d'accès, mais aucune prédiction JSON de production.

## 3. Alertes

| Alerte | Condition du guide | Sévérité | Runbook |
|---|---|---|---|
| ScoringHighLatency | P95 > 200 ms, 5 min | warning | [latence](../monitoring/runbooks.md#scoringhighlatency) |
| ScoringErrorBudgetBurn | budget 0,5 %, double fenêtre 14,4× / 6× | critical | [budget](../monitoring/runbooks.md#scoringerrorbudgetburn) |
| ScoringDataDrift | variable PSI > 0,25, 5 min | warning | [drift](../monitoring/runbooks.md#scoringdatadrift) |
| ScoringPositiveRateShift | écart > 10 points entre 5 min et 6 h | warning | [décisions](../monitoring/runbooks.md#scoringpositiverateshift) |
| ScoringNoReplicaAvailable | aucun réplica prêt, 2 min | critical | [réplicas](../monitoring/runbooks.md#scoringnoreplicaavailable) |
| ScoringDriftJobStale | publication âgée de 45 min, 5 min | warning | [fraîcheur](../monitoring/runbooks.md#scoringdriftjobstale) |

Les six règles sont chargées, de santé `ok` et observées `inactive`. Les huit recording
rules sont également saines. Le burn rate mesure la consommation du budget d'erreur du
SLO 99,5 % ; les deux fenêtres distinguent un incident durable d'un pic bref ou terminé.

`scoring-slack` est validé en dry-run serveur uniquement. Ni le Secret `slack-webhook`,
ni son routage effectif ne sont créés : aucun message Slack n'est autorisé. Une URL
webhook.site sera demandée au moment du test de notifications et gardée hors Git.
La configuration de routage par sévérité est prête ; aucune notification reçue n'est revendiquée.

## 4. Démo drift → alerte → ré-entraînement

La référence `train.csv` est vérifiée directement sur le remote S3 DVC ; aucun
`dvc repro`, ré-entraînement ou modification du contrat. Le CronJob conserve la période
de 15 minutes du guide mais est **suspendu avant fusion** ; aucun `CT_WEBHOOK_URL`
n'est injecté dans le pod. Job manuel `scoring-drift-premerge-20261121` **Complete**, 0 demandes trouvées : le garde-fou des 500 lignes a empêché tout calcul de PSI et tout rapport HTML. La lecture de la référence S3 et la publication du compteur de lignes au Pushgateway valident la plomberie, sans constituer une démonstration de drift.

Les tests autonomes exécutent réellement Evidently sur une population identique :
un score nul pour chacune des 20 variables et aucun verdict de drift. Ce test isolé
ne remplace pas les demandes réelles de production ni la démonstration du guide.

| Événement de démonstration | État / mesure |
|---|---|
| Trafic normal instrumenté, ≥ 500 demandes | En attente de publication et déploiement après fusion |
| Injection de drift, PSI et rapport S3 | Non exécutés ; aucune heure ou magnitude mesurée |
| Alerte Firing et notification reçue | Non exécutées ; URL de test à fournir au moment utile |
| Appel du webhook et run CT KFP | Non exécutés ; aucun nouvel identifiant |
| Temps total drift → staging/canary | Non mesuré |

Le guide réalise le calcul déclenchant CT depuis le poste, car le webhook est local.
KFP doit alors utiliser **8082**, conformément à l'environnement existant, et le webhook
être relancé avec `CT_AUTO_PROMOTE=0` pour laisser le futur canary à 10 %. Ces actions
restent réservées à la phase après fusion, avec validation du pilote.

## 5. Analyse du canary

Le script `monitoring/canary_analysis.py` et ses tests sont présents. La comparaison
porte sur deux révisions distinctes, avec garde-fous de volume, latence, erreurs et
décisions. **Aucun canary ou rollback exécuté** ; les rapports
`reports/m7/canary-analysis.{md,json}` ne sont donc pas fabriqués. La production reste
à 100 % sur la révision du Lab 6.

`make check-m7` : **9/15 vérifications OK**, code de Make 2 ; les contrôles en attente sont détaillés ci-dessous.

Les contrôles bloqués par l'image non publiée sont : cible up, métriques métier,
métrique de drift par variable et prédictions JSON dans Loki. Le routage de notifications
attend l'URL et l'autorisation du test ; le rapport canary attend la démonstration.
Le succès structurel du présent rapport ne signifie pas que le Lab 7 est terminé.
Non-régression : `make check-m6` **18/18**, code retour 0.

Ordre des PR : `lab/m7-monitoring` → `main`, puis `lab/m7-observabilite` →
`lab/m7-monitoring` (base à ajuster vers `main` après fusion de la première).
Après revue : vérifier CI/GHCR et staging, réaliser le premier canary instrumenté,
désuspendre le CronJob, établir la référence normale, puis seulement les démonstrations
de drift, notifications, CT et analyse du canary. PR #11 laissée intacte.

## 6. Améliorations à prévoir

1. Ajuster fenêtres et burn rates à un historique réel de trafic, puis mesurer les faux positifs.
2. Confronter les indicateurs sans labels aux résultats métier retardés avant une décision de ré-entraînement.
3. Encadrer rétention, accès et minimisation des journaux de caractéristiques sensibles ; 72 h éphémères suffisent au lab.
4. Évaluer stockage persistant et haute disponibilité hors du petit cluster kind.

Ces pistes sont discutées uniquement ; aucun outil ou mécanisme supplémentaire n'est ajouté.
