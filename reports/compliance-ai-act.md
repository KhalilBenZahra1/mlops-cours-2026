# Rapport de conformité — AI Act et RGPD — scoring-model v19

Équipe : Khalil Ben Zahra et binôme du dépôt.
Date : 21 novembre 2026.
Système : API scoring, InferenceService scoring-model, namespace scoring.
Statut : audit pédagogique ; aucune conformité pour un usage bancaire réel revendiquée.

## 1. Classification du risque

Le projet reste un exercice pédagogique sans décision sur de vrais demandeurs.
Le nom « production » du namespace ne constitue pas une mise sur le marché.

Pour un usage réel relevant du champ territorial européen, l'évaluation de
solvabilité de personnes physiques relève du haut risque : AI Act, article 6
et annexe III, point 5 b, hors détection de fraude.

Selon le calendrier officiel consulté le 21 novembre 2026, les règles haut risque
de l'annexe III s'appliquent le 2 décembre 2027 après modification du règlement.
Les dispositions générales et interdictions s'appliquent depuis février 2025.

Le RGPD reste distinct : article 22 pour les décisions exclusivement automatisées
significatives, avec exceptions et garanties ; article 35 pour l'analyse d'impact
lorsque les conditions sont réunies. Le report AI Act ne reporte pas le RGPD.

## 2. Checklist AI Act

Les éléments ci-dessous sont des contributions techniques, pas une certification.

| Obligation | Réponse du projet et limite | Preuve |
|---|---|---|
| Gestion des risques, art. 9 | Audits et garde-fous ; processus organisationnel incomplet | Model Card, rapports de sécurité et canary du Lab 7 |
| Données, art. 10 | Contrat, validation, groupes sensibles ; données anciennes peu représentatives | dataset.yaml, fairness_baseline.json |
| Documentation technique, art. 11 | Modèle, seuil, provenance et limites documentés | ../model-card/model-card.md |
| Journalisation, art. 12 | Journaux JSON et collecte Loki ; conservation durable non démontrée | rapport-m7.md, ../monitoring/ |
| Transparence, art. 13 | Explications globales/locales ; compréhension par des clients non évaluée | explanations_local.md, shap_importance.json |
| Contrôle humain, art. 14 | Relecture Git et gate ; aucun parcours bancaire de recours opérationnel | rapport-m7.md, Model Card |
| Exactitude, robustesse, cybersécurité, art. 15 | Métriques, scans, image durcie, RBAC et ESO ; vulnérabilités résiduelles | m8/model-card-metrics.json, trivy_distroless.txt, manifests Kubernetes |

## 3. Preuves produites

- trivy_full.txt et trivy_critical.txt : baseline, dont 51 occurrences HIGH.
- trivy_distroless.txt : 19 occurrences HIGH, aucune CRITICAL.
- m8/trivy-distroless.json : détail du scan durci.
- modelscan_pickle.txt et modelscan_pickle.json : opérateur posix.system détecté.
- modelscan_onnx.txt : format ignoré, code 3 ; aucune certification ONNX déduite.
- m8/skops-types.txt : numpy.dtype signalé hors liste de confiance.
- fairness_baseline.json et .txt : champion 19, seuil 0,3182, trois attributs.
- fairness_mitigated.json et .txt : comparaison des stratégies et proxies.
- shap_summary_bar.png, shap_beeswarm.png, shap_waterfall_*.png :
  importance globale et trois cas locaux.
- explanations_local.md : motifs et tests de changement d'attribut sensible.
- ../model-card/model-card.md : identité, usages, résultats et limites.
- ../k8s/rbac-scoring.yaml : identité et droits minimaux.
- ../k8s/overlays/prod/kustomization.yaml : ServiceAccount prévu par Git ;
  appliqué en production par Argo CD après fusion de la PR #17.
- ../k8s/mlflow-creds-source.yaml : synchronisation ESO sans valeur secrète.
  SecretStore prêt, clés identiques et recréation du Secret vérifiés sur le cluster.

## 4. Écarts identifiés

Données historiques, seulement 200 demandes de test, groupes de 6, 9 et 12 personnes.
Ratios d'acceptation inférieurs à 0,8 pour les trois attributs ; ce seuil de
dépistage n'est pas une preuve juridique de discrimination.
Les tests contrefactuels du cas 807 montrent des bascules de décision ;
SHAP explique le modèle, sans démontrer une causalité.

Aucune atténuation déployée ; les comparaisons sur le test ne remplacent pas
une évaluation indépendante. Le champion reste en version 19.

Vulnérabilités résiduelles et écart setuptools non expliqué :
Trivy annonce 70.3.0, métadonnées inspectées 84.2.1.
Le ServiceAccount scoring-sa est appliqué en production ; aucun volume
kube-api-access n'a été trouvé dans le pod vérifié. Contrôle officiel : 29/29.

Absence de procédure réelle d'intervention humaine et de contestation,
d'analyse d'impact formelle, de validation juridique et organisationnelle,
de politique de conservation probante et d'audit indépendant.
La relecture des PR ne remplace pas la supervision des décisions de crédit.

## 5. Recommandations

Avant tout usage réel, qualifier les rôles et obligations avec les responsables
juridiques et protection des données. Prévoir une AIPD adaptée au traitement
et l'analyse des droits fondamentaux prévue par l'article 27 pour les déployeurs
de scoring concernés, ainsi que les formalités d'enregistrement applicables.

Valider sur des données récentes et représentatives, avec un test indépendant.
Examiner les intersections, les petits groupes, les proxies et les préjudices.
Choisir une atténuation selon plusieurs critères, avec validation humaine.

Mettre en place information compréhensible, recours et intervention humaine
effective. Définir conservation, accès, sécurité et surveillance après déploiement.
Traiter les vulnérabilités, tracer les digests et maintenir les vérifications du ServiceAccount et de l'absence de jeton
à chaque nouvelle révision. Prévoir des revues périodiques et lors des changements.

## Sources

Sources officielles consultées le 21 novembre 2026 :

- [AI Act consolidé : articles 6, 9–15, 27 et annexe III](https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng)
- [Calendrier officiel de la Commission européenne](https://ai-act-service-desk.ec.europa.eu/en/ai-act/eu-ai-act-implementation-timeline)
- [RGPD : notamment articles 22 et 35](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
