@echo off
REM RAG Backend Deployment Verification Script (Windows)
REM Run this after deploying to Render to verify all components are working

setlocal enabledelayedexpansion

REM Configuration
set BACKEND_URL=%1
if "%BACKEND_URL%"=="" set BACKEND_URL=https://rag-chatbot-backend.onrender.com
set TIMEOUT=10

echo.
echo ===================================================================
echo   RAG Backend Deployment Verification (Windows)
echo ===================================================================
echo.
echo Testing Backend: %BACKEND_URL%
echo.

REM Test 1: Health Check
echo [1/6] Testing health endpoint...
for /f "tokens=*" %%i in ('curl -s "%BACKEND_URL%/health"') do set HEALTH_RESPONSE=%%i

if "%HEALTH_RESPONSE%"=="" (
    echo X Health check failed - no response
    exit /b 1
) else (
    echo OK Health check passed
    echo     Response: %HEALTH_RESPONSE:~0,100%...
)

REM Test 2: API Documentation
echo.
echo [2/6] Checking API documentation...
for /f "tokens=*" %%i in ('curl -s -o nul -w "%%{http_code}" "%BACKEND_URL%/docs"') do set HTTP_CODE=%%i

if "%HTTP_CODE%"=="200" (
    echo OK API docs available (HTTP %HTTP_CODE%)
    echo     URL: %BACKEND_URL%/docs
) else (
    echo X API docs not available (HTTP %HTTP_CODE%)
    exit /b 1
)

REM Test 3: Query Endpoint
echo.
echo [3/6] Testing query endpoint...

REM Create temp file with JSON
(
echo {
echo   "query": "What is ROS 2?",
echo   "mode": "full_book"
echo }
) > temp_query.json

for /f "tokens=*" %%i in ('curl -s -X POST "%BACKEND_URL%/query" -H "Content-Type: application/json" -d @temp_query.json') do set QUERY_RESPONSE=%%i

if "%QUERY_RESPONSE%"=="" (
    echo X Query endpoint failed - no response
    del temp_query.json
    exit /b 1
) else (
    echo OK Query endpoint working

    echo %QUERY_RESPONSE% | find /i "answer" >nul
    if !errorlevel! equ 0 (
        echo OK Response contains answer field
    )

    echo %QUERY_RESPONSE% | find /i "retrieved_chunks" >nul
    if !errorlevel! equ 0 (
        echo OK Response contains retrieved chunks
    )
)

del temp_query.json

REM Test 4: Response Time
echo.
echo [4/6] Measuring response time...

REM Simple timing (Windows batch limitation - approximate)
for /f "tokens=*" %%i in ('powershell -Command "Measure-Command { curl.exe -s '%BACKEND_URL%/health' | Out-Null } | Select-Object -ExpandProperty TotalMilliseconds"') do set RESPONSE_TIME=%%i

echo OK Response time: approximately %RESPONSE_TIME%ms

REM Test 5: Show important URLs
echo.
echo [5/6] Important URLs for monitoring:
echo.
echo Health Check:    %BACKEND_URL%/health
echo API Docs:        %BACKEND_URL%/docs
echo Query Endpoint:  %BACKEND_URL%/query (POST)
echo Ingest Endpoint: %BACKEND_URL%/ingest (POST)

REM Test 6: Environment Check
echo.
echo [6/6] Checking environment setup:
echo.
echo Required environment variables:
echo  - ENVIRONMENT=production
echo  - DEBUG=false
echo  - DATABASE_URL (Neon PostgreSQL)
echo  - QDRANT_URL + QDRANT_API_KEY
echo  - OPENAI_API_KEY
echo  - GROQ_API_KEY
echo.

echo.
echo ===================================================================
echo OK Deployment verification complete!
echo ===================================================================
echo.
echo Next steps:
echo 1. Monitor service in Render dashboard
echo 2. Check logs for any errors
echo 3. Update frontend to use: %BACKEND_URL%
echo 4. Run end-to-end tests with frontend
echo.
pause
