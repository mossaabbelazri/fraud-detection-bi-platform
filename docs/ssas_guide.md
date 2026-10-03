# Guide de Modélisation Décisionnelle avec SSAS (SQL Server Analysis Services)

Ce guide décrit comment concevoir un **Modèle Tabulaire SSAS** dans Visual Studio à partir du schéma en étoile importé dans la base `IEEE_Fraud_DW`. Le modèle tabulaire est la norme moderne recommandable car il utilise le moteur In-Memory *VertiPaq* (identique à celui de Power BI) et le langage de requêtes **DAX**.

---

## 1. Création du Projet SSAS Tabulaire

1. Ouvrez Visual Studio.
2. Cliquez sur **Créer un projet** et choisissez le modèle **Projet tabulaire Analysis Services**.
3. Nommez le projet `SSAS_IEEE_Fraud` et cliquez sur **Créer**.
4. Lors du choix de l'instance d'Analysis Services (Workspace Server), sélectionnez le serveur tabulaire local (ex: `localhost` ou `localhost\TABULAR`). Choisissez la compatibilité SQL Server la plus récente (ex: SQL Server 2022 / niveau de compatibilité 1600).

---

## 2. Importation des Tables (Source de données)

1. Dans l'Explorateur de modèles tabulaires (Tabular Model Explorer), faites un clic droit sur **Data Sources** (Sources de données) > **New Data Source**.
2. Sélectionnez **SQL Server** et cliquez sur **Suivant**.
3. Entrez le nom de votre serveur SQL local (`localhost` ou `.`) et sélectionnez la base de données `IEEE_Fraud_DW`.
4. Sélectionnez le mode d'authentification approprié (ex: Identifiants du service Analysis Services ou compte Windows d'exécution).
5. Dans l'écran suivant, cochez les tables à importer :
   * `Fact_Transactions`
   * `Dim_Cards`
   * `Dim_Devices`
   * `Dim_Locations`
6. Cliquez sur **Importer** (ou **Terminer**).

---

## 3. Configuration des Relations (Modèle en Étoile)

1. En bas à droite de l'espace de conception Visual Studio, basculez de la **Vue Grille** (Grid View) à la **Vue Diagramme** (Diagram View).
2. Configurez les relations par un simple glisser-déposer :
   * Faites glisser `CardKey` de la table `Fact_Transactions` vers `CardKey` de la table `Dim_Cards`.
   * Faites glisser `DeviceKey` de la table `Fact_Transactions` vers `DeviceKey` de la table `Dim_Devices`.
   * Faites glisser `LocationKey` de la table `Fact_Transactions` vers `LocationKey` de la table `Dim_Locations`.
3. Double-cliquez sur chaque ligne de relation pour vérifier :
   * Multiplicité : **Plusieurs à un (*:1)** (Plusieurs transactions pour une même dimension).
   * Direction du filtrage croisé : **Unique** (La dimension filtre la table de faits).
   * État de la relation : **Actif**.

---

## 4. Masquer les Colonnes Techniques (Best Practice BI)

Pour éviter de surcharger l'utilisateur final dans Power BI :
1. Dans la vue diagramme ou grille, sélectionnez les colonnes clés techniques de jointure :
   * `CardKey`, `DeviceKey`, `LocationKey` dans la table de faits.
   * `CardKey` dans `Dim_Cards`, `DeviceKey` dans `Dim_Devices`, `LocationKey` dans `Dim_Locations`.
2. Faites un clic droit et sélectionnez **Masquer les outils clients** (Hide from Client Tools). Ces colonnes restent fonctionnelles pour les jointures internes mais n'encombreront pas l'affichage Power BI.

---

## 5. Création des Mesures DAX Calculées

Basculez dans la **Vue Grille** de la table `Fact_Transactions`. La partie inférieure de l'écran correspond à la zone de calcul des mesures. 

Cliquez sur une cellule vide de cette zone et saisissez les formules DAX suivantes (n'oubliez pas de mettre le préfixe suivi de `:=`) :

1. **Volume Financier Total (Transactions Amt) :**
   ```dax
   Montant Total Transactions := SUM(Fact_Transactions[TransactionAmt])
   ```
2. **Nombre Total de Transactions :**
   ```dax
   Nombre Transactions := COUNT(Fact_Transactions[TransactionID])
   ```
3. **Nombre de Fraudes Réelles détectées :**
   ```dax
   Nombre Fraudes := CALCULATE([Nombre Transactions], Fact_Transactions[isFraud] = 1)
   ```
4. **Taux de Fraude global (%) :**
   ```dax
   Taux Fraude := DIVIDE([Nombre Fraudes], [Nombre Transactions], 0)
   ```
5. **Panier Moyen (Montant Moyen par Transaction) :**
   ```dax
   Panier Moyen := AVERAGE(Fact_Transactions[TransactionAmt])
   ```

---

## 6. Déploiement du Cube Decisionnel

1. Dans l'Explorateur de solutions (Solution Explorer), faites un clic droit sur le nom du projet `SSAS_IEEE_Fraud` et sélectionnez **Propriétés**.
2. Dans la section **Déploiement** (Deployment), configurez :
   * **Serveur :** Le nom de votre instance SSAS locale (ex: `localhost\TABULAR`).
   * **Base de données :** Le nom sous lequel le cube apparaîtra (ex: `SSAS_IEEE_Fraud_Model`).
3. Cliquez sur OK.
4. Faites un clic droit sur le projet et sélectionnez **Déployer** (Deploy).
5. Une fois le traitement terminé au vert, votre cube décisionnel est en ligne et hébergé par Analysis Services ! Vous pouvez maintenant vous y connecter depuis Power BI Desktop.
