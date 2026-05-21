@echo off
cd /d "%~dp0"

echo ========================================
echo   AI Trading Analyzer
echo ========================================
echo.

echo Menginstall dependencies...
python -m pip install --prefer-binary --upgrade pip -q
python -m pip install --prefer-binary -r requirements.txt -q
if errorlevel 1 (
    echo.
    echo GAGAL install. Mencoba install satu per satu...
    python -m pip install --prefer-binary streamlit yfinance plotly requests anthropic python-dotenv -q
    python -m pip install --prefer-binary pandas numpy scipy ta beautifulsoup4 lxml feedparser -q
    python -m pip install --prefer-binary streamlit-autorefresh websocket-client -q
)

echo.
echo Menjalankan aplikasi di http://localhost:8501
python -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false

pause
