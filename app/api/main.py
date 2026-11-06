"""REST API Skill Bary.

Jalan: uv run python main.py
Dokumentasi otomatis: /docs

POST /skills  -> kirim url GitHub, agent mengisi field lalu menyimpan ke database
GET  /skills  -> agent memilih skill yang cocok untuk teks `q`
"""

import time

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.skill_router import pilih_skill, simpan_skill_dari_url
from app.core.log import setup_logging
from app.db.database import get_sync_db
from app.db.models import Skills
from .schemas import SkillKeluar, SkillTersimpan, UrlMasuk

setup_logging()

app = FastAPI(title="Skill Bary API", version="1.0.0")


@app.middleware("http")
async def log_permintaan(request: Request, call_next):
    """Satu baris per request: metode, path, status, durasi."""
    mulai = time.perf_counter()
    response = await call_next(request)
    logger.info(
        "{} {} -> {} | {:.1f}s",
        request.method,
        request.url.path,
        response.status_code,
        time.perf_counter() - mulai,
    )
    return response


@app.post("/skills", response_model=SkillTersimpan, status_code=201)
def simpan_skill(data: UrlMasuk, db: Session = Depends(get_sync_db)) -> dict:
    """Daftarkan skill dari url GitHub. Field name, description, dan tags diisi agent."""
    url = data.url.rstrip("/")
    if db.scalar(select(Skills).where(Skills.url == url)):
        raise HTTPException(status_code=409, detail=f"url '{url}' sudah terdaftar")

    hasil = simpan_skill_dari_url(url)
    if "error" in hasil:
        raise HTTPException(status_code=502, detail=hasil)
    return hasil


@app.get("/skills", response_model=SkillKeluar)
def cari_skill(q: str = Query("", description="teks bebas, misal 'bikin animasi matematika'")) -> dict:
    """Pilih skill paling cocok untuk `q`. Tanpa `q` agent memilih dari katalog apa adanya."""
    return pilih_skill(q.strip() or "skill apa saja yang paling berguna")
