# RRR_Admin Startup Script
# Run this with: .\start.ps1

Write-Host "Starting RRR_Admin..." -ForegroundColor Green

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install dependencies if needed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# Start the Flask app
Write-Host "Starting Flask app on http://localhost:5001/admin" -ForegroundColor Green
python app.py
