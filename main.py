# Точка входа для совместимости с Heroku/Railway.
# Настоящее приложение находится в backend/app/main.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from app.main import app  # noqa
