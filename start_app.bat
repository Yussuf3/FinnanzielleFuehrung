@echo off
chcp 65001 > nul
echo =======================================================================
echo    Financial Analyzer ^& Wealth Management Tool
echo    Finanzielle Fuehrung - Hackathon 2026
echo =======================================================================
echo.
echo Oeffne Browser unter http://localhost:8501 ...
start "" "http://localhost:8501"
echo Starte Streamlit Server...
python -m streamlit run app.py
pause
