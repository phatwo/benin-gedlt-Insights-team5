# Dahomey Intel : système d'alerte précoce et de veille géopolitique

> **Projet développé dans le cadre du Hackathon iSHEERO × DataCamp Donates 2026 — Bénin Insights Challenge.**

**Dahomey Intel** est une solution d'intelligence décisionnelle qui transforme le flux massif des données mondiales GDELT en un instrument de souveraineté pour la République du Bénin. Notre système détecte les signatures numériques des crises pour offrir aux décideurs un temps d'avance sur l'instabilité.

## Problématique
Les décideurs béninois (ministres, journalistes, chercheurs) font face à un angle mort informationnel. La quantité énorme d'articles écrits par les pays du monde entier empêchent d'avoir une vue globale de la perception du Bénin à l'extérieur.  Comment avoir une vue objective du Bénin, non seulement du point de vue des médias locaux, mais aussi des médias extérieurs pour en tirer des décisions efficaces ?  

**Dahomey Intel** répond à ce défi par :
*   Un **indice de stabilité (0-100)** calculé quotidiennement.
*   Un **détecteur d'anomalies** basé sur l'IA (XGBoost).
*   Un **système d'alerte précoce** identifiant les ruptures de tendance avant qu'elles ne deviennent critiques.
  Le tout intégré dans un dashboard interactif permettant de filtrer suivant la période désirée.


## 2. Architecture Technique

Le projet respecte une structure modulaire en trois couches :

### A. Pipeline de données (Data Engineering)
*   **Source :** Extraction de 14 897 événements GDELT 2.0 via Google BigQuery en utilisant le code SQL suivant : 

*   **Purification du Signal :** 
    *   **Désambiguïsation géographique :** Implémentation d'un algorithme de nettoyage contextuel pour éliminer la pollution liée à *Benin City (Nigeria)*, un biais majeur identifié dans les données brutes.
    *   Gestion des valeurs manquantes selon leur gravité et les objectifs.
    *   Seuil de résonance médiatique (NumArticles ≥ 3).

### B. Modèle pour la prédiction (Machine Learning)
Notre approche initialement basée sur une régression linéaire a évolué finalement vers une classification binaire de détection d'anomalies pour maximiser la performance.
*   **Algorithme :** XGBoost Classifier optimisé par `GridSearchCV` et `TimeSeriesSplit`.
*   **Feature Engineering :** 
    *   **Stress index :** Mesure de la divergence entre le pouls récent (SMA-7) et la tendance de fond (EMA-30).
    *   **Conflict momentum :** Accélération des tensions médiatiques.
      
*   **Performances :** 
    *   **AUC-ROC : 0.87**
    *   **Rappel (Recall) : 0.75**

### C. Interface de restitution des analyses et des prédictions
*   **Dashboard Streamlit :** Visualisation interactive de la distribution des évènements dans le temps et dans l'espace, des acteurs, des indicateurs et des relations entre indicateurs.
*   **Projections 2026 :** Estimation de la tendance de stabilité pour l'année 2026.
*   **Simulateur de scénario :** Simulation de scénarios en fonction du niveau de sécurité, de l'intensité des conflits, du ton médiatique et de la tendance au conflit et détermination du risque de crise. 

---

##  3. Structure du Dépôt
```text
/
├── dashboard/           # Code de l'application Streamlit
├── data/                # Données (brutes et nettoyées)
├── models/              # Modèle XGBoost (.json) et métadonnées techniques
├── notebooks/           # Prétraitement, analyses exploratoires et entraînement du modèle
├── requirements.txt     # Dépendances Python pour la reproductibilité
└── README.md            # Présentation du projet
```

## 4. Installation et reproductibilité
Pour répliquer l'environnement de Dahomey Intel : 

*  Cloner le dépôt
*  Installer les dépendances
```bash
pip install -r requirements.txt
```
* Compiler les codes ou lancer le dashboard 
Le dashboard est déployé et disponible sur le lien https://dahomeyintel.streamlit.app/

## 5. Membres de l'équipe
* **Data Engineer :** Fatou Touré
* **Data Analyst :** Peresh CHABI
* **ML Engineer :** Penouel KPATINVO
* **Data Scientist :** Roxane GUEYEP



# Usage de l'IA
Nous déclarons avoir utilisé des outils d'IA générative pour : 

* L'assistance à l'écriture des codes.
* La structuration de la documentation technique et du storytelling.
* L'optimisation de la charte graphique du dashboard.

