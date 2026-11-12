# Rapport — Lab 5 : serving avec KServe

Khalil Ben Zahra (@KhalilBenZahra1) · Option B : réalisation individuelle,
revue croisée avec @oumaimagorrab · Dataset : german-credit ·
Modèle : scoring-model v17 · Seuil servi : 0.3182.

## 1. Résumé

L'image FastAPI/ONNX du Lab 4 est déployée dans l'InferenceService
scoring-model, en mode Knative, derrière Kourier sur localhost:30080.
L'autoscaler KPA utilise une cible de 200 requêtes/s, avec 0 à 5 pods.
Après vérification du canary 90/10, l'image 2.0.0 reçoit 100 % du trafic ;
elle conserve le modèle v17 et ses prédictions.

Installation : le cluster existant a été conservé. Après des téléchargements
lents, l'application des configurations LLM a échoué sur TrustRemoteCode.
Les runtimes de scoring étaient installés et le contrôleur KServe prêt.
La finalisation a été effectuée manuellement : mise à zéro des contrôleurs
LLM/LocalModel inutilisés et installation de metrics-server à la version
prescrite dans infra/versions.env. Knative, Kourier, KServe et les métriques
ont ensuite été vérifiés.

## 2. Benchmark de latence

Requêtes POST /predict construites depuis dataset.yaml et test.csv.
Run 100 : un processus Locust, 2 minutes.
Runs 500 et 1000 : quatre processus, 3 minutes chacun.

| Run | Requêtes | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Erreurs (%) |
|---|---|---|---|---|---|---|
| run_100 | 52502 | 466.2 | 8 | 29 | 55 | 0.0000 |
| run_500 | 312416 | 1838.6 | 70 | 160 | 220 | 0.0042 |
| run_1000 | 306814 | 1806.0 | 300 | 460 | 560 | 0.0020 |

Le premier essai à 500 utilisateurs, avec un processus, a signalé une
saturation CPU de Locust : 1017.83 req/s et P99 de 670 ms.
Il est conservé dans reports/m5/single_process/. Le run retenu a été
réexécuté avec quatre processus, comme prévu par le guide.

Entre 500 et 1000 utilisateurs, le débit plafonne autour de 1800 req/s,
tandis que le P99 passe de 220 à 560 ms. C'est le plateau observé dans cet
environnement, sans preuve qu'un composant unique explique la saturation.
Les échecs sont 13 HTTP 502 au run 500 et 6 HTTP 502 au run 1000.

Les valeurs du tableau proviennent des CSV. Pour le run 100, le résumé
terminal affichait 52586 requêtes et P99=59 ms, contre 52502 et 55 ms dans
le CSV conservé ; cette différence de fin de collecte est signalée.

## 3. Scale-up observé

| Run | Pods maximum pendant le run | CPU moyen sous charge | Temps de montée |
|---|---|---|---|
| run_100 | Non relevé précisément | Non mesuré | Non mesuré |
| run_500 | Non relevé précisément | Non mesuré | Non mesuré |
| run_1000 | Non relevé précisément | Non mesuré | Non mesuré |

Un contrôle après les tests a confirmé DESIREDSCALE=5 et ACTUALSCALE=5,
avec cinq pods 2/2 Running et aucun redémarrage. Cette observation confirme
que la limite a été atteinte, sans fournir une mesure précise pour chaque run.
Les mesures CPU prises après la charge ne sont pas présentées comme des
moyennes sous charge. Des échecs de readiness sur le port 8012 ont été
observés ; leur lien causal avec les HTTP 502 n'a pas été établi.

Le scale-to-zero est vérifié : KPA à 0/0 et aucun pod avant le réveil.
La terminaison a commencé à un âge de pod de 79 s et le statut Completed
a été observé à 108 s. Ces âges ne mesurent pas exactement le délai depuis
la dernière requête.
Premier appel /health à froid : HTTP 200 en 7.320275 s.
Second appel à chaud : HTTP 200 en 0.003702 s.

## 4. Analyse canary

Sur 200 réponses /metadata : 181 proviennent de 1.0.0 et 19 de 2.0.0,
soit 90.5 % / 9.5 %. L'écart d'une réponse par rapport à 180/20 est cohérent
avec un routage probabiliste 90/10.

Les adresses latest et prev ont été testées. La v2 répond version=2.0.0
et model_version=17 ; les deux images conservent le seuil 0.3182.
Le test local v2 et le test après promotion renvoient les mêmes probabilités
et décisions que la v1 sur les deux demandes utilisées.

Décision : promotion manuelle à 100 %. L'InferenceService est Ready et
la révision 00003 reçoit tout le trafic. Le manifest canary conserve le
scénario 90/10 ; la promotion a été appliquée par kubectl patch, conformément
au guide. Elle n'est pas automatisée par GitOps.

## 5. Points d'amélioration

- Enregistrer les pods, le CPU et les horodatages pendant chaque run pour
  mesurer précisément le temps de montée et les moyennes sous charge.
- Examiner les HTTP 502 et les échecs de readiness avec des logs corrélés.
- Comparer différents scaleTarget, le scaling par concurrence et le batching.
- Répéter les benchmarks dans des conditions identiques avec plusieurs
  processus Locust, en surveillant aussi la consommation du générateur.
- Automatiser la surveillance du canary et le rollback dans les labs suivants.

Les comparaisons optionnelles Triton/BentoML et le bonus batch ne sont
pas réalisés dans ce rapport.
