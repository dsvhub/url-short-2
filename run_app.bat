@echo off
echo Activating virtual environment...
call venv\Scripts\activate

echo Setting environment variables...
set FLASK_APP=wsgi.py
set FLASK_ENV=development

echo Starting Flask app...
flask run

pause
