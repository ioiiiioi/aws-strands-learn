"""Entry point: jalankan REST API Skill Bary.

    uv run python main.py

Padanan tanpa reloader untuk produksi:

    uv run fastapi run app/api/main.py
"""

import uvicorn

from app.core.config import settings

HOST = "0.0.0.0"
PORT = 8000

if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host=HOST,
        port=PORT,
        reload=settings.APP_ENV == "development",
    )
