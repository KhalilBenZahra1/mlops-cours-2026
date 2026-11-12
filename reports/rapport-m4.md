# Rapport — Lab 4 : packaging du modèle

Khalil Ben Zahra (`KhalilBenZahra1`) · Option B : réalisation individuelle et revue croisée · Dataset : `german-credit` · 10 novembre 2026.

Champion résolu au début du lab : `scoring-model` **v17**, run `7bf737a9c38b43b5b7c0c9bce7d92ab9`. Seuil du paramètre `decision_threshold` : **0.3182**, sans calcul de repli ni réentraînement. Les comparaisons chargent cette version exacte, même si l’alias change ensuite. SHA-256 ONNX : `abeed68fd420def11ac6b63af11d2ae77a315612bf4a84a2aed520402baf4ed7`.

**Validation finale : `make check-m4` — 16/16 vérifications OK le 10 novembre 2026. Les trois images sont construites, les scans Trivy sont terminés et l’image optimisée est publiée puis récupérée depuis le registry local.**

## 1. Comparatif des tailles

Les tailles ci-dessous reprennent les valeurs arrondies affichées par Docker : contenu et occupation disque sont distingués. Pour l’image optimisée, `.Size` vaut exactement 106 797 737 octets ; le contrôle officiel affiche 106 Mo. Son utilisateur réel 10001:10001 a été vérifié. Les totaux HIGH/CRITICAL proviennent des rapports texte Trivy et ne représentent pas nécessairement des identifiants CVE distincts.

| Image | Contenu Docker affiché | Disque Docker affiché | HIGH | CRITICAL |
|---|---|---|---|---|
| `scoring-api:naive` | 572 MB | 2.14 GB | 313 | 15 |
| `scoring-api:optimized` | 107 MB | 458 MB | 49 | 0 |
| `scoring-api:bentoml` | 358 MB | 1.41 GB | 104 | 0 |

La baseline suit `python:3.12`, `COPY . /app` et une installation non épinglée. Pour ne jamais embarquer de vrais secrets, elle est construite depuis une copie temporaire contrôlée : fichiers suivis, code de packaging et trois CSV publics, sans `.git`, credentials locaux ni environnement virtuel. Son `.env` est factice ; les littéraux d’identifiants déjà présents dans certains fichiers suivis sont remplacés uniquement dans cette copie. Le dépôt et les contrôles officiels restent intacts. L’image naïve reste locale.

## 2. Comparatif des latences

Intel Core i7-13620H, 16 CPU logiques, WSL2 Ubuntu 24.04, Python 3.12.15, NumPy 2.5.3, scikit-learn 1.9.1, ONNX Runtime 1.30.0. Chaque backend effectue 10 chauffes puis 1 000 mesures ; modèle et entrées chargés avant le chronométrage.

| Backend | P50 (ms) | P95 (ms) | P99 (ms) |
|---|---|---|---|
| sklearn_pipeline | 4.653 | 7.619 | 11.871 |
| onnx_python | 0.077 | 0.118 | 0.231 |
| onnx_batch_100 | 0.347 | 0.652 | 1.000 |

L’accélération P50 sur une ligne est **×60.1**. `onnx_batch_100` mesure le lot entier de 100 lignes, pas une ligne. Ces microbenchmarks excluent HTTP, le chargement et la préparation des entrées. Des services Docker et téléchargements tournaient en arrière-plan : ce résultat unique ne constitue pas une garantie de performance en production. Le scénario Locust est fourni ; le test de charge optionnel n’a pas été exécuté.

## 3. Interprétation

L’export conserve le prétraitement complet et adapte une copie du pipeline aux contraintes ONNX. Sur les **200 lignes** de test, l’écart maximal des probabilités est **8.73351403419e-08**, inférieur à 10⁻⁴, avec **100 %** de décisions identiques au seuil exporté. L’exécution du graphe ONNX réduit ici le coût des appels Python du pipeline scikit-learn.

L’image optimisée utilise une base slim et un build multi-stage : seules les dépendances d’inférence, le contrat, le serveur, l’ONNX et ses métadonnées sont copiés. Pandas est nécessaire à l’import de `src/dataset_config.py`. MLflow, scikit-learn et les outils d’export sont exclus du runtime. Un téléchargement NumPy tronqué (5,1/16,7 Mo) a été rejeté par pip : l’empreinte attendue correspond bien à `uv.lock`. Les délais ont été augmentés et pip 25.2 a été épinglé comme outil d’installation pour sa [reprise automatique](https://discuss.python.org/t/announcement-pip-25-2-release/100716), uniquement dans le builder optimisé et dans la baseline. Les versions des dépendances de serving et leurs contrôles d’intégrité restent inchangés ; cette correction ne concerne pas le runtime optimisé.

Le premier build optimisé occupait 535 Mo dans la liste Docker, malgré une inspection à 125 Mo. Pour respecter la limite sans ambiguïté, 52 536 183 octets de bytecode ont été retirés du builder avant copie dans le runtime ; les fichiers source et bibliothèques restent présents. L’image finale occupe 457 969 398 octets sur disque (106 797 737 via l’inspection). Son API et son état Docker `healthy` ont été revérifiés après reconstruction, ainsi que son fonctionnement avec `--network none`, l’absence de credentials et des bibliothèques d’export, et les quatre variables de configuration.

Le build BentoML standard a échoué sur des connexions Debian HTTP. `packaging/bento/containerize.py` réutilise le contexte et le Dockerfile générés par BentoML 1.4.39 et ne modifie que la commande APT : mêmes paquets, transport HTTPS, délais et retries. Cette adaptation est nécessaire ici, car le mode BentoML moderne ignore les templates Docker classiques. Le service, le modèle et la méthode de sérialisation restent ceux de l’énoncé.

Les tests HTTP locaux FastAPI couvrent les lots de 1, 3 et 200 lignes, les valeurs nulles, les métadonnées, `/health`, `/docs` et les refus 422 : colonne manquante, inconnue, types incorrects et lot invalide. L’API reproduit exactement ONNX sur le test complet. BentoML 1.4.39 utilise le même modèle et seuil ; ses prédictions concordent à 8.73e-08 près et ses décisions sont identiques. Ses requêtes invalides répondent **400**. Son store embarque un modèle scikit-learn sérialisé par joblib et ses dépendances supplémentaires.

Trivy 0.75.0 a analysé les trois images avec la même base conservée dans le volume `trivy-cache`, sans mise à jour entre les scans (`--skip-db-update`). Périmètre : vulnérabilités OS et bibliothèques, sévérités HIGH/CRITICAL. Les rapports sont `reports/trivy_optimized.txt`, `reports/trivy_naive.txt` et `reports/trivy_bentoml.txt`. La baseline présente 328 résultats, dont 15 CRITICAL ; BentoML en présente 104 HIGH ; l’image optimisée 49 HIGH et aucun CRITICAL. L’optimisation réduit ici les résultats détectés mais ne supprime pas toutes les vulnérabilités. Les dépendances non épinglées de la baseline diffèrent aussi de celles du runtime optimisé : la comparaison ne mesure donc pas uniquement l’effet de la base slim.

ModelScan 0.8.8 détecte **1 CRITICAL**, l’opérateur `posix.system` du pickle de démonstration ; les deux pickles générés n’ont jamais été chargés et sont exclus de Git. Le scan ONNX renvoie **3**, avec un fichier ignoré : « No issues found » ne signifie donc pas que le modèle a été analysé. Le skops du Registry donne aussi le code **3**, mais révèle 11 erreurs sur ses membres NumPy (`numpy.lib.format._check_version` absent), et 12 éléments ignorés. Cette incompatibilité avec NumPy 2.5.3 limite l’analyse ; elle n’est pas masquée. L’inspection statique skops demande le type `numpy.dtype`. Un graphe ONNX évite la désérialisation arbitraire d’un pickle, sans constituer une garantie absolue contre toute vulnérabilité du runtime ou du modèle.

## 4. Choix recommandé

Pour ce scoring, l’API FastAPI/ONNX est le choix retenu : équivalence mesurée, faible latence et séparation de l’entraînement et du serving. Son contrat strict, son utilisateur numérique et son healthcheck sont adaptés aux labs suivants. La construction, la santé Docker et les prédictions sont validées ; les 49 résultats HIGH restent à examiner avant un déploiement de production. BentoML apporte un store et un packaging intégrés, mais conserve ici la sérialisation scikit-learn ; la baseline sert à illustrer le coût d’une base complète, de root et d’un contexte trop large.

L’image `localhost:5001/scoring-api:1.0.0` a été poussée puis récupérée. Son digest est `sha256:15a39bd92b977807e5e30fce260317d74bb7e760adfbbc3580a5f30f3eddb7ae`. Le contrôle officiel valide son démarrage, son état healthy, ses endpoints et le refus HTTP 422.

## 5. Pistes d’amélioration

Pour une évolution ultérieure, étudier une quantification en revérifiant probabilités et décisions, une base plus minimale compatible avec les dépendances natives, et l’épinglage des digests de base. Ajouter une politique de mise à jour des CVE, une signature d’image et un SBOM après analyse des rapports. Répéter les mesures dans un environnement isolé et sous une charge représentative avant de dimensionner le service. Ces pistes ne sont pas implémentées dans ce lab.
