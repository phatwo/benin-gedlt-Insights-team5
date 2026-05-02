# Données
Les données sont stockées sur Google Drive partagé. 

| Fichier | Lignes | Description |
|---|---|---|
|`Data.csv` | 23859 | Dataset initial provenant de BigQuery |
| `beninwatch_clean.csv` | 15 203 | Dataset purifié — prêt pour l'analyse |
| `beninwatch_rejected.csv` | 8 656 | Événements rejetés avec traçabilité |
| `beninwatch_rejection_log.csv` | 6 | Synthèse par couche de filtrage |

## Pipeline de séparation (Bénin City et République du Bénin)
- **Couche 1A** : 1 356 lignes ( mots-clés Benin City dans URL)
- **Couche 1B** : 809 lignes (acteurs Benin City/Edo détectés ) 
- **Couche 2** : 5 090 lignes (score de confiance négatif)
- **Couche 3** : 1 401 lignes (scraping contenu + pré-filtre)
- **Taux de décontamination** : 36.3% du dataset initial rejeté


# Mention concernant l'usage de l'IA
> Ce travail a été réalisé avec l'assistance de Claude qui a été utilisé surtout  pour
> l'écriture du code. Ces codes ont été ensuité vérifiés. Les idées et la conception des 
> pipeline sont bien de notre fait.
