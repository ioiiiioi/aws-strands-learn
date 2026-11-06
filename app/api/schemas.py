from pydantic import BaseModel, ConfigDict, Field



class PilihanSkill(BaseModel):
    """Hasil pemilihan: satu skill, atau kosong jika tidak ada yang cocok."""

    name: str | None = Field(default=None, description="nama skill persis seperti di database")
    url: str | None = None
    alasan: str = Field(description="kenapa skill ini cocok dengan permintaan")
    alternatif: list[str] = Field(default_factory=list, description="nama skill lain yang mendekati")


class UrlMasuk(BaseModel):
    url: str = Field(
        pattern=r"^https://github\.com/[\w.-]+/[\w.-]+/?$",
        description="url repo GitHub, contoh https://github.com/owner/repo",
        examples=["https://github.com/tiangolo/typer"],
    )


class SkillTersimpan(BaseModel):
    """Baris skill seperti yang benar-benar ada di database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    description: str
    tags: str


class SkillKeluar(BaseModel):
    """Hasil agent pemilih skill; name/url kosong jika tidak ada yang cocok."""

    name: str | None = None
    url: str | None = None
    alasan: str
    alternatif: list[str] = Field(default_factory=list)
    metrics: dict | None = None


class DataSkill(BaseModel):
    """Field yang harus diisi agent saat mendaftarkan skill baru."""

    nama: str = Field(description="nama repo, huruf kecil, tanpa spasi")
    deskripsi: str = Field(description="ringkasan 1-3 kalimat dari README")
    tags: str = Field(description="3 sampai 6 kata kunci dipisah koma")
