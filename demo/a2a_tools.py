"""04 — Agent sebagai tool: agent-to-agent di dalam satu proses.

Pola inti Strands: spesialis dibungkus `agent.as_tool()`, lalu orkestrator yang
memilih spesialis mana yang dipanggil. Tiga hal yang diuji di sini:

  1. dasar            -> orkestrator memanggil 2 spesialis sekaligus
  2. preserve_context -> state sub-agent di-reset (False) vs disimpan (True)
  3. delegate         -> hasil sub-agent langsung jadi jawaban akhir (hemat 1 call)

Jalan: uv run --env-file .env python -m demo.a2a_tools
"""

from strands import Agent, tool

from demo.model import get_model


def _mk(**kwargs) -> Agent:
    """Agent tanpa streaming verbose — output demo tetap bersih."""
    kwargs.setdefault("callback_handler", None)
    return Agent(model=get_model(), **kwargs)


# ---------- "ilmu" milik masing-masing spesialis ----------


@tool
def harga_sembako(komoditas: str) -> dict:
    """Harga eceran sembako per kg (data contoh)."""
    data = {"beras": 14_000, "telur": 32_000, "gula": 17_500, "minyak": 18_000}
    harga = data.get(komoditas.lower().strip())
    return {"komoditas": komoditas, "harga_per_kg": harga} if harga else {"error": "tidak ada datanya"}


@tool
def hitung_ppn(nilai: float, tarif_persen: float = 11.0) -> dict:
    """Hitung PPN dari nilai dasar."""
    ppn = nilai * tarif_persen / 100
    return {"dpp": nilai, "ppn": round(ppn, 2), "total": round(nilai + ppn, 2)}


# ---------- spesialis ----------


def spesialis_harga() -> Agent:
    return _mk(
        name="spesialis_harga",
        description="Menjawab harga sembako per kg. Pakai untuk pertanyaan harga beras/telur/gula/minyak.",
        system_prompt="Kamu spesialis harga sembako. Selalu pakai tool harga_sembako, jangan mengarang harga.",
        tools=[harga_sembako],
    )


def spesialis_pajak() -> Agent:
    return _mk(
        name="spesialis_pajak",
        description="Menghitung PPN 11%. Pakai untuk pertanyaan pajak/PPN/total setelah pajak.",
        system_prompt="Kamu spesialis perpajakan. Selalu pakai tool hitung_ppn.",
        tools=[hitung_ppn],
    )


def ringkas_tools(hasil) -> str:
    """Ringkasan tool yang dipanggil — termasuk agent-tool milik orkestrator."""
    usage = hasil.metrics.get_summary().get("tool_usage", {})
    if not usage:
        return "(tidak ada tool dipanggil)"
    baris = []
    for nama, m in usage.items():
        st = m["execution_stats"]
        baris.append(f"{nama}={st['call_count']}x")
    return ", ".join(baris)


# ---------- 1. dasar ----------


def demo_dasar() -> None:
    print("\n=== 1. DASAR: orkestrator + 2 spesialis ===")
    orkestrator = _mk(
        name="orkestrator",
        system_prompt=(
            "Kamu manajer. Jangan menjawab sendiri: panggil spesialis yang tepat, "
            "lalu rangkum jawabannya dalam Bahasa Indonesia."
        ),
        tools=[
            spesialis_harga().as_tool(name="tanya_harga"),
            spesialis_pajak().as_tool(name="tanya_pajak"),
        ],
    )
    hasil = orkestrator("Harga telur 1 kg berapa, dan kalau beli 2 kg kena PPN jadi berapa totalnya?")
    print("jawaban :", str(hasil).replace("\n", " ")[:300])
    print("tools   :", ringkas_tools(hasil))
    print("cycles  :", hasil.metrics.cycle_count, "| token:", hasil.metrics.accumulated_usage.get("totalTokens"))


# ---------- 2. preserve_context ----------


def _uji_ingatan(preserve: bool) -> tuple[Agent, str]:
    spesialis = _mk(
        name="petugas_ingat",
        description="Mengingat percakapan sebelumnya dengan user.",
        system_prompt="Jawab satu kalimat pendek.",
    )
    orkestrator = _mk(
        system_prompt="Kamu penerus pesan. Teruskan pertanyaan user ke tool.",
        tools=[
            spesialis.as_tool(
                name="tanya_petugas",
                description="Tanya petugas.",
                preserve_context=preserve,
            )
        ],
    )
    orkestrator("Nama saya Budi.")
    jawab = orkestrator("Siapa nama saya?")
    return spesialis, str(jawab).replace("\n", " ")[:120]


def demo_context() -> None:
    print("\n=== 2. preserve_context: state sub-agent antar panggilan ===")
    for preserve in (False, True):
        spesialis, jawab = _uji_ingatan(preserve)
        print(f"preserve_context={preserve:<5} | messages sub-agent={len(spesialis.messages):<2} | jawaban ke-2: {jawab}")


# ---------- 3. delegate ----------


def demo_delegate() -> None:
    print("\n=== 3. delegate=True: hasil sub-agent jadi jawaban akhir ===")
    orkestrator = _mk(
        system_prompt="Kamu hanya meneruskan ke spesialis pajak.",
        tools=[
            spesialis_pajak().as_tool(
                name="hitung_pajak",
                description="Hitung PPN dari nilai dasar.",
                delegate=True,
            )
        ],
    )
    hasil = orkestrator("Hitung PPN dari 1.000.000.")
    print("jawaban :", str(hasil).replace("\n", " ")[:200])
    print("tools   :", ringkas_tools(hasil))
    print("cycles  :", hasil.metrics.cycle_count, "(delegate=True -> tidak ada call model tambahan di orkestrator)")


if __name__ == "__main__":
    demo_dasar()
    demo_context()
    demo_delegate()
