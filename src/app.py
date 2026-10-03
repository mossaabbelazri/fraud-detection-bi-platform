import os
import json
import asyncio
import pandas as pd
import numpy as np
import joblib
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI(title="Decisional Fraud Detection Platform")

# Setup directories
base_dir = r"c:\Users\Lenovo\Desktop\MASTER\BI\Project"
processed_dir = os.path.join(base_dir, "data_processed")
models_dir = os.path.join(base_dir, "models")

# Mount static files (for css/js)
static_dir = os.path.join(base_dir, "src", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates
templates_dir = os.path.join(base_dir, "src", "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

# Global Simulation State
class SimulatorState:
    def __init__(self):
        self.is_running = True
        self.speed_seconds = 1.0  # seconds between transactions
        self.current_idx = 0
        self.df_stream = None
        self.model_data = None
        
        # Live Session Metrics
        self.total_processed = 0
        self.total_amount_processed = 0.0
        self.actual_frauds_detected = 0      # Actual frauds flagged by model
        self.prevented_fraud_amount = 0.0     # Amount of fraud blocked by analyst
        self.false_alerts_count = 0          # Safe transactions blocked by mistake
        
        # Queue of active alerts (waiting for analyst decision)
        # key: transaction_id, val: transaction details
        self.active_alerts = {}
        # History of analyst decisions
        # key: transaction_id, val: 'approved' | 'blocked'
        self.decisions = {}

state = SimulatorState()

# Load model and data
def init_data():
    model_path = os.path.join(models_dir, "fraud_model.joblib")
    fact_path = os.path.join(processed_dir, "fact_transactions.csv")
    
    if not os.path.exists(fact_path):
        print(f"Error: {fact_path} does not exist. Please run ETL script first.")
        return False
        
    print("Loading datasets for simulation...")
    df_fact = pd.read_csv(fact_path)
    df_cards = pd.read_csv(os.path.join(processed_dir, "dim_cards.csv"))
    df_devices = pd.read_csv(os.path.join(processed_dir, "dim_devices.csv"))
    df_locations = pd.read_csv(os.path.join(processed_dir, "dim_locations.csv"))
    
    print("Reconstructing full table for streaming...")
    df = pd.merge(df_fact, df_cards, on='card_key', how='left')
    df = pd.merge(df, df_devices, on='device_key', how='left')
    df = pd.merge(df, df_locations, on='location_key', how='left')
    
    # Sort by TransactionDT to simulate chronological stream
    df = df.sort_values('TransactionDT').reset_index(drop=True)
    state.df_stream = df
    
    if os.path.exists(model_path):
        print("Loading trained Machine Learning model...")
        state.model_data = joblib.load(model_path)
    else:
        print("Warning: Trained ML model not found. Using predictions from ETL scoring.")
        
    print(f"Simulator initialized with {len(df)} transactions.")
    return True

# Initialize on startup
init_data()

# Root page
@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    if state.df_stream is None:
        # Re-try init
        init_data()
    return templates.TemplateResponse(request, "index.html")

# SSE streaming endpoint
@app.get("/api/stream")
async def stream_transactions():
    if state.df_stream is None:
        init_data()
        if state.df_stream is None:
            return StreamingResponse(iter(["data: {\"error\": \"No data loaded\"}\n\n"]), media_type="text/event-stream")

    async def event_generator():
        print("Client connected to SSE stream.")
        while True:
            if not state.is_running:
                await asyncio.sleep(0.5)
                continue
                
            if state.current_idx >= len(state.df_stream):
                state.current_idx = 0 # loop back
                
            row = state.df_stream.iloc[state.current_idx]
            state.current_idx += 1
            
            # Extract features for this transaction
            tx_data = {
                "TransactionID": int(row["TransactionID"]),
                "TransactionDT": int(row["TransactionDT"]),
                "TransactionAmt": float(row["TransactionAmt"]),
                "ProductCD": str(row["ProductCD"]),
                "card_brand": str(row["card4"]),
                "card_type": str(row["card6"]),
                "card_bank": int(row["card1"]),
                "DeviceType": str(row["DeviceType"]),
                "DeviceInfo": str(row["DeviceInfo"]),
                "OS": str(row["id_30"]),
                "Browser": str(row["id_31"]),
                "addr1": float(row["addr1"]),
                "addr2": float(row["addr2"]),
                "isFraud": int(row["isFraud"]),
                "predicted_fraud_prob": float(row.get("predicted_fraud_prob", 0.05)),
                "predicted_isFraud": int(row.get("predicted_isFraud", 0))
            }
            
            # Update live processing metrics
            state.total_processed += 1
            state.total_amount_processed += tx_data["TransactionAmt"]
            
            # If model flags it as fraud (predicted_fraud_prob >= 0.5)
            # it goes to active alerts queue and requires analyst validation
            is_flagged = tx_data["predicted_fraud_prob"] >= 0.5
            if is_flagged:
                state.actual_frauds_detected += 1
                state.active_alerts[tx_data["TransactionID"]] = tx_data
            
            # Yield event
            yield f"data: {json.dumps(tx_data)}\n\n"
            
            await asyncio.sleep(state.speed_seconds)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Control simulation parameters
class ControlConfig(BaseModel):
    is_running: bool
    speed_seconds: float

@app.post("/api/control")
async def control_simulator(config: ControlConfig):
    state.is_running = config.is_running
    state.speed_seconds = max(0.05, min(5.0, config.speed_seconds)) # bound between 0.05s and 5s
    return {"status": "success", "is_running": state.is_running, "speed_seconds": state.speed_seconds}

# Submit analyst decision (approve or block)
class DecisionRequest(BaseModel):
    transaction_id: int
    decision: str  # 'approved' or 'blocked'

@app.post("/api/decision")
async def submit_decision(req: DecisionRequest):
    tx_id = req.transaction_id
    dec = req.decision.lower()
    
    if dec not in ['approved', 'blocked']:
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'blocked'")
        
    if tx_id not in state.active_alerts:
        # Check if we already processed it
        if tx_id in state.decisions:
            return {"status": "ignored", "message": f"Transaction {tx_id} already has a decision: {state.decisions[tx_id]}"}
        raise HTTPException(status_code=404, detail="Transaction not found in active alerts")
        
    tx_data = state.active_alerts.pop(tx_id)
    state.decisions[tx_id] = dec
    
    # Calculate stats changes based on decision
    is_actual_fraud = tx_data["isFraud"] == 1
    amount = tx_data["TransactionAmt"]
    
    if dec == 'blocked':
        state.prevented_fraud_amount += amount
        if not is_actual_fraud:
            state.false_alerts_count += 1 # Blocked an innocent customer!
    
    return {
        "status": "success",
        "transaction_id": tx_id,
        "decision": dec,
        "is_actual_fraud": is_actual_fraud,
        "amount": amount
    }

# Get live metrics
@app.get("/api/stats")
async def get_stats():
    return {
        "total_processed": state.total_processed,
        "total_amount_processed": round(state.total_amount_processed, 2),
        "actual_frauds_detected": state.actual_frauds_detected,
        "prevented_fraud_amount": round(state.prevented_fraud_amount, 2),
        "false_alerts_count": state.false_alerts_count,
        "active_alerts_count": len(state.active_alerts),
        "decisions_count": len(state.decisions),
        "current_idx": state.current_idx
    }

# Get historical / BI statistics from the full processed dataset
@app.get("/api/historical-charts")
async def get_historical_charts():
    if state.df_stream is None:
        init_data()
        if state.df_stream is None:
            return {}
            
    # To avoid computing on full dataset every time, we take a representative sample of 15,000 for chart aggregates
    df = state.df_stream.sample(min(15000, len(state.df_stream)), random_state=42)
    
    # Chart 1: Fraud Rate by Card Brand
    card_brand_stats = df.groupby('card4', observed=False).agg(
        total=('isFraud', 'count'),
        frauds=('isFraud', 'sum')
    )
    card_brand_stats['fraud_rate'] = (card_brand_stats['frauds'] / card_brand_stats['total']) * 100
    card_brand_stats = card_brand_stats.fillna(0)
    
    # Chart 2: Fraud Rate by Device Type
    device_stats = df.groupby('DeviceType', observed=False).agg(
        total=('isFraud', 'count'),
        frauds=('isFraud', 'sum')
    )
    device_stats['fraud_rate'] = (device_stats['frauds'] / device_stats['total']) * 100
    device_stats = device_stats.fillna(0)
    
    # Chart 3: Transaction Amount Distribution vs Fraud
    # Define bins
    bins = [0, 50, 100, 250, 500, 1000, 5000, 100000]
    labels = ['0-50$', '50-100$', '100-250$', '250-500$', '500-1k$', '1k-5k$', '5k$+']
    df['AmtRange'] = pd.cut(df['TransactionAmt'], bins=bins, labels=labels)
    amt_stats = df.groupby('AmtRange', observed=False).agg(
        total=('isFraud', 'count'),
        frauds=('isFraud', 'sum')
    )
    amt_stats['fraud_rate'] = (amt_stats['frauds'] / amt_stats['total']) * 100
    amt_stats = amt_stats.fillna(0)

    # Chart 4: Fraud rate over time (by transaction offset hour)
    # Simple hour calculation: TransactionDT is seconds from start. Let's make bins of 12 hours.
    df['DT_Hour'] = (df['TransactionDT'] // 3600) % 24
    time_stats = df.groupby('DT_Hour', observed=False).agg(
        total=('isFraud', 'count'),
        frauds=('isFraud', 'sum')
    )
    time_stats['fraud_rate'] = (time_stats['frauds'] / time_stats['total']) * 100
    time_stats = time_stats.fillna(0).sort_index()

    return {
        "card_brand": {
            "labels": list(card_brand_stats.index),
            "rates": list(round(card_brand_stats['fraud_rate'], 2)),
            "counts": list(card_brand_stats['total'])
        },
        "device_type": {
            "labels": list(device_stats.index),
            "rates": list(round(device_stats['fraud_rate'], 2)),
            "counts": list(device_stats['total'])
        },
        "amt_range": {
            "labels": list(amt_stats.index),
            "rates": list(round(amt_stats['fraud_rate'], 2)),
            "counts": list(amt_stats['total'])
        },
        "time_of_day": {
            "labels": [f"{h}h" for h in time_stats.index],
            "rates": list(round(time_stats['fraud_rate'], 2)),
            "counts": list(time_stats['total'])
        }
    }

# Reset stats
@app.post("/api/reset")
async def reset_stats():
    state.total_processed = 0
    state.total_amount_processed = 0.0
    state.actual_frauds_detected = 0
    state.prevented_fraud_amount = 0.0
    state.false_alerts_count = 0
    state.active_alerts.clear()
    state.decisions.clear()
    state.current_idx = 0
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    # Start server
    uvicorn.run(app, host="127.0.0.1", port=8000)
