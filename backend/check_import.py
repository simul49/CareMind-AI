import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./caremind_check.db")

from app.main import app

print("Import OK - routes:", len(app.routes))
