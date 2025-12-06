@echo off
echo Starting RRR_Admin...
echo.

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo Starting Flask app on http://localhost:5001/admin
echo.
python app.py

pause
