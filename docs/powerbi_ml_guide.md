# Guide d'Intégration du Machine Learning dans Power BI (Power Query)

Votre professeur a tout à fait raison ! On peut intégrer le Machine Learning (ML) directement **à l'intérieur de Power BI Desktop** en utilisant un script Python au moment de l'ETL dans **Power Query**. 

Cela permet à Power BI de recalculer les prédictions de fraude à chaque fois que vous rafraîchissez vos données.

Voici comment procéder étape par étape.

---

## Étape 1 : Préparer Power BI pour exécuter du Python

1. Ouvrez **Power BI Desktop**.
2. Allez dans **Fichier** > **Options et paramètres** > **Options**.
3. Dans la barre latérale gauche, cliquez sur **Script Python** (Python scripting).
4. Power BI détecte automatiquement votre répertoire d'installation Python local (ex: `C:\Python\Python313` ou votre environnement Conda). Si ce n'est pas le cas, indiquez le chemin manuellement.
5. Cliquez sur **OK**.

---

## Étape 2 : Lier la table de faits et les dimensions dans Power Query

Puisque notre modèle ML a besoin des variables des dimensions (ex: type de carte `card6`, type d'appareil `DeviceType`) et que la table `Fact_Transactions` ne contient que des clés numériques (`CardKey`, `DeviceKey`), nous devons d'abord fusionner temporairement les tables dans Power Query.

1. Dans Power BI, cliquez sur **Transformer les données** (Transform Data) pour ouvrir **Power Query**.
2. Sélectionnez la table **`fact_transactions`**.
3. Dans l'onglet Accueil, cliquez sur **Fusionner les requêtes** (Merge Queries) :
   * Fusionnez `fact_transactions` avec `dim_cards` sur la colonne `card_key`.
   * Développez (Expand) la table jointe pour ne garder que les colonnes `card1`, `card2`, `card3`, `card4`, `card5`, `card6`.
4. Répétez l'opération :
   * Fusionnez avec `dim_devices` sur `device_key` et développez `DeviceType`, `DeviceInfo`, `id_30` (OS), `id_31` (Browser).
   * Fusionnez avec `dim_locations` sur `location_key` et développez `addr1`, `addr2`.
   
*(Vous avez maintenant toutes les colonnes nécessaires à la prédiction réunies dans la même table de faits temporaire).*

---

## Étape 3 : Exécuter le script Python de prédiction

1. Dans Power Query, allez dans l'onglet **Transformer** (Transform) et cliquez sur **Exécuter le script Python** (Run Python Script) tout à droite.
2. Une boîte de dialogue s'ouvre. Copiez-y le script Python suivant :

```python
# 'dataset' contient la table de faits avec toutes ses colonnes
import pandas as pd
import joblib
import os

# Chemin d'accès absolu vers le modèle de Machine Learning entraîné
model_path = r"C:\Users\Lenovo\Desktop\MASTER\BI\Project\models\fraud_model.joblib"

if os.path.exists(model_path):
    # 1. Charger le modèle et l'encodeur sauvegardés par train_model.py
    model_data = joblib.load(model_path)
    model = model_data['model']
    encoder = model_data['encoder']
    features = model_data['features']
    categorical_features = model_data['categorical_features']
    
    # 2. Extraire et renommer les colonnes pour correspondre aux features du modèle
    # Power Query peut ajouter des suffixes après fusion (ex: dim_cards.card1). 
    # Nous nettoyons les noms si nécessaire pour correspondre aux features attendus :
    df_features = pd.DataFrame()
    for feat in features:
        # Recherche la colonne exacte ou avec un suffixe de table
        col_name = next((c for c in dataset.columns if c == feat or c.endswith("." + feat)), None)
        if col_name:
            df_features[feat] = dataset[col_name]
        else:
            # Valeur par défaut en cas d'absence
            if feat in categorical_features:
                df_features[feat] = "missing"
            else:
                df_features[feat] = 0.0

    # 3. Encoder les variables catégorielles
    for col in categorical_features:
        df_features[col] = df_features[col].astype(str)
    df_features[categorical_features] = encoder.transform(df_features[categorical_features])
    
    # 4. Prédire la probabilité et la classe de fraude
    dataset['predicted_fraud_prob'] = model.predict_proba(df_features)[:, 1]
    dataset['predicted_isFraud'] = (dataset['predicted_fraud_prob'] >= 0.5).astype(int)
else:
    # Valeurs par défaut si le modèle n'est pas trouvé
    dataset['predicted_fraud_prob'] = 0.02
    dataset['predicted_isFraud'] = 0

# Retourner le dataset modifié
output = dataset
```

3. Cliquez sur **OK**.
4. Power Query affiche une table nommée `output`. Cliquez sur le lien **Table** à côté d'elle pour afficher le résultat.

---

## Étape 4 : Nettoyer et Fermer

1. Sélectionnez les colonnes de dimensions que vous aviez fusionnées à l'étape 2 (ex: `card1`, `DeviceType`, etc.).
2. Faites un clic droit et sélectionnez **Supprimer les colonnes** (les dimensions d'origine restent disponibles dans leurs tables de dimensions respectives, nous n'avons plus besoin de ces copies).
3. Conservez uniquement les deux nouvelles colonnes créées par le script : **`predicted_fraud_prob`** et **`predicted_isFraud`**.
4. Allez dans l'onglet Accueil et cliquez sur **Fermer et appliquer** (Close & Apply).

---

## Étape 5 : Exemples d'Analyses de Machine Learning dans Power BI

Grâce à cette intégration, vous pouvez concevoir des graphiques avancés comparant l'IA décisionnelle et la réalité :

1. **Matrice de Confusion Visuelle :**
   * Utilisez un tableau croisé dynamique avec en lignes `isFraud` (Réel) et en colonnes `predicted_isFraud` (Prédiction).
   * La diagonale affichera les Vrais Positifs (Fraudes bien détectées) et Vrais Négatifs (Transactions saines bien classées).
2. **Visualisation des seuils de risque :**
   * Créez une courbe de distribution du score de risque `predicted_fraud_prob` pour identifier la proportion de transactions suspectes.
3. **Analyse des facteurs d'influence IA :**
   * Utilisez le visuel Power BI **"Influenceurs clés"** (Key Influencers) pour analyser quelles variables (ex: type de carte, pays, montant) influencent le plus le score `predicted_fraud_prob`. C'est une excellente démonstration d'IA explicable (XAI) directement dans Power BI.
