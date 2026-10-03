@echo off
title Plateforme de Detection de Fraude Bancaire - Decisionnel en Quasi-Temps Reel
echo =========================================================================
echo  PLATEFORME DE DETECTION ET DECISION DE FRAUDES EN QUASI-TEMPS REEL
echo =========================================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe ou n'est pas dans le PATH systeme.
    echo Veuillez installer Python pour lancer l'application.
    pause
    exit /b 1
)

echo [1/3] Verification des dependances Python...
python -c "import fastapi, uvicorn, joblib, pandas, sklearn" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installation des dependances manquantes...
    pip install fastapi uvicorn joblib pandas scikit-learn
) else (
    echo [OK] Toutes les dependances sont deja installees.
)
echo.

:: Check if processed data exists
if not exist "data_processed\fact_transactions.csv" (
    echo [2/3] Donnes pretraitees non detectees. Lancement de l'ETL...
    python src\etl_pipeline.py
) else (
    echo [2/3] [OK] Donnes pretraitees (Star Schema) deja presentes.
)
echo.

:: Check if trained model exists
if not exist "models\fraud_model.joblib" (
    echo [3/3] Modele de Machine Learning non detecte. Entrainement en cours...
    python src\train_model.py
) else (
    echo [3/3] [OK] Modele de Machine Learning charge et pret.
)
echo.

echo =========================================================================
echo  LANCEMENT DU SERVEUR WEB DECISIONNEL...
echo  Veuillez ouvrir votre navigateur a l'adresse : http://127.0.0.1:8000
echo  Pour arreter le serveur, fermez cette fenetre ou faites CTRL+C.
echo =========================================================================
echo.

python src\app.py
pause
