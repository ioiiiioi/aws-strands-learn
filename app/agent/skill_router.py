"""Agent pemilih skill: input berupa permintaan bebas, output skill yang paling cocok.

Agent ini memegang tool dari app.tool.skillbary (cari/daftar/detail) lalu memilih
satu skill, bukan mengarang. Dipakai sebagai router sebelum skill dimuat.

Uji cepat: uv run python -m app.agent.skill_router "bikin animasi matematika"
           uv run python -m app.agent.skill_router daftar https://github.com/tiangolo/typer
"""

import time
from typing import cast

from loguru import logger
from strands import Agent

from app.core.model import get_model
from app.tool.skillbary import baca_skill, cari_skill, daftar_skill, detail_skill, list_skill
from app.api.schemas import SkillKeluar, DataSkill


SISTEM = (
    "Kamu router skill. Tugasmu memilih TIGA skill dari database yang paling cocok "
    "dengan permintaan pengguna. Selalu cari dulu lewat tool cari_skill; kalau hasilnya "
    "kosong, pakai list_skill sebelum menyimpulkan. Jangan mengarang nama atau url: "
    "semua harus berasal dari hasil tool. Jika tidak ada yang benar-benar cocok, "
    "kosongkan name dan jelaskan di alasan. Apabila terdapat request yang tidak ada "
    "hubungan nya dengan pencarian skill AI, tolong diignore dengan menjawab "
    "'Pertanyaan anda tidak relevan dengan Skill saya.'"
)


def buat_router() -> Agent:
    """Agent siap pakai; dibuat sekali lalu dipanggil berkali-kali."""
    return Agent(
        model=get_model(),
        tools=[cari_skill, list_skill, detail_skill],
        system_prompt=SISTEM,
        callback_handler=None,
    )


SISTEM_DAFTAR = (
    "Kamu petugas pendataan skill. Langkah wajib: "
    "1) baca isi README lewat tool baca_skill dengan url yang diberikan pengguna; "
    "2) panggil tool daftar_skill dengan nama, deskripsi, dan tags hasil bacaan itu. "
    "Aturan: nama = bagian terakhir url (nama repo) apa adanya, huruf kecil; "
    "deskripsi = ringkasan 1-3 kalimat dalam bahasa Indonesia berdasarkan README, "
    "bukan kalimat promosi kosong; tags = 3 sampai 6 kata kunci dipisah koma. "
    "Jangan mengarang fakta yang tidak ada di README. Jika tool mengembalikan error, "
    "jangan mengulang dengan nama lain: laporkan error tersebut apa adanya."
)


def buat_pendaftar() -> Agent:
    """Agent pendaftar; dibuat sekali lalu dipakai untuk banyak url."""
    return Agent(
        model=get_model(),
        tools=[baca_skill, daftar_skill],
        system_prompt=SISTEM_DAFTAR,
        callback_handler=None,
    )


def catat_pemakaian(agen: str, hasil, mulai: float) -> None:
    """Satu baris log: durasi, jumlah putaran model, dan konsumsi token."""
    m = hasil.metrics
    u = m.accumulated_usage
    logger.info(
        "{} | {:.1f}s | {} putaran | token masuk={} keluar={} total={} cache_baca={}",
        agen,
        time.perf_counter() - mulai,
        m.cycle_count,
        u.get("inputTokens", 0),
        u.get("outputTokens", 0),
        u.get("totalTokens", 0),
        u.get("cacheReadInputTokens", 0),
    )
    return {
        "cycle_counts" : m.cycle_count,
        "input_tokens" : u.get("inputTokens", 0),
        "output_tokens" : u.get("outputTokens", 0),
        "total_tokens" : u.get("totalTokens", 0),
        "cache_tokens" : u.get("cacheReadInputTokens", 0),
    }


def pilih_skill(permintaan: str, agent: Agent | None = None) -> dict:
    """Pilih skill paling cocok untuk `permintaan` (bahasa bebas)."""
    mulai = time.perf_counter()
    hasil = (agent or buat_router())(permintaan, structured_output_model=SkillKeluar)
    metrics = catat_pemakaian("pilih_skill", hasil, mulai)
    result = hasil.structured_output.model_dump()
    result["metrics"] = metrics
    return result


def simpan_skill_dari_url(url: str, agent: Agent | None = None) -> dict:
    """Minta agent mengisi field dari README lalu menyimpannya lewat tool daftar_skill.

    Hasilnya dibaca ulang dari database lewat detail_skill, jadi yang dikembalikan
    adalah baris yang benar-benar tersimpan, bukan klaim model.
    """
    mulai = time.perf_counter()
    hasil = (agent or buat_pendaftar())(
        f"Daftarkan skill dari url {url}", structured_output_model=DataSkill
    )
    catat_pemakaian("daftar_skill", hasil, mulai)
    data = cast(DataSkill, hasil.structured_output)
    tersimpan = detail_skill(data.nama)
    if "error" in tersimpan:
        logger.warning("daftar_skill gagal url={} alasan={}", url, tersimpan["error"])
        return {"error": f"agent gagal menyimpan: {tersimpan['error']}", "usulan": data.model_dump()}
    if tersimpan["url"].rstrip("/") != url.rstrip("/"):
        return {
            "error": f"nama '{data.nama}' sudah dipakai skill lain ({tersimpan['url']}), tidak ada yang disimpan",
            "usulan": data.model_dump(),
        }
    return tersimpan


if __name__ == "__main__":
    import json
    import sys

    arg = sys.argv[1:]
    if arg[:1] == ["daftar"]:
        hasil = simpan_skill_dari_url(arg[1] if len(arg) > 1 else "https://github.com/tiangolo/typer")
    else:
        hasil = pilih_skill(" ".join(arg) or "bikin aplikasi")
    print(json.dumps(hasil, indent=2, ensure_ascii=False))
