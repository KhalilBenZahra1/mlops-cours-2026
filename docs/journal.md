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
