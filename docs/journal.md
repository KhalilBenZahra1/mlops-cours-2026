# Journal de bord du binôme

<!--
Mode d'emploi (à garder en tête du fichier) :
- Une entrée par séance (et par session de travail importante hors séance), la plus récente en bas.
- 3 à 5 lignes : qui a piloté, ce qui a été fait, ce qui a bloqué ou ce qui a été appris,
  la prochaine étape. Pas de roman : c'est un outil de pilotage, pas un rapport.
- Titre d'entrée au format exact « ## S<n> — AAAA-MM-JJ — <sujet> » (date réelle) :
  le pré-contrôle de rendu (make check-m10) compte les entrées datées.
- Liez les PR, issues et ADR (#12, docs/adr/0003-...). Les problèmes non résolus restent
  visibles : c'est précisément ce qui aide l'enseignant à vous débloquer.
- L'entrée d'exemple ci-dessous (date AAAA-MM-JJ) n'est pas comptée ; supprimez-la
  quand vous aurez écrit la vôtre.
-->

**Binôme :** [À compléter : @pseudo-github-1 (Prénom Nom), @pseudo-github-2 (Prénom Nom)]
**Repo :** [À compléter : https://github.com/VOTRE_USER/mlops-cours-2026]
**Dataset :** [À compléter : german-credit (fil rouge) ou nom du dataset validé + lien de l'issue]
**Extensions :** [À compléter à la S8 : @pseudo-1 → ext/<nom> · @pseudo-2 → ext/<nom>]

## S0 — AAAA-MM-JJ — Exemple d'entrée (à supprimer)

- **Pilote / copilote :** @alice / @bob
- **Fait :** Lab 1 étapes 1 à 5 ; `dvc push` OK ; premier run MLflow dans l'expérience `scoring` (#3).
- **Bloqué / appris :** `dvc push` refusé (identifiants absents de `.dvc/config.local`, corrigé).
- **Prochaine étape :** Bob pilote le Lab 1 étapes 6-8 ; ouvrir l'ADR 0001 (métrique de promotion).

<!-- Vos entrées commencent ici. Modèle :

## S1 — AAAA-MM-JJ — Lab 0 : setup

- **Pilote / copilote :**
- **Fait :**
- **Bloqué / appris :**
- **Prochaine étape :**

-->

## 2026-10-12 — Lab 1 : versionner un projet ML end-to-end

- Données : contrat `dataset.yaml`, téléchargement et pipeline versionnés avec DVC ; sorties poussées vers le remote S3.
- Entraînement : préparation et évaluation reproductibles ; recherche de paramètres avec MLflow et modèle enregistré dans le Model Registry.
- Feature store : vue Feast `request_features` appliquée, extraction hors ligne comparée à `train.csv` et lecture en ligne vérifiée.
- Validation : `make check-m1` — 18/18 vérifications OK ; `make lint` passe ; `make test` passe avec 9 tests.

## S2 — 2026-10-27 — Lab 2 : Kubeflow Pipelines et Airflow

- **Pilote / copilote :** @KhalilBenZahra1 / Codex ; installation KFP débloquée manuellement par le pilote.
- **Fait :** image 1.0.1, six composants réutilisant src, deux runs KFP réussis avec cache vérifié ; deux runs Airflow réussis avec six tâches chacun ; probes de gate et de parallélisme exécutées.
- **Validé :** make check-m2 19/19, check-m0 19/19, check-m1 18/18 ; lint réussi et 15 tests réussis ; historique MLflow conservé.
- **Appris :** SDK KFP incomplet avec --no-deps ; ports 8082/8083 ; promotions concurrentes visibles dans les alias. Voir reports/rapport-m2.md et docs/adr/0001-reutiliser-image-pipeline.md (proposé).
- **Prochaine étape :** capture terminal authentique, commit/push des compléments par le pilote, puis revue croisée de la PR Draft existante sans fusion automatique.

## S3 — 2026-11-03 — Lab 3 : gates de validation

- **Pilote / copilote :** @KhalilBenZahra1 / Codex ; branche `lab/m3-validation` basée sur le Lab 2 (`3a71a24`), encore absent de `main` à l'audit.
- **Fait :** contrat GX figé depuis l'entraînement (67 expectations), drift KS/χ² + PSI et gate modèle (2 tests Evidently + 8 comportementaux) ; images 1.1.0 et 1.2.0 publiées ; trois scénarios KFP confirmés, rapports HTML téléchargés du SeaweedFS interne.
- **Validé :** `make check-m3` 20/20, contrôle final `check-m2` 19/19, contrôles M0 19/19 et M1 18/18 ; `make lint` et 23 tests réussis ; modèle 17 lié au run KFP à huit composants, aliases champion/challenger 17, ROC AUC 0,8094.
- **Bloqué / appris :** publication des ports Docker rétablie par redémarrage du seul control plane existant ; délais PyPI augmentés ; deux premiers scénarios arrêtés à l'ingestion par DNS transitoire, relances vérifiées au bon gate sans changer le code Lab 1. Voir [ADR-0002](adr/0002-gates-validation.md).
- **Prochaine étape :** revue croisée de la PR vers `main`, après prise en compte de la PR Lab 2 ; aucune fusion automatique.

## S4 — 2026-11-10 — Lab 4 : packaging du modèle

- **Pilote / assistance :** @KhalilBenZahra1 / Codex, puis finalisation manuelle.
- **Fait :** export ONNX du champion v17, API FastAPI, images naïve, optimisée et BentoML ; benchmark et scans ModelScan/Trivy ; push et pull de scoring-api:1.0.0.
- **Validé :** make check-m4 — 16/16 ; équivalence sur 200 lignes, écart maximal 8,73e-08 et décisions identiques ; image optimisée 458 MB sur disque, utilisateur 10001:10001 et healthy.
- **Mesures :** P50 sklearn 4,653 ms, ONNX unitaire 0,077 ms, lot de 100 lignes 0,347 ms ; accélération unitaire ×60,1.
- **Scans Trivy :** optimized 49 HIGH/0 CRITICAL ; naive 313 HIGH/15 CRITICAL ; BentoML 104 HIGH/0 CRITICAL.
- **Bloqué / appris :** téléchargements interrompus ; base Python récupérée par miroir avec digest identique ; installation pip avec reprise et APT BentoML en HTTPS. ModelScan ignore ONNX et rencontre une incompatibilité NumPy sur skops.
- **Prochaine étape :** commit, push et PR pour revue croisée du binôme.

## S5 — 2026-11-12 — Lab 5 : serving KServe

- **Pilote :** @KhalilBenZahra1 ; réalisation manuelle et revue croisée prévue avec @oumaimagorrab.
- **Fait :** déploiement FastAPI/ONNX avec KServe, Knative et Kourier ; KPA RPS de 0 à 5 pods ; trois charges Locust ; canary puis promotion de l'image 2.0.0.
- **Validé :** make check-m5 — 14/14 ; 36 tests réussis ; modèle v17 et seuil 0.3182 identiques à MLflow.
- **Mesures :** réveil à froid 7.320275 s, appel à chaud 0.003702 s ; cinq pods prêts observés après charge ; plateau autour de 1800 req/s. Temps de montée et CPU moyen sous charge non mesurés précisément.
- **Canary :** 181 réponses v1 et 19 réponses v2 sur 200 ; promotion à 100 %, prédictions conservées.
- **Bloqué / appris :** intégration Docker WSL et horloge rétablies ; téléchargements lents ; erreur TrustRemoteCode des configurations LLM, finalisation manuelle des étapes restantes de l'installation. Locust passé à quatre processus après saturation du générateur ; rares HTTP 502 conservés dans le rapport.
- **Prochaine étape :** revue croisée de la PR avant fusion.


## S6 — 2026-11-20 — Lab 6 : première PR, étapes 1–2

- **Pilote / assistance :** @KhalilBenZahra1 / Codex ; branche `lab/m6-cicd` issue de `main` (`a14ed12`, PR Lab 5 fusionnée).
- **Fait :** fixtures et mini-modèle ONNX du guide, tests API et Kustomize ; couverture des Labs 3–4 conservée, imports isolés entre mini-modèle et véritable ONNX versionné ; repli synthétique issu des domaines GX figés quand les données DVC sont absentes. Workflow `CI scoring` à trois jobs : lint/tests, build et fumée, puis publication GHCR et commit GitOps staging sur `main` après fusion. Starter `gitops.py` conservé, y compris `local-ci` ; Applications Argo CD préparées selon l'étape 1, sans application au cluster.
- **Validé :** `make lint`, `make test` (52 réussis), copie de checkout sans `.env`/DVC ni services accessibles (44 réussis, 8 comportementaux ignorés comme prévu sans modèle DVC), schéma GitHub Actions avec `check-jsonschema@0.38.2`, rendus staging/prod avec Kustomize 5.8.1 ; `make check-m5` 14/14. État et journaux de la CI distante consultables dans la PR.
- **Préservé / appris :** overlay prod identique au spec servi (image 2.0.0, trafic 100 %, révision 00003), ONNX et métadonnées inchangés ; 14 déploiements KFP disponibles, UI/API sur 8082 et `KFP_HOST` cohérent dans `.env` ignoré ; MLflow/S3 accessibles par les port-forwards du cours. SSH indisponible dans le terminal de contrôle : authentification `gh` existante utilisée temporairement en HTTPS, sans changer clés ou remotes.
- **Prochaine étape :** relecture et approbation du binôme, puis fusion par le pilote ; suivre la publication et le commit staging sur `main`, avant la phase Argo CD dans sa PR dédiée. Aucun CT ni déploiement GitOps exécuté ; validation complète `check-m6` réservée à la fin du lab. Aucune nouvelle décision d'architecture hors du guide.


## S6.2 — 2026-11-20 — Lab 6 : Argo CD, PR dépendante

- **Fait :** branche `lab/m6-argocd` issue de `lab/m6-cicd` ; Applications personnalisées, script d'installation rendu exécutable, docstring de serving de l'étape 5 mise à jour. Argo CD v3.5.3 installé par `make argocd`, quatre pods prêts, réconciliation 60 s ; identifiants masqués.
- **Validé :** lint et 52 tests réussis ; Applications acceptées en dry-run serveur ; production 2.0.0 à 100 % et modèle Git conservés. Contrôle initial réel `check-m6` : 4/18, avant Argo CD et CT.
- **Bloqué / décision de déroulement :** `main` ne contient pas les overlays et aucune image GHCR de staging n'est publiée ; Applications non activées pour préserver prod et éviter le tag de gabarit inexistant. Synced/Healthy, self-heal et déploiement par fusion restent à mesurer.
- **Livraison :** PR vers `lab/m6-cicd`, deuxième dans l'ordre cicd → argocd → ct → rapport. Retargetage vers `main` après fusion du parent par le pilote ; aucune fusion ni poussée directe sur `main`.


## S6.3 — 2026-11-20 — Lab 6 : CT isolé, PR dépendante

- **Fait :** branche `lab/m6-ct` issue de `lab/m6-argocd` ; webhook, pipeline CT et cinq tests du guide ajoutés, KFP sur 8082. Jeton seulement dans `.env` ignoré ; webhook lié à 127.0.0.1:8095, `CT_AUTO_RELEASE=0` ; refus HTTP 401 sans jeton et acceptation HTTP 202 authentifiée.
- **Validé :** lint et 57 tests réussis ; checkout sans DVC ni services : 49 réussis, 8 comportementaux ignorés ; pipelines scoring et CT compilés, sept composants CT. Dérive réelle : 15 % des variables, rapport et lot enregistrés dans MLflow (`61cba61414724aa7b4c4469e41ca3f30`).
- **Exécuté :** run KFP `2698026a-2258-475e-88ce-9866032d1104` SUCCEEDED, sept étapes réussies en 221 s ; run MLflow `a902bebbdde241ea87a32bc744279ee2`, modèle v18 promu par la gate, `previous_champion=17`. ROC AUC 0,8094 ; coût récent 108 contre 124 pour v17 ; seuil 0,3182 lu dans le run.
- **Préservé / en attente :** production 2.0.0 / modèle 17, ONNX et métadonnées Git inchangés. Les alias du Registry sont v18 après la gate ; aucun export ni commit automatique, aucune publication ou mise en production. Validation complète de promotion/serving attend les fusions et GHCR.
- **Livraison :** PR vers `lab/m6-argocd`, troisième dans l'ordre cicd → argocd → ct → rapport ; retargetage vers `main` après fusion du parent, sans modification des déclencheurs CI ni poussée directe sur `main`.


## S6.4 — 2026-11-20 — Lab 6 : rapport intermédiaire et état final des PR

- **Fait :** rapport en six sections du starter, temps réellement relevés et démonstration explicitement partielle. Branche `lab/m6-rapport` issue de `lab/m6-ct` ; aucun nouveau mécanisme ni changement de déclencheur CI.
- **Validé :** contrôle officiel `make check-m6` : **11/18 vérifications OK**, aucun SKIP ; code du script 7, code de Make 2. Fichiers, schéma Actions, lint/tests, overlays, Argo prêt, webhook, CT MLflow/KFP, contrat, jeton hors Git et structure du rapport passent. Référence initiale : 4/18. Non-régression après CT : `check-m5` **14/14** ; production et fichiers ONNX/métadonnées conservés.
- **Bloqué par le déroulement sans fusion :** CI sur `main`, Applications Synced/Healthy, staging GHCR, gestion GitOps de prod, tag servi conforme à Git, champion CT servi et historique des commits automatiques. `main` reste `a14ed12`. L'absence d'Applications actives évite le tag staging de gabarit inexistant ; aucun état non fonctionnel n'est déployé. Le rapport passe son contrôle structurel mais le Lab 6 n'est pas déclaré terminé.
- **Livraison / suite :** PR #7 cicd vers `main`, #8 argocd vers cicd, #9 ct vers argocd, puis rapport vers ct. Revue des quatre parties, fusions successives par le pilote et bases ajustées vers `main` après fusion du parent. Préserver les tags générés par la CI ; vérifier publication/accessibilité GHCR avant d'activer les Applications, puis selfHeal, publication du modèle CT, canary et cycle complet. Aucune fusion ni poussée directe sur `main` effectuée.


## S6.5 — 2026-11-20 — Lab 6 : fusions et cycle automatique validé

- **Livré :** approbations des PR #7, #8, #9 et #10 vérifiées ; fusions dans cet ordre, bases ajustées vers `main`, branches conservées et commits staging préservés. CI applicables réussies ; publication GHCR publique et pull réel depuis kind.
- **Argo :** deux Applications Synced/Healthy, adoption du spec de prod existant ; selfHeal 50 → 100 % en 2.01 s. Phase manuelle : modèle 18, image 2.1.7, canary 181/19 sur 200 appels sans erreur, promotion 200/200.
- **Cycle automatique :** run KFP `d538fecb-e59e-4d95-a5f0-76ebbd3a5037` SUCCEEDED, sept tâches ; modèle 19, run MLflow `f2d47c40fcfd4fe98b66a149ed010410`, champion précédent 18. Export/commit → CI/GHCR → staging → canary/50 prédictions → commit promotion sans intervention de déploiement ; durée observée 696.962 s. Production `ghcr.io/khalilbenzahra1/mlops-cours-2026/scoring-api:2.1.8` à 100 %, modèle 19 confirmé par `/version`.
- **Écart diagnostiqué :** scénario ×2 rejeté au gate GX, 14 durées et 18 âges hors bornes sur 1 000 lignes, tolérance 1 %. Aucun entraînement aval. Démonstration positive avec le scénario ×1,5 du guide, drift 15 %, contrat et seuils inchangés ; réussite du scénario ×2 exact non revendiquée.
- **Validé :** `make check-m6` **18/18**, code 0, aucun SKIP ; lint et 57 tests ; contrôles M0 **19/19**, M1 **18/18**, M5 **14/14**, équivalence ONNX/scikit-learn revérifiée. Contrôles officiels inchangés. Voir `reports/rapport-m6.md` et `reports/m6/` pour les preuves et limites de mesure.
- **Suite :** PR finale de documentation sur une nouvelle branche, à relire sans fusion automatique. Les services et historiques sont conservés ; aucune extension du Lab 7 commencée.


## S6.6 — 2026-11-21 — Lab 6 : captures finales et rendu de la PR #11

- **Fait :** cinq captures fournies par le pilote intégrées sans retouche dans `reports/rapport-m6.md`, avec chemins relatifs `m6/captures/` et légendes : Argo CD, KFP CT, GitHub Actions, production et `check-m6`. Ancienne mention d'absence de PNG actualisée ; PR #11 existante conservée, sans fusion.
- **Vérifié :** `kfp.png` montre le run `ct-evidently-drift-20261120-224035`, sept tâches réussies ; nom recoupé avec l'API pour l'UUID `d538fecb-e59e-4d95-a5f0-76ebbd3a5037`. Capture du Lab 6, pas du Lab 3. Images ouvertes et lisibles, aucun secret visible ni métadonnée textuelle PNG ; tous les liens locaux du rapport résolvent vers des fichiers existants.
- **Préservé :** mesures du cycle (696,962 s), preuves JSON/texte/Markdown et explication du rejet ×2 puis du cycle positif ×1,5 inchangées. Aucun ré-entraînement, déploiement, changement d'alias ou modification des contrôles.
- **Livraison :** vérification `git diff --check`, commit limité au rapport, au journal et aux cinq PNG, puis push sur `lab/m6-validation-finale` et actualisation de la description de #11. Captures distinctes du canary et de MLflow non fournies ; preuves existantes conservées. Relecture du binôme requise avant fusion.


## S7.1 — 2026-11-21 — Lab 7 : instrumentation, première PR

- **Fait :** API instrumentée selon le guide : `/metrics` direct, registre Prometheus propre au module, compteurs HTTP/décisions/groupes, histogrammes et informations du modèle ; journal JSON désactivable. Groupes issus de `dataset.yaml`, chemins inconnus et méthodes HTTP bornés pour éviter la cardinalité non contrôlée. Dépendance runtime `prometheus-client==0.24.1`, déjà présente dans `uv.lock` inchangé ; starters monitoring et 13 tests du professeur repris, quatre tests de protection ajoutés.
- **Validé :** `make lint` et `make test` : **74 réussis**, dont **17 tests monitoring** ; copie sans `.env`, données/modèle DVC, MLflow ni configuration Kubernetes : **66 réussis, 8 comportementaux ignorés**, sans nouveau SKIP. API temporaire réelle : 20 lots de 20 lignes du test, 220 décisions 0 et 180 décisions 1 ; 11 séries de groupes réparties entre les trois attributs sensibles ; `/metrics` HTTP 200 sans redirection, cinq requêtes invalides HTTP 422 et imputation des valeurs nulles conservée. Journal : 401 événements avec journalisation, zéro lorsque désactivée ; serveurs temporaires arrêtés.
- **Préservé :** modèle ONNX et métadonnées versionnés, seuil, contrats, verrou de dépendances, workflow et contrôles officiels inchangés. Production observée : image 2.1.8, modèle 19, révision 00006 à 100 % ; aucune nouvelle image déployée, aucun entraînement ni changement d'alias. PR #11 du Lab 6 laissée intacte.
- **Suite :** revue de la PR d'instrumentation et CI distante avant fusion. La partie observabilité sera une PR dépendante, sans fusion ni publication artificielle ; déploiement instrumenté, canary, drift et rollback réservés à l'après-fusion. `check-m7` complet ne peut pas encore être déclaré validé.


## S7.2 — 2026-11-21 — Lab 7 : stack et seconde PR dépendante

- **Fait :** `lab/m7-observabilite` créée depuis la première PR #12 après CI verte (lint/tests, build et smoke test) ; configurations du guide pour Helm, PodMonitor, dashboard, Evidently, alertes et routage, runbooks et rapport intermédiaire en six sections. Scripts monitoring rendus exécutables. Grafana utilise un Secret local ; variante officielle Ubuntu 13.2.3 nécessaire car la commande `test` du contrôle est absente de l'image distroless du chart, malgré le dashboard déjà chargé via API. Versions du chart et de l'application conservées ; contrôles officiels inchangés.
- **Validé :** quatre releases Helm du guide, **11 pods prêts**, interfaces HTTP disponibles et **18 panneaux Grafana** chargés ; six alertes et huit recording rules saines. Alloy transmet les logs d'accès existants à Loki. Référence DVC S3 vérifiée (800 lignes), sans reproduction. Image `localhost:5001/scoring-drift:1.0.0` poussée et réellement récupérée par un pod ; UID 10001, imports vérifiés. Job `scoring-drift-premerge-20261121` Complete : zéro demande JSON, aucun calcul de PSI, compteur zéro publié au Pushgateway ; aucun rapport HTML ou appel CT.
- **Tests / contrôles :** lint réussi, **78 tests réussis** ; copie sans secrets/DVC/services : **70 réussis, 8 comportementaux ignorés** comme auparavant. `check-m6` **18/18**, code 0. Premier `check-m7` **8/15** ; après correction légitime de la variante Grafana : **9/15**, script 6, Make 2. Preuves dans `reports/m7/verification-preparation.txt` et `preparation.json`.
- **Bloqué par le déroulement :** quatre contrôles attendent l'image instrumentée et le trafic réel (cible up, métriques métier, drift par variable et logs JSON). Notifications préparées, validées seulement en dry-run, sans Secret webhook ni envoi ; URL de test à demander au moment utile. Analyse canary différée. CronJob suspendu avant fusion ; webhook CT non configuré dans le job. Aucun entraînement, canary ou rollback ; le Lab 7 n'est pas déclaré entièrement validé.
- **Préservé / livraison :** production 2.1.8, modèle 19, seuil 0.3182, révision 00006 à 100 % ; spec, modèle ONNX, métadonnées, contrat, verrou et workflow inchangés. Argo staging/prod Synced/Healthy, KFP 14 déploiements disponibles sans pause, Airflow arrêté ; PR #11 inchangée. Seconde PR vers `lab/m7-monitoring`, à retargeter vers `main` après fusion de #12. Aucune PR fusionnée, aucun push direct sur `main` ; suivre ensuite publication staging, canary instrumenté, trafic normal et démonstrations sous contrôle du pilote.


## S7.3 — 2026-11-21 — Lab 7 : intégration isolée avant approbation

- **Périmètre autorisé :** branche `lab/m7-integration` issue de `lab/m7-observabilite`, sans fusion ni modification des PR #11/#12/#13. Image locale distincte `localhost:5001/scoring-api:m7-integration-db3668ce7ab8`, modèle 19 et seuil 0.3182 inchangés ; namespace/ISVC `scoring-integration`, deux révisions instrumentées du même modèle à 90/10, hors Applications Argo CD et overlays existants.
- **Observé :** trafic normal 3586 prédictions puis dérivé 5977, zéro erreur ; deux cibles up, JSON collecté par Loki/Alloy, 18 panneaux Grafana alimentés. Evidently : 3586 demandes normales sans drift (PSI max 0.129070), puis 5000 demandes récentes et 7/20 variables numériques en dérive avec le scénario par défaut ×1,5 du guide. Deux rapports HTML S3 vérifiés, métriques isolées `model=scoring-model-integration` / `job=scoring-drift-integration` ; aucun CT. Écart observé de 4 événements entre stdout et comptage Loki, cause non établie, documenté sans garantie de collecte sans perte.
- **Canary / alertes :** analyse en lecture seule sur trafic normal, six PASS, CONTINUE, P95 4.8/4.8 ms et PSI des scores 0,047 ; aucune commande GitOps appliquée. Sept alertes d'intégration Pending puis Firing et reçues par Alertmanager, seul receiver null ; aucun message externe. Routage webhook.site seulement préparé/dry-run, soumis à URL et autorisation future.
- **Validations :** lint et **83 tests réussis** ; copie sans secrets/DVC/services : **75 réussis, 8 comportementaux ignorés** comme auparavant. `check-m6` **18/18**, Make 0 ; `check-m7` officiel toujours **9/15**, script 6 / Make 2, sans substitution du namespace ou des rapports. Preuves et rapport sous `reports/m7/integration/`, sans journal brut de prédictions ; procédures sous `monitoring/integration/`.
- **Préservé / suite :** specs/révisions prod et staging, Applications, overlays, modèle ONNX, métadonnées, contrat, verrou et workflow inchangés ; production 2.1.8 / modèle 19 / révision 00006 à 100 %, KFP 14 déploiements disponibles, Airflow arrêté. Générateurs terminés, CronJobs suspendus ; environnement d'intégration conservé. Nouvelle PR vers `lab/m7-observabilite`, sans copie des PR parentes ni changement de leur base. Démonstration officielle de production et cycle CT/GitOps réservés à l'après-approbation et fusion.


## S7.4 — 2026-11-21 — Lab 7 : démonstration officielle, gate respecté et validation finale

- **Fusions / CI :** approbations et contrôles vérifiés ; #12, #13, #14 fusionnées dans cet ordre, bases retargetées vers main, branches conservées. Conflit du journal résolu sans perdre les ajouts du Lab 6 ; neuf fichiers du rendu Lab 6, dont cinq PNG, SHA-256 inchangés. CI main n°11/13/15 vertes, images GHCR et staging réellement vérifiés. Premier canary instrumenté 2.1.15 / modèle 19 promu après smoke test ; ancienne stable 2.1.8 sans métriques, aucune comparaison métrique fictive.
- **Observabilité officielle :** trois nœuds Ready, 11 pods monitoring prêts, 18 panneaux Grafana avec données, Prometheus UP par révision, trois attributs sensibles, JSON collecté par Loki/Alloy. CronJob officiel activé, historique porté à 20 jobs pour conserver les preuves. Référence DVC/S3 800 lignes ; 5 000 demandes normales : 0/20 drift, PSI max 0,136776. Scénario du guide age ×0,6 et credit_amount ×2,5 : 18 688 prédictions sans erreur, 2/20 drift, PSI 4,163755 et 1,458036. Rapports S3 relus et empreintes conservées ; retour normal 0/20.
- **Alertes / CT :** destination webhook.site autorisée, URL uniquement dans un Secret, aucun canal Slack contacté. Réponse du site de test passée à HTTP 200 / corps ok après diagnostic du rejet de la réponse HTML par le notifier ; FIRING et RESOLVED du test et du drift reçus. Calcul déclenchant CT relancé depuis le poste comme le guide, pas de lien automatique direct Alertmanager→CT. Webhook avec CT_AUTO_PROMOTE=0 ; KFP a052e470-2935-40d6-a687-f2175e33b88a SUCCEEDED, sept composants en environ 233 s. Modèle 20 / run 9ed81e39c7f34009a297653c505ce627 : gate REFUSÉE, coût réévalué 108 > 105 pour le champion 19, malgré AUC 0,8094 > 0,8026. Challenger 20 rejected/failed, champion 19 inchangé, aucune publication automatique du modèle 20. Sans lot récent étiqueté, source de repli src.download explicitement tracée ; aucune prédiction utilisée comme vérité terrain.
- **Canary / rollback :** repli de l'étape 10.2, workflow existant déclenché manuellement, CI n°16 verte : 2.1.16 avec le même champion 19. Six PASS à 10 % puis 50 %, commits GitOps jusqu'à 100 %. Canary défectueux 2.0.0 / modèle 17 : métriques 404, observabilité FAIL, décision ROLLBACK, code 1 attendu ; trafic 100/0 confirmé, alias inchangé. Bonne image 2.1.16 restaurée à 100 %, révision 00010, modèle 19, seuil 0,3182 ; Argo staging/prod Synced/Healthy. Promotion de modèle CT non revendiquée : refus du gate préservé.
- **Validation / livraison :** make check-m7 15/15, check-m6 18/18, check-m5 14/14, codes 0 ; lint et 83 tests locaux réussis. Copie autonome / CI : 75 réussis, 8 comportementaux ignorés comme auparavant. Contrôles officiels, ONNX, métadonnées et seuil inchangés ; environnement d'intégration conservé, KFP 14 déploiements disponibles, Airflow arrêté. Preuves agrégées sous reports/m7/official/, rapport en six sections actualisé. PNG non produits : URLs et fenêtres réelles de capture documentées. Branche finale et PR de rendu séparées, à relire sans fusion automatique ; aucune donnée brute ni secret versionné.
