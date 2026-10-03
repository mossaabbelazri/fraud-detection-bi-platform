# Guide de Restitution et Visualisation dans Power BI

Ce guide explique comment connecter **Power BI Desktop** à votre modèle tabulaire **SSAS** et concevoir des rapports décisionnels interactifs et professionnels pour l'analyse des fraudes bancaires.

---

## 1. Connexion de Power BI à SSAS

Puisque toute la modélisation (relations, nettoyage) et les calculs (mesures DAX) ont été centralisés dans le cube SSAS, nous allons utiliser une **Connexion en Direct (Live Connection)**. C'est la meilleure pratique en entreprise car Power BI n'agit que comme couche de présentation, déléguant les calculs lourds au serveur Analysis Services.

1. Ouvrez **Power BI Desktop**.
2. Dans l'onglet Accueil (Home), cliquez sur **Obtenir des données** (Get Data) > **SQL Server Analysis Services**.
3. Dans la boîte de dialogue :
   * **Serveur :** Saisissez le nom de votre instance SSAS locale (ex: `localhost\TABULAR`).
   * **Base de données (facultatif) :** Saisissez le nom du modèle déployé (ex: `SSAS_IEEE_Fraud_Model`).
   * **Mode de connexion :** Cochez **Se connecter en direct** (Connect live).
4. Cliquez sur **OK**.
5. Sélectionnez votre cube décisionnel dans la liste et cliquez sur **OK**.

*Vous verrez apparaître dans le panneau de droite (Champs / Fields) vos dimensions et votre table de faits avec l'icône de calcul de vos mesures DAX. Remarquez que les clés de jointure masquées n'apparaissent pas, ce qui rend le modèle propre et simple.*

---

## 2. Conception de l'Interface Visuelle (Dashboard)

Pour créer un rapport percutant et professionnel (qui saura impressionner votre professeur), suivez cette structure de mise en page :

### A. En-tête et KPI Cards (Le résumé)
Placez en haut de la page 3 à 4 visuels de type **Carte** (Card) pour les indicateurs clés de performance (KPIs) :
1. **Montant total des transactions :** Glissez la mesure `[Montant Total Transactions]`.
2. **Nombre de transactions :** Glissez la mesure `[Nombre Transactions]`.
3. **Nombre de fraudes réelles :** Glissez la mesure `[Nombre Fraudes]`.
4. **Taux de fraude moyen :** Glissez la mesure `[Taux Fraude]`.

### B. Graphiques d'Analyse des Dimensions (Le détail)
Ajoutez les graphiques suivants dans le corps de votre rapport :

1. **Analyse des Cartes (Qui fraude ?) :**
   * **Type de visuel :** Histogramme groupé (Clustered Column Chart).
   * **Axe X :** `Dim_Cards[Card4]` (Réseau de cartes : Visa, Mastercard...) ou `Dim_Cards[Card6]` (Crédit/Débit).
   * **Valeurs :** `[Taux Fraude]`.
   * *Objectif : Analyser si le risque de fraude est plus élevé sur les cartes de crédit ou sur certains réseaux spécifiques.*
2. **Analyse des Appareils (Comment fraudent-ils ?) :**
   * **Type de visuel :** Graphique à secteurs (Pie Chart) ou en anneau (Donut Chart).
   * **Légende :** `Dim_Devices[DeviceType]` (desktop, mobile, missing).
   * **Valeurs :** `[Nombre Fraudes]`.
   * *Objectif : Identifier les canaux préférés des fraudeurs.*
3. **Analyse Géographique (D'où fraudent-ils ?) :**
   * **Type de visuel :** Treemap ou Cartographie.
   * **Catégorie / Groupe :** `Dim_Locations[Addr2]` (Code Pays de facturation) puis `Dim_Locations[Addr1]` (Région).
   * **Valeurs :** `[Montant Total Transactions]`.
   * *Objectif : Localiser géographiquement les flux financiers suspects.*
4. **Évolution Temporelle (Quand fraudent-ils ?) :**
   * **Type de visuel :** Graphique en courbes (Line Chart).
   * **Axe :** Créez une dimension temporelle ou utilisez un axe d'heures calculées.
   * **Valeurs :** `[Taux Fraude]`.

---

## 3. Bonnes Pratiques de Design dans Power BI

* **Charte Graphique :** Utilisez une palette de couleurs harmonieuse. Évitez les couleurs primaires agressives (rouge vif, bleu vif, vert vif). Privilégiez des teintes professionnelles (comme un camaïeu de bleus/gris avec le rouge réservé exclusivement pour mettre en évidence la fraude).
* **Filtres interactifs :** Ajoutez des segments (**Slicers**) sur le côté ou en haut de la page pour filtrer par type de produit (`Fact_Transactions[ProductCD]`) ou par réseau de carte.
* **Titres clairs :** Donnez des titres descriptifs à vos visuels (ex : *"Taux de fraude par type d'appareil de connexion"* au lieu de *"Taux Fraude par DeviceType"*).
* **Format des nombres :** Assurez-vous que la mesure `[Taux Fraude]` est formatée en **Pourcentage (%)** avec 2 décimales et que le `[Montant Total Transactions]` est formaté en **Devise ($)** avec des séparateurs de milliers.
