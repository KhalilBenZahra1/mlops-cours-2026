# Rapport — Lab 6 : CI/CD/CT de bout en bout

**Rapport intermédiaire — démonstration de bout en bout incomplète.** Observations du 20 novembre 2026, avant les fusions des quatre PR dépendantes.

Pilote : Khalil Ben Zahra (`KhalilBenZahra1`), option B et revue croisée du binôme. Fork : `KhalilBenZahra1/mlops-cours-2026`. Dataset : `german-credit`. Production préservée : `localhost:5001/scoring-api:2.0.0`, modèle **17**, révision `scoring-model-predictor-00003`, trafic **100 %**. Registry après CT : `@champion` et `@challenger` **18**, version 17 conservée.

## 1. Architecture

Le flux prévu par le guide est : développeur → GitHub ; Actions construit et pousse dans GHCR puis commite le tag staging dans Git ; Argo CD tire Git et KServe tire les images. Evidently pousse un événement authentifié au webhook, qui soumet un run KFP ; KFP lit le lot étiqueté dans MLflow, entraîne, évalue et enregistre un challenger. La gate déplace l'alias MLflow si les règles réussissent. La publication du modèle, le commit GitOps et le canary complètent ensuite le cycle.

Exécuté : CI de PR #7 verte (lint/tests et build/smoke) ; Argo CD **v3.5.3**, quatre pods prêts, réconciliation 60 s ; manifests acceptés en dry-run serveur ; détection, webhook et CT réels. KFP utilise `http://localhost:8082`, Argo UI `https://localhost:8443`, MLflow `http://localhost:5000`.

Non exécuté : publication GHCR sur `main`, activation des Applications et adoption GitOps. `main` reste `a14ed12` et ne contient pas les overlays. Les Applications visent bien `main`, avec auto-sync, prune et selfHeal ; elles restent non appliquées pour éviter de tirer le tag de gabarit staging `0.0.0` inexistant. La production du Lab 5 reste opérationnelle. Les déclencheurs du workflow sont inchangés : publication après fusion, sans contournement par dispatch.

## 2. Temps du cycle

Horodatages **UTC**, issus du webhook et de l'API KFP. La préparation a simulé un facteur 1,5 sur trois variables numériques configurées ; Evidently a détecté **15 %** de variables en dérive.

| Étape | Début UTC | Fin UTC | Durée |
|---|---|---|---|
| Détection seule, rapport et stockage MLflow | 20:51:05,090 | 20:51:14,074 | 8.984 s |
| POST authentifié → accusé de soumission KFP | 20:52:13,473 | 20:52:14,545 | 1.072 s |
| Pipeline CT, ingest → gate | 20:52:14 | 20:55:55 | **221 s** |
| Commit du modèle → image publiée | Non exécuté | En attente des fusions | Non mesuré |
| Image publiée → staging servi | Non exécuté | En attente GHCR/Argo | Non mesuré |
| Canary 10 % → promotion 100 % | Non exécuté pour le CT | En attente de publication | Non mesuré |
| **Cycle complet** | **Démo partielle** | **Non terminé** | **Non mesuré** |

La détection a été lancée avec `--no-send`, puis l'événement enregistré a été envoyé séparément : l'attente entre les deux commandes ne mesure pas la latence automatique. Ces durées ne sont donc pas additionnées pour prétendre mesurer le cycle complet. KFP domine les segments mesurés, mais une seule exécution ne permet pas de conclure sur le goulot global. Les temps des tâches et les téléchargements devront être examinés avant toute optimisation.

## 3. Gates et décisions

Run KFP `2698026a-2258-475e-88ce-9866032d1104`, nom `ct-evidently-drift-20261120-215214` : **SUCCEEDED**, sept tâches réussies (`ingest-ct-data`, `validate-data`, `prepare-features`, `train-model`, `evaluate-model`, `register-challenger`, `promotion-gate`). Validation GX réussie avant préparation. Run d'entraînement MLflow `a902bebbdde241ea87a32bc744279ee2` ; rapport de drift et lot dans `runs:/61cba61414724aa7b4c4469e41ca3f30/batch/current.csv` et `runs:/61cba61414724aa7b4c4469e41ca3f30/drift_report.html`. Le modèle 18 porte `kfp_run_id`, `ct_trigger=evidently-drift`, `ct_drift_share=0.1500`, `previous_champion=17`, `promotion=passed`.

Comparaison de gate sur les **mêmes données récentes** :

| Modèle | ROC AUC | Coût métier |
|---|---:|---:|
| Ancien champion 17 | 0,8050 | 124 |
| Challenger 18 | 0,8094 | 108 |

Règles du contrat : ROC AUC ≥ 0,70 et coût challenger ≤ coût champion. Les deux passent ; la gate promeut réellement la version **18**. Seuil de décision lu dans le run : **0,3182**. Ce résultat Registry ne signifie pas une mise en production : `CT_AUTO_RELEASE=0`, aucun export ni commit automatique ; ONNX et métadonnées versionnés inchangés. Le canary du nouveau modèle et sa décision restent **en attente**, sans extrapoler la démonstration du Lab 5.

Contrôle final réel : **Résultat : 11/18 vérifications OK**, `make` retourne **2** (sept échecs, code du script 7), sans contrôle ignoré. Référence initiale avant Argo/CT : **4/18**.

Les contrôles acquis couvrent les fichiers, le schéma Actions, lint/tests, les deux rendus Kustomize, Argo prêt, webhook joignable, MLflow CT, run KFP réussi, contrat sans colonnes codées en dur, jeton hors Git et structure du rapport. Les sept contrôles restant à démontrer concernent la CI sur `main`, les Applications Synced/Healthy, staging, la gestion GitOps de prod, le tag servi conforme à Git, le champion CT servi et l'historique des commits automatiques. Ce sont des validations bloquées par les fusions/publications, pas des résultats positifs. La structure du rapport peut passer son contrôle alors que la démonstration reste incomplète.

Non-régression réelle après CT : `check-m5` **14/14**. Lint et **57 tests locaux réussis** ; checkout sans `.env`, DVC, MLflow ni cluster : **49 réussis, 8 tests comportementaux ignorés** faute de modèle DVC, tous exécutés avec succès dans l'environnement local. CI distante de #7 : **44 réussis, 8 ignorés**, build et smoke réussis ; les cinq tests CT arrivent dans les PR suivantes.

## 4. Points d'attention

Le webhook est lié à `127.0.0.1:8095`. Le jeton aléatoire reste dans `.env` ignoré : sans jeton, **401** ; avec jeton, **202**. Aucun secret n'est versionné. La publication automatique est désactivée et le pilote conserve la décision de fusion après revue du binôme. Cette exécution s'arrête au Registry, conformément au déroulement adapté.

Un retour arrière complet doit distinguer trois états : trafic KServe, alias MLflow et image déclarée dans Git. Après le CT, l'alias est 18 tandis que le service reste volontairement sur 17 ; un alias seul ne change pas l'ONNX embarqué. Les contrôles ont confirmé le même spec, la même révision et les mêmes empreintes des fichiers modèle. Aucun cluster, volume, bucket, historique ou service existant supprimé. L'installeur Argo a seulement nécessité le bit exécutable manquant ; son contenu et les contrôles officiels sont inchangés.

## 5. Différences avec la prod

Le lot récent est **simulé et étiqueté** depuis le dataset du cours : il prouve le mécanisme, pas l'efficacité sur un changement réel de population. Les décisions sont fondées sur un échantillon unique, sans estimation d'incertitude ni suivi des labels retardés. Les horodatages mesurés dépendent de ce poste WSL2/Docker Desktop et de sa connexion. Le webhook conserve son état en mémoire ; ce lab ne démontre pas une reprise durable après panne.

En production, il faudrait discuter des secrets managés, d'une identité limitée pour le bot, de PR de release plutôt que de commits directs, d'environnements séparés, d'audit, de reprise et de métriques métier. Ces pistes ne sont pas implémentées ici. Le code et l'architecture du professeur sont conservés.

Ordre des PR : **#7 cicd → main**, **#8 argocd → cicd**, **#9 ct → argocd**, puis **rapport → ct**. Après revue, fusionner successivement et ajuster chaque base vers `main` une fois le parent fusionné. Préserver les tags staging générés par la CI lors de la résolution d'éventuels conflits. Après publication GHCR accessible : appliquer les Applications, vérifier Synced/Healthy et selfHeal, terminer le parcours contrôlé de publication/canary, relever le temps complet puis relancer `make check-m6`. Aucune fusion ou poussée directe sur `main` effectuée dans cette séance.

## 6. Captures d'écran

Captures authentiques à réaliser dans l'environnement du pilote : run KFP ci-dessus avec sept tâches vertes et tableau de gate ; MLflow version 18, tags et alias ; Actions de #7, run `44811547598` vert ; terminal montrant les quatre pods Argo prêts et `check-m5` 14/14.

Captures **encore impossibles avant les fusions** : Applications Argo Synced/Healthy, Actions de publication sur `main`, staging prêt avec image GHCR et canary du modèle CT puis promotion. Elles seront ajoutées après la démonstration, ainsi que la validation finale complète. Aucune capture ni sortie de validation n'est fabriquée.
