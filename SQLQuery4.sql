-- =========================================================================
-- PROJET DECISIONNEL : Data Warehouse pour la Détection des Fraudes Bancaires
-- Module : SSMS (SQL Server Management Studio)
-- Script : Création de la Base de Données et du Schéma en Étoile (Star Schema)
-- =========================================================================

-- 1. Création de la Base de Données
USE master;
GO

IF EXISTS (SELECT * FROM sys.databases WHERE name = 'IEEE_Fraud_DW')
BEGIN
    ALTER DATABASE IEEE_Fraud_DW SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE IEEE_Fraud_DW;
END
GO

CREATE DATABASE IEEE_Fraud_DW;
GO

USE IEEE_Fraud_DW;
GO

-- =========================================================================
-- 2. Création des Tables de Dimensions
-- =========================================================================

-- Dimension 1: Cartes de Paiement (Dim_Cards)
CREATE TABLE Dim_Cards (
    CardKey INT IDENTITY(1,1) PRIMARY KEY, -- surrogate key (clé artificielle)
    Card1 INT NULL,                        -- ID banque émettrice
    Card2 INT NULL,                        -- ID banque émettrice (secondaire)
    Card3 INT NULL,                        -- Code pays de la carte
    Card4 VARCHAR(50) NULL,                -- Réseau de carte (visa, mastercard, discover...)
    Card5 INT NULL,                        -- ID technique de carte
    Card6 VARCHAR(50) NULL                 -- Type de carte (debit, credit...)
);
GO

-- Dimension 2: Appareils de Connexion (Dim_Devices)
CREATE TABLE Dim_Devices (
    DeviceKey INT IDENTITY(1,1) PRIMARY KEY, -- surrogate key
    DeviceType VARCHAR(50) NULL,             -- mobile, desktop, missing...
    DeviceInfo VARCHAR(100) NULL,            -- Windows, iOS Device, Samsung...
    OS VARCHAR(100) NULL,                    -- Système d'exploitation (extrait de id_30)
    Browser VARCHAR(100) NULL                -- Navigateur web (extrait de id_31)
);
GO

-- Dimension 3: Localisation de Facturation (Dim_Locations)
CREATE TABLE Dim_Locations (
    LocationKey INT IDENTITY(1,1) PRIMARY KEY, -- surrogate key
    Addr1 INT NULL,                            -- ID Région de facturation
    Addr2 INT NULL                             -- ID Pays de facturation
);
GO

-- =========================================================================
-- 3. Création de la Table de Faits
-- =========================================================================

CREATE TABLE Fact_Transactions (
    TransactionID INT PRIMARY KEY,              -- Clé naturelle (id de transaction)
    TransactionDT INT NOT NULL,                 -- Delta de temps en secondes
    TransactionAmt DECIMAL(18,4) NOT NULL,      -- Montant de la transaction ($)
    ProductCD VARCHAR(10) NOT NULL,             -- Code produit (W, H, C, S, R...)
    
    -- Clés Étrangères vers les Dimensions
    CardKey INT NOT NULL,
    DeviceKey INT NOT NULL,
    LocationKey INT NOT NULL,
    
    -- Attributs de Transaction complémentaires
    P_emaildomain VARCHAR(100) NULL,            -- Email acheteur
    R_emaildomain VARCHAR(100) NULL,            -- Email destinataire
    
    -- Variables quantitatives de comptage (C)
    C1 DECIMAL(12,2) NULL,
    C2 DECIMAL(12,2) NULL,
    C11 DECIMAL(12,2) NULL,
    C13 DECIMAL(12,2) NULL,
    C14 DECIMAL(12,2) NULL,
    
    -- Variables quantitatives d'écart temporel (D)
    D1 DECIMAL(12,2) NULL,
    D2 DECIMAL(12,2) NULL,
    D10 DECIMAL(12,2) NULL,
    D15 DECIMAL(12,2) NULL,
    
    -- Variable Cible (Indicateur de Fraude)
    isFraud TINYINT NOT NULL DEFAULT 0,         -- 0 = Sain, 1 = Fraude
    
    -- Contraintes de clés étrangères (Foreign Keys)
    CONSTRAINT FK_Fact_Cards FOREIGN KEY (CardKey) REFERENCES Dim_Cards(CardKey),
    CONSTRAINT FK_Fact_Devices FOREIGN KEY (DeviceKey) REFERENCES Dim_Devices(DeviceKey),
    CONSTRAINT FK_Fact_Locations FOREIGN KEY (LocationKey) REFERENCES Dim_Locations(LocationKey)
);
GO

-- Création d'index pour optimiser les performances des requêtes analytiques (facultatif mais fortement recommandé en Big Data)
CREATE INDEX IX_Fact_CardKey ON Fact_Transactions(CardKey);
CREATE INDEX IX_Fact_DeviceKey ON Fact_Transactions(DeviceKey);
CREATE INDEX IX_Fact_LocationKey ON Fact_Transactions(LocationKey);
CREATE INDEX IX_Fact_isFraud ON Fact_Transactions(isFraud);
GO

print 'Data Warehouse IEEE_Fraud_DW cree avec succes !';
