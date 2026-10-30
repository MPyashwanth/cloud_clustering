@echo off
setlocal
cd /d "%~dp0"
if errorlevel 1 (
    echo Could not open the project folder.
    pause
    exit /b 1
)

set "APP_URL=http://localhost:8501"
set "PYTHON=%CD%\.venv\Scripts\python.exe"
set "LOG_FILE=%TEMP%\global-development-clustering-streamlit.log"

if not exist "%PYTHON%" (
    echo Creating the project Python environment...
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv "%CD%\.venv"
    ) else (
        where python >nul 2>nul
        if errorlevel 1 (
            echo Python 3 is required. Install Python and run this file again.
            pause
            exit /b 1
        )
        python -m venv "%CD%\.venv"
    )
    if errorlevel 1 (
        echo Could not create the Python environment.
        pause
        exit /b 1
    )
)

if not exist "requirements.txt" (
    echo Could not find requirements.txt in the project folder.
    pause
    exit /b 1
)

"%PYTHON%" -c "import matplotlib, numpy, openpyxl, pandas, sklearn, streamlit" >nul 2>nul
if errorlevel 1 (
    echo Installing the app dependencies. This may take a few minutes the first time...
    "%PYTHON%" -m pip install -r "%CD%\requirements.txt"
    if errorlevel 1 (
        echo Dependency installation failed. Check your internet connection and try again.
        pause
        exit /b 1
    )
)

curl.exe --silent --fail --max-time 3 "%APP_URL%" >nul 2>nul
if not errorlevel 1 goto open_edge

echo Starting the clustering app...
start "" /B "%PYTHON%" -m streamlit run "%CD%\app.py" --server.headless true --server.port 8501 >"%LOG_FILE%" 2>&1

echo Waiting for Streamlit to start...
for /L %%i in (1,1,45) do (
    curl.exe --silent --fail --max-time 2 "%APP_URL%" >nul 2>nul
    if not errorlevel 1 goto open_edge
    timeout /t 1 /nobreak >nul
)

echo The app did not start. See the log:
echo %LOG_FILE%
pause
exit /b 1

:open_edge
echo Opening the app in Microsoft Edge: %APP_URL%
start "" "microsoft-edge:%APP_URL%"
exit /b 0
