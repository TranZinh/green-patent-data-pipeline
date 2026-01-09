@echo off
cls
echo ==========================================================
echo   STARTING END-TO-END DATA PIPELINE (MINIO + POLARS)
echo ==========================================================

:: Step 1: Ingestion - Download data from S3 to MinIO
echo [STEP 1/6] Ingesting raw data...
docker exec -it python_worker python app/main.py
if %ERRORLEVEL% NEQ 0 (echo [!] ERROR at Step 1: Ingestion failed. && pause && exit /b)

:: Step 2: Ingestion Audit - Verify ZIP integrity (Files in /test)
echo [STEP 2/6] Auditing ingested files (Magic Bytes)...
docker exec -it python_worker python test/test_main.py
if %ERRORLEVEL% NEQ 0 (echo [!] ERROR at Step 2: Audit failed. && pause && exit /b)

:: Step 3: Transformation - Convert TSV.ZIP to Parquet
echo [STEP 3/6] Converting formats (TSV to Parquet)...
docker exec -it python_worker python app/convert_to_parquet.py
if %ERRORLEVEL% NEQ 0 (echo [!] ERROR at Step 3: Conversion failed. && pause && exit /b)

:: Step 4: Transformation Audit - Row count verification (Files in /test)
echo [STEP 4/6] Auditing transformation (Row count match)...
docker exec -it python_worker python test/test_convert_to_parquet.py
if %ERRORLEVEL% NEQ 0 (echo [!] ERROR at Step 4: Row count mismatch. && pause && exit /b)

:: Step 5: Analysis - Process business logic with Polars
echo [STEP 5/6] Running data analysis...
docker exec -it python_worker python app/process_data.py
if %ERRORLEVEL% NEQ 0 (echo [!] ERROR at Step 5: Analysis failed. && pause && exit /b)

:: Step 6: Final Audit - Business logic reconciliation (Files in /test)
echo [STEP 6/6] Final data reconciliation (Brute-force)...
docker exec -it python_worker python test/test_process_data.py
if %ERRORLEVEL% NEQ 0 (echo [!] ERROR at Step 6: Reconciliation failed. && pause && exit /b)

echo ==========================================================
echo   PIPELINE COMPLETED SUCCESSFULLY!
echo ==========================================================
pause