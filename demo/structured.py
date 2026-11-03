"""02 — structured output: model wajib isi Pydantic, bukan teks bebas.

Jalan: uv run python -m demo.structured
"""

from pydantic import BaseModel, Field

from strands import Agent

from demo.model import get_model


class ItemBelanja(BaseModel):
    nama: str
    qty: int = Field(ge=1)
    harga_satuan: int = Field(ge=0)


class Struk(BaseModel):
    merchant: str
    items: list[ItemBelanja]
    total: int = Field(ge=0)
    kategori: list[str] = Field(description="kategori pengeluaran")


agent = Agent(model=get_model(), system_prompt="Kamu parser struk belanja.")

TEKS = """Indomaret 12/10
Aqua 600ml 2x5000
Roti tawar 1x17000
Sabun Lifebuoy 1x6500
Total 33500"""

if __name__ == "__main__":
    hasil = agent(TEKS, structured_output_model=Struk)
    struk: Struk = hasil.structured_output
    print(struk.model_dump_json(indent=2))
    print("\nstop_reason:", hasil.stop_reason)
