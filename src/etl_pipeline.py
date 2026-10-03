import os
import pandas as pd
import numpy as np

# Define paths
raw_dir = r"c:\Users\Lenovo\Desktop\MASTER\BI\Project\ieee-fraud-detection"
processed_dir = r"c:\Users\Lenovo\Desktop\MASTER\BI\Project\data_processed"

def run_etl(sample_size=None):
    print("--- Starting ETL Pipeline ---")
    os.makedirs(processed_dir, exist_ok=True)
    
    # 1. Define columns to load to optimize memory
    trans_cols = [
        'TransactionID', 'isFraud', 'TransactionDT', 'TransactionAmt', 'ProductCD',
        'card1', 'card2', 'card3', 'card4', 'card5', 'card6',
        'addr1', 'addr2',
        'P_emaildomain', 'R_emaildomain',
        'C1', 'C2', 'C11', 'C13', 'C14',
        'D1', 'D2', 'D10', 'D15'
    ]
    
    ident_cols = [
        'TransactionID', 'DeviceType', 'DeviceInfo', 'id_30', 'id_31'
    ]
    
    # Define data types to save RAM
    trans_dtypes = {
        'TransactionID': 'int32',
        'isFraud': 'int8',
        'TransactionDT': 'int32',
        'TransactionAmt': 'float32',
        'ProductCD': 'category',
        'card1': 'float32',
        'card2': 'float32',
        'card3': 'float32',
        'card4': 'category',
        'card5': 'float32',
        'card6': 'category',
        'addr1': 'float32',
        'addr2': 'float32',
        'P_emaildomain': 'category',
        'R_emaildomain': 'category',
        'C1': 'float32',
        'C2': 'float32',
        'C11': 'float32',
        'C13': 'float32',
        'C14': 'float32',
        'D1': 'float32',
        'D2': 'float32',
        'D10': 'float32',
        'D15': 'float32'
    }
    
    ident_dtypes = {
        'TransactionID': 'int32',
        'DeviceType': 'category',
        'DeviceInfo': 'category',
        'id_30': 'category',
        'id_31': 'category'
    }
    
    # 2. Load Transaction data
    trans_path = os.path.join(raw_dir, "train_transaction.csv")
    print(f"Loading transactions from {trans_path}...")
    if sample_size:
        # Load sample to go fast
        df_trans = pd.read_csv(trans_path, usecols=trans_cols, dtype=trans_dtypes, nrows=sample_size)
        print(f"Loaded a sample of {sample_size} transactions.")
    else:
        df_trans = pd.read_csv(trans_path, usecols=trans_cols, dtype=trans_dtypes)
        print(f"Loaded all {len(df_trans)} transactions.")
        
    # 3. Load Identity data
    ident_path = os.path.join(raw_dir, "train_identity.csv")
    print(f"Loading identities from {ident_path}...")
    # Load all identities first, then we filter by merged IDs
    df_ident = pd.read_csv(ident_path, usecols=ident_cols, dtype=ident_dtypes)
    print(f"Loaded {len(df_ident)} identities.")
    
    # 4. Merge Data
    print("Merging transaction and identity data...")
    df_merged = pd.merge(df_trans, df_ident, on='TransactionID', how='left')
    
    # 5. Clean missing values and prepare clean labels
    print("Cleaning and preprocessing categorical data...")
    # Clean email domains
    df_merged['P_emaildomain'] = df_merged['P_emaildomain'].cat.add_categories(['missing']).fillna('missing')
    df_merged['R_emaildomain'] = df_merged['R_emaildomain'].cat.add_categories(['missing']).fillna('missing')
    
    # Clean device columns
    df_merged['DeviceType'] = df_merged['DeviceType'].cat.add_categories(['missing']).fillna('missing')
    df_merged['DeviceInfo'] = df_merged['DeviceInfo'].cat.add_categories(['missing']).fillna('missing')
    df_merged['id_30'] = df_merged['id_30'].cat.add_categories(['missing']).fillna('missing')
    df_merged['id_31'] = df_merged['id_31'].cat.add_categories(['missing']).fillna('missing')
    
    # Clean card info
    df_merged['card4'] = df_merged['card4'].cat.add_categories(['missing']).fillna('missing')
    df_merged['card6'] = df_merged['card6'].cat.add_categories(['missing']).fillna('missing')
    
    # Fill numeric columns with medians
    numeric_cols = ['card1', 'card2', 'card3', 'card5', 'addr1', 'addr2', 
                    'C1', 'C2', 'C11', 'C13', 'C14', 'D1', 'D2', 'D10', 'D15']
    for col in numeric_cols:
        if col in df_merged.columns:
            median_val = df_merged[col].median()
            # If median is nan (all missing), fill with 0
            if pd.isna(median_val):
                median_val = 0
            df_merged[col] = df_merged[col].fillna(median_val)
            
    # 6. Extract Dimensions (Star Schema)
    print("Extracting Star Schema dimensions...")
    
    # Dimension 1: Cards
    card_cols = ['card1', 'card2', 'card3', 'card4', 'card5', 'card6']
    df_cards = df_merged[card_cols].drop_duplicates().reset_index(drop=True)
    df_cards['card_key'] = df_cards.index + 1
    
    # Dimension 2: Devices
    device_cols = ['DeviceType', 'DeviceInfo', 'id_30', 'id_31']
    df_devices = df_merged[device_cols].drop_duplicates().reset_index(drop=True)
    df_devices['device_key'] = df_devices.index + 1
    
    # Dimension 3: Locations
    loc_cols = ['addr1', 'addr2']
    df_locations = df_merged[loc_cols].drop_duplicates().reset_index(drop=True)
    df_locations['location_key'] = df_locations.index + 1
    
    # 7. Map Foreign Keys to Fact Table
    print("Mapping keys to fact table...")
    # Merge card_key
    df_fact = pd.merge(df_merged, df_cards, on=card_cols, how='left')
    # Merge device_key
    df_fact = pd.merge(df_fact, df_devices, on=device_cols, how='left')
    # Merge location_key
    df_fact = pd.merge(df_fact, df_locations, on=loc_cols, how='left')
    
    # 8. Drop original dimension columns from Fact Table to save space
    fact_cols_to_keep = [
        'TransactionID', 'isFraud', 'TransactionDT', 'TransactionAmt', 'ProductCD',
        'P_emaildomain', 'R_emaildomain',
        'C1', 'C2', 'C11', 'C13', 'C14',
        'D1', 'D2', 'D10', 'D15',
        'card_key', 'device_key', 'location_key'
    ]
    df_fact = df_fact[fact_cols_to_keep]
    
    # 9. Save tables to CSV
    print("Saving Star Schema tables...")
    fact_path = os.path.join(processed_dir, "fact_transactions.csv")
    cards_path = os.path.join(processed_dir, "dim_cards.csv")
    devices_path = os.path.join(processed_dir, "dim_devices.csv")
    locations_path = os.path.join(processed_dir, "dim_locations.csv")
    
    df_fact.to_csv(fact_path, index=False)
    df_cards.to_csv(cards_path, index=False)
    df_devices.to_csv(devices_path, index=False)
    df_locations.to_csv(locations_path, index=False)
    
    print(f"ETL completed successfully! Files written to {processed_dir}")
    print(f"Fact Table rows: {len(df_fact)}")
    print(f"Dim Cards rows: {len(df_cards)}")
    print(f"Dim Devices rows: {len(df_devices)}")
    print(f"Dim Locations rows: {len(df_locations)}")
    print("---------------------------------")
    return df_fact, df_cards, df_devices, df_locations

if __name__ == "__main__":
    # Let's default to a sample of 150,000 for speed and performance, but can run on full if needed.
    # 150,000 is more than enough for excellent training and representation.
    run_etl(sample_size=150000)
