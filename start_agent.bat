@echo off

REM Activating virtual environment
CALL .\venv\Scripts\activate

REM Installing dependencies from requirements.txt
ECHO Installing required libraries... Please wait.
.\venv\Scripts\python.exe -m pip install -r requirements.txt

REM Starting the server
ECHO Starting the agent server...
uvicorn web_server:app --reload