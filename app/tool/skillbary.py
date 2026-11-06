"""Tool MCP untuk database Skill Bary (tabel `skills`).

Tiap fungsi ber-decorator `@tool` bisa langsung dipakai Agent Strands maupun
dibungkus jadi MCP server. Semua query lewat sesi sync dari app.db.database.

Uji cepat: uv run python -m app.tool.skillbary
"""

import re

import httpx
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.db.database import SyncSessionLocal
from app.db.models import Skills
from strands import tool


def _row(skill: Skills) -> dict:
    return {
        "id": skill.id,
        "name": skill.name,
        "url": skill.url,
        "description": skill.description,
        "tags": skill.tags,
    }


@tool
def cari_skill(kata_kunci: str, limit: int = 5) -> list[dict]:
    """Cari skill di database berdasarkan kata kunci pada nama, deskripsi, atau tag."""
    pola = f"%{kata_kunci.strip()}%"
    stmt = (
        select(Skills)
        .where(
            or_(
                Skills.name.ilike(pola),
                Skills.description.ilike(pola),
                Skills.tags.ilike(pola),
            )
        )
        .order_by(Skills.name)
        .limit(limit)
    )
    with SyncSessionLocal() as session:
        return [_row(s) for s in session.scalars(stmt)]


@tool
def list_skill(limit: int = 20, offset: int = 0) -> list[dict]:
    """Ambil daftar skill terurut nama, dengan paginasi limit dan offset."""
    stmt = select(Skills).order_by(Skills.name).limit(limit).offset(offset)
    with SyncSessionLocal() as session:
        return [_row(s) for s in session.scalars(stmt)]


@tool
def detail_skill(name: str) -> dict:
    """Ambil satu skill persis berdasarkan namanya. Mengembalikan error jika tidak ada."""
    with SyncSessionLocal() as session:
        skill = session.scalar(select(Skills).where(Skills.name == name))
        return _row(skill) if skill else {"error": f"skill '{name}' tidak ditemukan"}


@tool
def daftar_skill(nama: str, url: str, deskripsi: str = "", tags: str = "") -> dict:
    """Simpan skill baru ke database. Nama dan url wajib, tags dipisah koma."""
    with SyncSessionLocal() as session:
        skill = Skills(name=nama.strip(), url=url.strip(), description=deskripsi, tags=tags)
        session.add(skill)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            return {"error": f"skill '{nama}' sudah terdaftar"}
        session.refresh(skill)
        return _row(skill)


def _kandidat_url(url: str) -> list[str]:
    """Repo GitHub -> URL raw README/SKILL; URL lain dipakai apa adanya."""
    m = re.fullmatch(r"https?://github\.com/([^/]+)/([^/?#]+?)(?:\.git)?/?", url.strip())
    if not m:
        return [url.strip()]
    owner, repo = m.groups()
    return [
        f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{nama}"
        for nama in ("README.md", "SKILL.md", "readme.md")
    ]


@tool
def baca_skill(url: str, max_chars: int = 8000) -> dict:
    """Ambil teks isi skill dari URL-nya (repo GitHub atau URL file mentah)."""
    dicoba = []
    for kandidat in _kandidat_url(url):
        try:
            resp = httpx.get(kandidat, timeout=15, follow_redirects=True)
        except httpx.HTTPError as e:
            dicoba.append({"url": kandidat, "error": type(e).__name__})
            continue
        if resp.status_code == 200 and resp.text.strip():
            return {
                "url": kandidat,
                "status": resp.status_code,
                "panjang": len(resp.text),
                "terpotong": len(resp.text) > max_chars,
                "text": resp.text[:max_chars],
            }
        dicoba.append({"url": kandidat, "status": resp.status_code})
    return {"error": f"tidak ada teks yang bisa diambil dari {url}", "dicoba": dicoba}


if __name__ == "__main__":
    import json

    print(json.dumps(list_skill(limit=3), indent=2, ensure_ascii=False))
