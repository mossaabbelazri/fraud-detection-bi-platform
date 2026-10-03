import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.preprocessing import OrdinalEncoder

# Define paths
processed_dir = r"c:\Users\Lenovo\Desktop\MASTER\BI\Project\data_processed"
models_dir = r"c:\Users\Lenovo\Desktop\MASTER\BI\Project\models"

def train_model():
    print("--- Starting ML Model Training ---")
    os.makedirs(models_dir, exist_ok=True)
    
    # 1. Load Star Schema tables
    print("Loading processed data...")
    df_fact = pd.read_csv(os.path.join(processed_dir, "fact_transactions.csv"))
    df_cards = pd.read_csv(os.path.join(processed_dir, "dim_cards.csv"))
    df_devices = pd.read_csv(os.path.join(processed_dir, "dim_devices.csv"))
    df_locations = pd.read_csv(os.path.join(processed_dir, "dim_locations.csv"))
    
    # 2. Reconstruct features for training by joining
    print("Reconstructing feature space for training...")
    df_train = pd.merge(df_fact, df_cards, on='card_key', how='left')
    df_train = pd.merge(df_train, df_devices, on='device_key', how='left')
    df_train = pd.merge(df_train, df_locations, on='location_key', how='left')
    
    # 3. Define features
    categorical_features = [
        'ProductCD', 'card4', 'card6', 'P_emaildomain', 'R_emaildomain', 
        'DeviceType', 'DeviceInfo', 'id_30', 'id_31'
    ]
    
    numerical_features = [
        'TransactionAmt', 'card1', 'card2', 'card3', 'card5', 'addr1', 'addr2',
        'C1', 'C2', 'C11', 'C13', 'C14',
        'D1', 'D2', 'D10', 'D15'
    ]
    
    features = categorical_features + numerical_features
    target = 'isFraud'
    
    X = df_train[features].copy()
    y = df_train[target].copy()
    
    # 4. Handle categorical features using OrdinalEncoder (required for HistGradientBoostingClassifier)
    print("Encoding categorical features...")
    # Convert categorical features to string and then encode
    for col in categorical_features:
        X[col] = X[col].astype(str)
        
    encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    X[categorical_features] = encoder.fit_transform(X[categorical_features])
    
    # 5. Split train/test
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"Train set size: {X_train.shape[0]} | Validation set size: {X_val.shape[0]}")
    print(f"Fraud rate in training: {y_train.mean():.2%}")
    print(f"Fraud rate in validation: {y_val.mean():.2%}")
    
    # 6. Train HistGradientBoostingClassifier (supports categorical features natively if indices are specified, but ordinal encoding is also excellent)
    print("Training HistGradientBoostingClassifier model...")
    # Find indices of categorical features for hist gradient boosting
    cat_indices = [features.index(col) for col in categorical_features]
    
    model = HistGradientBoostingClassifier(
        max_iter=150, 
        learning_rate=0.1, 
        max_depth=8, 
        random_state=42,
        class_weight='balanced'  # highly unbalanced data (approx 3.5% fraud)
    )
    
    model.fit(X_train, y_train)
    
    # 7. Evaluate Model
    print("Evaluating model...")
    preds = model.predict(X_val)
    probs = model.predict_proba(X_val)[:, 1]
    
    auc = roc_auc_score(y_val, probs)
    print(f"\nROC AUC Score: {auc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_val, preds))
    
    print("Confusion Matrix:")
    print(confusion_matrix(y_val, preds))
    
    # 8. Save model components
    model_data = {
        'model': model,
        'encoder': encoder,
        'features': features,
        'categorical_features': categorical_features,
        'numerical_features': numerical_features
    }
    
    model_path = os.path.join(models_dir, "fraud_model.joblib")
    print(f"Saving model to {model_path}...")
    joblib.dump(model_data, model_path)
    
    # 9. Score the entire fact dataset to export predictions for Power BI
    print("Scoring entire fact table for Power BI analytics...")
    X_all = df_train[features].copy()
    for col in categorical_features:
        X_all[col] = X_all[col].astype(str)
    X_all[categorical_features] = encoder.transform(X_all[categorical_features])
    
    df_fact['predicted_fraud_prob'] = model.predict_proba(X_all)[:, 1]
    df_fact['predicted_isFraud'] = (df_fact['predicted_fraud_prob'] >= 0.5).astype(int)
    
    # Resave the fact table with predictions included!
    fact_path = os.path.join(processed_dir, "fact_transactions.csv")
    df_fact.to_csv(fact_path, index=False)
    print(f"Updated fact table with predictions at: {fact_path}")
    print("--- Model Training & Scoring Complete ---")

if __name__ == "__main__":
    train_model()
