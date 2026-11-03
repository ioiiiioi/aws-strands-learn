"""01 — agent paling kecil: model + system prompt + satu tool Python.

Jalan: uv run python -m demo.agent
"""

from strands import Agent, tool

from demo.model import get_model


@tool
def hitung_total(harga: float, jumlah: int, diskon_persen: float = 0.0) -> dict:
    """Hitung total belanja setelah diskon.

    Args:
        harga: harga satuan dalam rupiah
        jumlah: banyaknya barang
        diskon_persen: potongan 0-100 persen
    """
    bruto = harga * jumlah
    potongan = bruto * diskon_persen / 100
    return {"bruto": bruto, "potongan": potongan, "total": bruto - potongan}


agent = Agent(
    model=get_model(),
    tools=[hitung_total],
    system_prompt=(
        "Kamu asisten belanja. Kalau perlu aritmatika, panggil tool hitung_total. "
        "Jawab ringkas dalam Bahasa Indonesia."
    ),
)

if __name__ == "__main__":
    hasil = agent("Beli 3 kopi @18.000 dengan diskon 10%, berapa yang harus dibayar?")
    print("\n--- jawaban ---")
    print(hasil)
    print("\n--- tool yang dipanggil ---")
    summary = hasil.metrics.get_summary()
    for nama, m in summary["tool_usage"].items():
        st = m["execution_stats"]
        print(f"{nama}: {st['call_count']}x, sukses {st['success_count']}, error {st['error_count']}")
    print("cycles:", summary["total_cycles"], "| token:", summary["accumulated_usage"]["totalTokens"])
