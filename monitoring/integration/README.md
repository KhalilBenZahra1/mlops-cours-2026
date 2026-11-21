# Intégration isolée du Lab 7 avant fusion

Déroulement demandé par le pilote : branche `lab/m7-integration` issue de
`lab/m7-observabilite`. Cette expérimentation réutilise le code du professeur, KServe,
les outils de trafic/analyse et la stack existante. Elle ne remplace pas les étapes
GitOps officielles en production. PR #12 et #13 restent ouvertes et inchangées.

## Périmètre et isolation

| Élément | Ressource d'intégration |
|---|---|
| Namespace / InferenceService | `scoring-integration` / `scoring-integration` |
| PodMonitor | `monitoring/scoring-api-integration`, namespace exclusivement d'intégration |
| Image API | `localhost:5001/scoring-api:m7-integration-db3668ce7ab8` |
| Dashboard / ConfigMap | UID `scoring-integration` / `scoring-integration-dashboards` |
| CronJob suspendu | `monitoring/scoring-drift-integration` |
| Groupe Pushgateway | `job="scoring-drift-integration"` |
| Label du calcul Evidently | `model="scoring-model-integration"` |
| Rapports S3 | `s3://monitoring/integration/drift-reports/` |
| Alertes / équipe | `ScoringIntegration*` / `ml-integration` |

Le label du calcul sert uniquement à isoler les séries de monitoring : le modèle reste
`scoring-model`, version lue dans les métadonnées ONNX, sans renommage du Registry ni
changement de seuil. Les sélecteurs du dashboard et des règles excluent production/staging.
Le job réutilise la référence DVC et le Secret S3 existants, sans versionner leurs valeurs.

## Construire et démarrer

Depuis la racine Linux du dépôt, vérifier le registre et l'absence de collision du tag :

```bash
curl -fsS http://localhost:5001/v2/scoring-api/tags/list
uv sync --locked
```

Le tag ci-dessus est déjà publié. Le réutiliser pour reproduire l'expérience ; si le
code embarqué change, choisir un nouveau tag et adapter les deux manifests d'ISVC.
La commande de construction utilisée est celle du Lab 4, modèle déjà exporté :

```bash
MODEL_VERSION=$(uv run python -c   'import json; print(json.load(open("packaging/model/metadata.json"))["model_version"])')
docker build -f packaging/Dockerfile   --build-arg VERSION=m7-integration-db3668ce7ab8 --build-arg MODEL_VERSION="$MODEL_VERSION"   -t localhost:5001/scoring-api:m7-integration-db3668ce7ab8 .
docker push localhost:5001/scoring-api:m7-integration-db3668ce7ab8
```

Ne pas reconstruire/pousser ce tag avec un contenu différent. Aucun accès MLflow requis.
Vérifier d'abord qu'un éventuel namespace existant correspond bien à ce test, puis :

```bash
kubectl kustomize monitoring/integration
kubectl apply -k monitoring/integration
kubectl wait -n scoring-integration --for=condition=Ready   isvc/scoring-integration --timeout=240s
kubectl apply -f monitoring/integration/candidate.yaml
kubectl get isvc -n scoring-integration
```

Le kustomization installe d'abord la stable à 100 %. Le second manifest crée une deuxième
révision à 10 % : même image, ONNX et seuil, seul `APP_VERSION` diffère. Ne pas réappliquer
la base pendant l'analyse : ce sont deux étapes de préparation, pas un overlay Argo CD.
L'état 90/10 concerne exclusivement l'intégration. Aucun manifeste de `k8s/` n'est modifié.

## Trafic et analyse en lecture seule

```bash
INT_HOST=$(kubectl get isvc scoring-integration -n scoring-integration   -o jsonpath='{.status.url}' | cut -d/ -f3)
uv run python monitoring/traffic.py --url http://localhost:30080   --host-header "$INT_HOST" --mode normal --duration 180 --rps 20 --seed 42
uv run python monitoring/canary_analysis.py --namespace scoring-integration   --isvc scoring-integration --prometheus http://localhost:9090 --window 5m   --out reports/m7/integration/canary-analysis
```

**Ne jamais ajouter `--apply` ou `--push`.** La commande GitOps suggérée par le script
du professeur vise les overlays de production ; elle est indicative et ne doit pas être
exécutée depuis cette expérience. Les mesures `increase()` sont des estimations sur cinq
minutes, distinctes du décompte exact des requêtes envoyées. Les P95 proviennent des buckets.
Les deux révisions du même modèle vérifient la chaîne technique ; cela ne prouve pas qu'un
nouveau modèle est meilleur ni qu'une promotion en production serait justifiée.

## Evidently, Loki et alertes

Les logs restent dans Loki, jamais dans Git. Le job relit les demandes HTTP effectivement
reçues dans ce namespace ; aucun fichier courant synthétique ni remplacement de métriques.

```bash
kubectl create job -n monitoring --from=cronjob/scoring-drift-integration   scoring-drift-integration-normal-NOUVEAU-NOM
kubectl logs -n monitoring job/scoring-drift-integration-normal-NOUVEAU-NOM
```

Choisir un nom inédit pour chaque exécution, sans écraser un job existant. Le CronJob est
suspendu, `CT_WEBHOOK_URL` et son token sont explicitement vides. Vérifier le job Complete,
les 20 séries de scores, le rapport S3, et le dashboard `scoring-integration` dans Grafana.

Le scénario de dérive par défaut du guide ne code aucune colonne dans un script :

```bash
uv run python monitoring/traffic.py --url http://localhost:30080   --host-header "$INT_HOST" --mode drift --factor 1.5 --duration 300 --rps 20 --seed 42
kubectl create job -n monitoring --from=cronjob/scoring-drift-integration   scoring-drift-integration-shift-NOUVEAU-NOM
```

Toutes les colonnes numériques de `dataset.yaml` sont multipliées par 1,5. Le job garde
les 5 000 demandes les plus récentes ; attendre assez de trafic pour éviter de mélanger
normal et dérivé. Les règles `ScoringIntegration*` utilisent les mêmes seuils/durées du
guide, une équipe distincte, et aucun label de déclenchement CT.

`alertmanager-test.yaml` est préparé et exclu du kustomization. Pour une notification
externe, demander d'abord au pilote une URL **webhook.site** et l'autorisation explicite
du test, puis créer le Secret `monitoring/integration-test-webhook` (clé `url`) hors Git.
Ne pas envoyer vers Slack ; ne pas appliquer le routage avant cette autorisation.
Aucune notification externe n'est nécessaire pour vérifier les états internes d'alerte.

## Validation officielle et suite

Lancer `make check-m7` avec ses valeurs de production, sans substituer le namespace
d'intégration pour obtenir artificiellement du vert. Les rapports officiels de canary
restent absents de `reports/m7/canary-analysis.*` tant que la démonstration de production
n'a pas eu lieu. Les preuves de cette expérience sont exclusivement sous
`reports/m7/integration/` ; les preuves antérieures restent intactes.

Après revue : fusionner #12 vers `main`, puis traiter #13 dans l'ordre convenu et cette
PR d'intégration après son parent. Aucun changement de base ou fusion n'est effectué
dans cette phase. Les opérations ultérieures nécessitent une nouvelle autorisation :
publication GHCR/staging, premier canary instrumenté de production, trafic et drift de
production, notification autorisée, CT puis analyse/promotion/rollback via GitOps.
Vérifier KFP actif et `KFP_HOST` sur 8082 avant tout CT. Ne pas contourner les protections.
