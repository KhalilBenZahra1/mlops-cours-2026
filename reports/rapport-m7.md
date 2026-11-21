# Rapport — Lab 7 : monitoring du modèle de scoring

Validation officielle effectuée le **21 novembre 2026** sur `scoring/scoring-model`.
Tous les horaires ci-dessous sont en **UTC** (Tunis : UTC + 1).
`make check-m7` : **15/15, code retour 0**. Le CT a réellement entraîné un challenger,
puis le gate a refusé sa promotion. Le canary suivant utilise donc le repli de l'étape
10.2 : nouvelle image du champion existant. Aucun succès de promotion automatique du
modèle 20 n'est revendiqué.

## 1. Architecture déployée

API Knative → PodMonitor → Prometheus → Grafana / Alertmanager ; API → Alloy → Loki
→ CronJob Evidently → Pushgateway → Prometheus, avec rapports HTML sur le S3 du cours.
Le calcul relancé depuis le poste peut appeler le webhook CT local ; KFP, MLflow,
GitHub Actions et Argo CD assurent ensuite le parcours prévu au Lab 6.

Les PR [#12](https://github.com/KhalilBenZahra1/mlops-cours-2026/pull/12),
[#13](https://github.com/KhalilBenZahra1/mlops-cours-2026/pull/13) et
[#14](https://github.com/KhalilBenZahra1/mlops-cours-2026/pull/14), approuvées par le binôme, ont été fusionnées
dans cet ordre, après ajustement des bases vers `main` et contrôles applicables réussis.
Le seul conflit de journal a été résolu en conservant les deux ajouts ; les neuf fichiers
du rendu du Lab 6, dont ses cinq PNG, conservent exactement leur SHA-256.
Branches dépendantes et commits automatiques de staging préservés.
[Approbations](m7/official/approbations-avant-fusion.json),
[fusions](m7/official/fusions.json), [CI](m7/official/ci.json),
[préservation du Lab 6](m7/official/preservation-lab6.json).

État final confirmé : `ghcr.io/khalilbenzahra1/mlops-cours-2026/scoring-api:2.1.16`, modèle **19**, seuil **0,3182**,
révision `scoring-model-predictor-00010` à 100 %. Image réellement récupérée par le nœud :
`ghcr.io/khalilbenzahra1/mlops-cours-2026/scoring-api@sha256:01ac21e5ccb05b8fd99ebb5e4ff79f3356f0266659fc294dc0a7d5c73190d51c`. Run du champion : `f2d47c40fcfd4fe98b66a149ed010410` ;
SHA-256 ONNX inchangé : `4b7517525ab6398be391bb58404f8584bdb49502cace1ca070d43b99ddaa222e`.
Les deux Applications Argo CD sont Synced/Healthy ; KFP conserve ses 14 déploiements
disponibles, Airflow reste arrêté, l'environnement d'intégration est conservé.
[Instantané final](m7/official/snapshot.json).

Les CI sur `main` n°11, 13 et 15 ont publié respectivement `2.1.11`, `2.1.13` et
`2.1.15` sur GHCR, puis commité les tags staging. Trois jobs réussis par exécution :
lint/tests, build/smoke/publication, commit GitOps staging. La
[CI n°15](https://github.com/KhalilBenZahra1/mlops-cours-2026/actions/runs/44933819281) confirme le dernier état
fusionné. Les images ont réellement été récupérées par kind, sans `kind load`.

Stack existante réutilisée : kube-prometheus-stack 91.9.0, Pushgateway 3.9.0, Loki
18.13.8, Alloy 1.13.0 ; **11 pods prêts**. Grafana 13.2.3 utilise la variante Ubuntu
de la même version, nécessaire à la commande `test` du contrôle officiel ; mot de passe
dans un Secret, jamais dans Git. Métriques retenues 24 h, logs éphémères 72 h.
Trois nœuds Ready, KFP **14 déploiements disponibles**, Airflow toujours arrêté.
L'environnement antérieur `scoring-integration` est conservé, spec inchangé : ses
[résultats isolés](m7/integration/canary-analysis.md) ne constituent pas les preuves de production.

**État final réellement servi :** `ghcr.io/khalilbenzahra1/mlops-cours-2026/scoring-api:2.1.16`, révision `scoring-model-predictor-00010` à **100 %**,
modèle **19**, run MLflow `f2d47c40fcfd4fe98b66a149ed010410`, seuil **0.3182**.
ONNX et métadonnées versionnés inchangés ; SHA-256 ONNX `4b7517525ab6398be391bb58404f8584bdb49502cace1ca070d43b99ddaa222e`.
Argo CD staging/prod **Synced/Healthy** ; détails et digests des pods dans
[restauration](m7/official/restored.json) et [état final](m7/official/snapshot.json).

## 2. Instrumentation et dashboard

| Métrique | Type / labels métier | Usage |
|---|---|---|
| `http_requests_total` | compteur ; method, handler, code | trafic, erreurs HTTP |
| `ml_inference_latency_seconds` | histogramme | latence des lots |
| `ml_prediction_score` | histogramme | distribution des probabilités |
| `ml_predictions_total` | compteur ; model, version, outcome | décisions 0/1 |
| `ml_predictions_by_group_total` | compteur ; attribute, group, outcome | décisions par groupe sensible |
| `ml_model_info` | Info ; versions et threshold | version et seuil effectivement servis |

Registre Prometheus propre au module ; labels bornés et groupes issus de `dataset.yaml`.
`LOG_PREDICTIONS=false` désactive le journal JSON. Contrats, imputation, limites de batch,
métadonnées, `/version` et contrôles SHA-256 conservés. Aucun journal brut de prédictions
n'est commité.

Le premier canary instrumenté `2.1.15` / modèle 19 a été vérifié à 18:14:07 puis promu
à 18:15:44 : prédiction et `/metrics` 200. La stable `2.1.8` prédisait correctement mais
répondait 404 sur `/metrics` : **aucune comparaison métrique avec cette stable**.
[Preuve du contrôle de fumée](m7/official/first-canary.json).

Production instrumentée : cibles Prometheus UP par révision, trois attributs sensibles
présents, événements JSON réellement reçus par Loki/Alloy ; **18/18 panneaux Grafana
alimentés**, requête également vérifiée par le proxy de source Grafana.
[Normal](m7/official/observed-normal.json), [drift](m7/official/observed-drift.json),
[final](m7/official/observed-final.json). Les compteurs instantanés Loki et stdout ne
sont pas des mesures de perte : fenêtres, rotation des logs du kubelet et instants de
lecture diffèrent. Aucune garantie de collecte sans perte n'est déduite.

Tests finaux : **83 réussis**, sans SKIP local, et `make lint` réussi.
La copie autonome et la CI conservent **75 réussis, 8 comportementaux ignorés** faute
d'artifacts DVC, sans élargissement des SKIP. Les anciens contrôles API/modèle restent
présents ; [sortie de la suite](m7/official/test.txt), [lint](m7/official/lint.txt).

## 3. Alertes

| Alerte | Condition du guide | Sévérité |
|---|---|---|
| ScoringHighLatency | P95 > 200 ms pendant 5 min | warning |
| ScoringErrorBudgetBurn | budget 0,5 %, double fenêtre 14,4× / 6× | critical |
| ScoringDataDrift | PSI > 0,25 pendant 5 min | warning |
| ScoringPositiveRateShift | écart > 10 points entre 5 min et 6 h | warning |
| ScoringNoReplicaAvailable | aucun réplica prêt pendant 2 min | critical |
| ScoringDriftJobStale | publication âgée de 45 min pendant 5 min | warning |

Six règles et huit recording rules chargées et saines ;
[runbooks](../monitoring/runbooks.md) et routage par sévérité conservés.
Le burn rate mesure la consommation du budget du SLO 99,5 % ; ses deux fenêtres évitent
de confondre un pic bref avec un incident durable.

Après autorisation du pilote, `scoring-slack` a été activé avec une destination
**webhook.site uniquement**. L'URL reste dans le Secret Kubernetes `slack-webhook`,
absente de Git ; **aucun canal Slack contacté**. Les premiers POST arrivaient mais
la réponse HTML par défaut était rejetée par le notifier au format Slack. Réglage du
seul endpoint de test à HTTP 200, corps `ok`, type `text/plain`, à 18:32:28 ; aucun seuil
ni règle d'alerte modifié. Voir [réponse de test](m7/official/webhook-response.json) et
[documentation de l'API Webhook.site](https://docs.webhook.site/api/tokens.html).

Réceptions vérifiées : test FIRING 18:32:48 / RESOLVED 18:37:48 ; drift FIRING
18:36:19, rappel 18:41:19, RESOLVED 18:46:20. La règle ScoringDataDrift était Pending
à 18:35:16 et Firing à 18:36:26, pour les deux variables concernées.
[États réels](m7/official/alerts.json), [accusés de réception expurgés](m7/official/notifications.json).
Le taux positif observé passe de 58,0 % à 67,7 %, soit +9,7 points : aucune activation
de ScoringPositiveRateShift n'est revendiquée, et l'historique de 6 h est limité.

## 4. Démo drift → alerte → ré-entraînement

Le CronJob officiel est actif toutes les 15 minutes ; référence DVC/S3 **800 lignes**,
fenêtre Loki 60 min, minimum 500 demandes, maximum 5 000. L'historique des jobs est
porté à 20 pour conserver les preuves de cette démonstration. Son pod n'a pas d'URL CT :
conformément au guide, le calcul déclenchant CT est relancé depuis le poste, car le
webhook est local. **La notification n'appelle pas directement le CT.**

Trafic synthétique du script fourni, construit avec de vraies lignes du test et envoyé
par HTTP à la production : 20 requêtes/s visées, scénario German Credit explicite
`age=0.6`, `credit_amount=2.5`. Il ne s'agit pas de clients réels.

| Phase / job | Demandes et résultat observés |
|---|---|
| Normal, 18:17:27–18:24:53 | 8 853 prédictions, zéro erreur ; 58,0 % positives, score moyen 0,411 |
| `scoring-drift-29921415`, 18:22:53–18:23:10 | 5 000 demandes ; 0/20 variables en drift, PSI max 0.136776 |
| Drift, 18:25:02–18:40:42 | 18 688 prédictions, zéro erreur ; 67,7 % positives, score moyen 0,486 |
| `scoring-drift-29921430`, 18:30:00–18:30:12 | 5 000 demandes ; 2/20 variables, PSI age 4.163755, credit_amount 1.458036 |
| Retour normal, `scoring-drift-m7-recovery-190610` | 5 000 demandes ; 0/20 variables, PSI max 0.138398 |

Les trois rapports HTML ont été relus depuis S3 et leurs SHA-256 enregistrés :
[normal](m7/official/drift-normal.json), [drift](m7/official/drift-drift.json),
[retour normal](m7/official/drift-recovery.json). URI du rapport dérivé :
`s3://monitoring/drift-reports/drift-20261121T183007Z.html`. Les 20 séries PSI et les compteurs sont publiés au Pushgateway
et lus dans Prometheus. [Volumes de trafic](m7/official/trafic.json).

Chronologie réelle : drift à 18:25:02 → premier POST FIRING reçu à 18:36:19
(environ **677 s**, avec attente du CronJob et temporisation de l'alerte) → appel CT
accepté à 18:37:59 → fin KFP à 18:41:53. Le délai comprend les actions humaines ;
il ne mesure pas une boucle entièrement autonome.

Prévol : KFP prêt sur 8082, MLflow joignable, webhook actif avec `CT_AUTO_RELEASE=1`
et **`CT_AUTO_PROMOTE=0`**. Run
[`a052e470-2935-40d6-a687-f2175e33b88a`](http://localhost:8082/#/runs/details/a052e470-2935-40d6-a687-f2175e33b88a)
**SUCCEEDED**, sept composants métier réussis, environ **233 s** de 18:38:00 à 18:41:53.
Modèle **20**, run MLflow `9ed81e39c7f34009a297653c505ce627`, tag
`ct_trigger=evidently-drift`, part 0,1000, `kfp_run_id` correct.

Le lot de prédictions ne possède pas de vérités terrain. L'événement n'envoie donc pas
de `data_uri` étiqueté : repli du guide `src.download`, explicitement tracé, et aucune
étiquette produite par le modèle n'est utilisée comme vérité terrain d'entraînement.
Le gate réévalue **les deux modèles sur le même test de ce run**, à leurs seuils propres :

| Modèle réévalué | ROC AUC | Coût métier |
|---|---:|---:|
| Champion 19 | 0,8026 | 105 |
| Challenger 20 | 0,8094 | 108 |

Le seuil AUC minimal passe, mais **108 > 105**, sans tolérance d'augmentation du coût :
modèle 20 **rejected / validation_status=failed**, alias challenger seulement.
Le gate retourne un verdict de refus, sans faire échouer le pipeline ; champion **19**
inchangé et `promoted_version=null`. Ces coûts réévalués ne doivent pas être confondus
avec les tags historiques du champion issus de son ancien jeu de test.
**Aucune publication automatique ni promotion du modèle 20.**
[Gate authentique](m7/official/gate.md), [sept tâches et registre](m7/official/ct.json),
[appel](m7/official/trigger.json), [prévol](m7/official/ct-preflight.json).

## 5. Analyse du canary

Le repli autorisé en étape 10.2 a été utilisé après le refus du modèle : déclenchement
manuel du workflow existant sur `main`, sans modification de ses déclencheurs.
[CI n°16](https://github.com/KhalilBenZahra1/mlops-cours-2026/actions/runs/44937266448), trois jobs réussis,
publication GHCR **2.1.16**, commit staging `3bb4610`. Même champion 19 et même ONNX
que la stable instrumentée 2.1.15. Cette publication est **manuelle**, distincte du CT.

Trafic normal rétabli depuis 18:40:49. Canary 10 % prêt à 18:51:02 ; analyses officielles
sur 5 minutes, sans forcer une promotion lorsque des données manquent.

| Analyse | Volume stable / canary | 5xx | P95 stable / canary | PSI scores | Positives stable / canary | Décision |
|---|---:|---|---|---:|---|---|
| 10 %, 18:54:08 | 5 566 / 382 | 0 / 0 % | 4,8 / 4,8 ms | 0,049 | 59,1 / 55,2 % | six PASS, CONTINUE → 50 % |
| 50 %, 18:57:56 | 4 304 / 1 680 | 0 / 0 % | 4,8 / 4,8 ms | 0,018 | 58,7 / 57,0 % | six PASS, PROMOTE → 100 % |

Volumes issus de `increase()` Prometheus et P95 estimés par histogramme, non latences
brutes chronométrées. Les différences de scores/décisions viennent d'échantillons
différents ; ces courtes fenêtres synthétiques ne prouvent pas un gain métier.
Commits GitOps `ceb5428` (10 %), `f2144df` (50 %), `81a55ca` (100 %), états réels
confirmés après synchronisation Argo CD.
[Analyse 10 %](m7/official/canary-10.md), [50 %](m7/official/canary-50.md).

Canary défectueux du guide : image locale **2.0.0 / modèle 17**, révision 00009 à 10 %,
prête à 19:02:00 ; `/metrics` 404. À 19:03:37, observabilité FAIL (`up=0`), autres
garde-fous WAIT faute de métriques du canary ; priorité au FAIL : **ROLLBACK**, code
retour **1 attendu**. Commit `023c6ae`, trafic réel stable 100 % / canary 0 % confirmé.
Le modèle 17 diffère du champion 19 : alias MLflow inchangé, conformément au guide.
[Rapport canonique du rollback](m7/canary-analysis.md),
[JSON](m7/canary-analysis.json), [application](m7/official/analysis-bad.json).

Restauration finale commit `387ce1e` : bonne image **2.1.16** à **100 %**, confirmée à
19:06:08, révision **scoring-model-predictor-00010**, champion **19**. La chaîne automatique a donc été
testée jusqu'au refus du gate ; la promotion et le rollback par métriques ont été
démontrés ensuite sur le repli du champion, sans assouplir les garde-fous.

Contrôles finaux : [Lab 7 **15/15**](m7/official/check-m7.txt),
[Lab 6 **18/18**](m7/official/check-m6.txt), [Lab 5 **14/14**](m7/official/check-m5.txt),
tous code 0 ; lint et 83 tests réussis. Le contrôle Lab 6 confirme toujours le champion
19 validé et servi ; il ne signifie pas que le challenger 20 de cette séance a été promu.
Le SHA-256 du contrôle officiel Lab 7 est inchangé, conservé dans l'état final.

Captures PNG de cette démonstration **non produites dans cette séance** : les preuves
jointes sont des sorties/API réelles, pas des captures reconstituées. Pour la soutenance :

1. [Grafana](http://localhost:3000/d/scoring-overview) : namespace `scoring`, fenêtre UTC
   18:17–19:08 le 21/11, puis zoom 18:25–18:41 ; métriques, PSI et logs JSON. Réduire la
   vue des caractéristiques de demandes sensibles sur les captures partagées.
2. [Prometheus](http://localhost:9090/targets) : cible courante UP ; historique d'alerte
   via requête `ALERTS{alertname="ScoringDataDrift"}`. [Alertmanager](http://localhost:9093)
   peut maintenant être résolu : ne pas le présenter comme encore Firing.
3. Réceptions webhook.site FIRING/RESOLVED en masquant l'URL et l'identifiant de l'endpoint.
4. KFP : run exact `a052e470-2935-40d6-a687-f2175e33b88a`, sept tâches et gate REFUSÉE ;
   [MLflow](http://localhost:5000) : champion 19 et challenger 20 rejeté.
5. [Argo CD](https://localhost:8443) : deux Applications Synced/Healthy ; CI n°15 et n°16,
   distinction push/main et déclenchement manuel ; `/version` final avec le Host KServe.
6. Terminal Ubuntu : `cd ~/mlops-cours-2026 && make check-m7`, puis les deux rapports
   canary positifs et le rollback. Utiliser une vraie capture du terminal, sans `.env`.

Les interfaces, le webhook CT inactif (`busy=false`) et le trafic normal nécessaire aux
captures restent disponibles. Aucun nettoyage, suppression d'intégration ou pause KFP.

## 6. Améliorations à prévoir

1. Garder chaque palier plusieurs heures sur du trafic représentatif ; 100 requêtes
   minimales détectent une panne grossière, pas une variation métier de deux points.
2. Joindre les vérités terrain retardées avant le CT sur de nouveaux clients, mesurer le
   coût métier et les biais avec labels ; le drift sans labels n'est pas une baisse de qualité.
3. Ajuster burn rates et fenêtres sur un historique de production suffisant, mesurer les
   faux positifs ; conserver une décision de gate indépendante des alertes.
4. Prévoir stockage durable/haute disponibilité et contrôler l'accès aux caractéristiques
   sensibles ; mesurer la complétude des logs avec des identifiants adaptés avant toute garantie.

Pistes discutées uniquement : aucune extension d'architecture ni assouplissement des
seuils du professeur n'a été implémenté.
