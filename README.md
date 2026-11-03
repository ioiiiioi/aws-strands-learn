# AWS Strands Agents — catatan ringkas

SDK agent dari AWS. Prinsipnya **model-driven**: kamu kasih model + daftar tool + system
prompt, lalu model sendiri yang memutuskan tool mana dipanggil, berapa kali, kapan
berhenti. Tidak ada graph/DAG yang harus kamu tulis manual (kecuali memang mau).

- Paket: `strands-agents` (PyPI) — versi saat catatan ini ditulis **1.63.0**, Python ≥ 3.10
- Docs: <https://strandsagents.com> · Repo: <https://github.com/strands-agents/sdk-python>
- Lisensi Apache-2.0, dependency inti cuma `boto3`, `pydantic`, `mcp`, `opentelemetry`

## Kegunaan

| Kebutuhan | Strands memberi |
|---|---|
| Agent yang pakai tool Python | dekorator `@tool`, skema tool digenerate dari type hint + docstring |
| Output terstruktur (bukan teks bebas) | `structured_output_model=PydanticModel` |
| Banyak agent kerja bareng | `Swarm` (saling handoff) dan `GraphBuilder` (alur tetap, bisa bercabang) |
| Ganti-ganti LLM | `BedrockModel` (default), `LiteLLMModel`, `OpenAIModel`, `AnthropicModel`, `OllamaModel` |
| Sambung tool eksternal | MCP client bawaan (stdio/HTTP), plus A2A untuk agent-to-agent |
| Observability | OpenTelemetry built-in (trace ke Langfuse/Jaeger/X-Ray/CloudWatch) |
| Ingatan antar sesi | `FileSessionManager`, `S3SessionManager`, `AgentCoreMemorySessionManager` |
| Deploy | bungkus jadi Lambda/Fargate/ECS, atau **Bedrock AgentCore Runtime** |

Cocok kalau: butuh agent cepat jalan, tool-nya banyak tapi alurnya tidak kaku, dan/atau
sudah di ekosistem AWS (IAM role, Bedrock, CloudWatch).

Kurang cocok kalau: butuh orkestrasi deterministik kompleks (LangGraph lebih eksplisit),
atau tidak mau dependency `boto3`.

## Instal

```bash
uv init my-agent && cd my-agent
uv add strands-agents                    # inti (default Bedrock)
uv add "strands-agents[litellm]"         # kalau mau provider lain via LiteLLM
uv add "strands-agents[otel]"            # tracing OTLP
```

Model default = Bedrock, kredensial diambil dari env/role AWS biasa:

```bash
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

## Sample di repo ini

Semua sample jalan dengan **model lokal** (OmniRoute, OpenAI-compatible) supaya tidak
butuh kredensial AWS. Ganti `USE_BEDROCK=1` untuk pakai Bedrock sungguhan.

```bash
cp .env.example .env      # isi OPENAI_BASE_URL + OPENAI_API_KEY
uv run --env-file .env python -m demo.agent        # agent + custom tool
uv run --env-file .env python -m demo.structured   # output Pydantic dari teks struk
uv run --env-file .env python -m demo.multiagent   # Graph 2 node (ada juga demo_swarm())
```

`uv --env-file` baca `.env` tanpa perlu dependency `python-dotenv`.

### 1. Agent + tool (`demo/agent.py`)

```python
from strands import Agent, tool

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
    model=get_model(),                      # Bedrock atau LiteLLM
    tools=[hitung_total],
    system_prompt="Kamu asisten belanja. Pakai tool untuk aritmatika.",
)
hasil = agent("Beli 3 kopi @18.000 diskon 10%, bayar berapa?")
print(hasil)                                # teks final
print(hasil.metrics.get_summary()["tool_usage"])   # tool apa saja dipanggil
```

Output nyata (dijalankan, bukan karangan):

```
Tool #1: hitung_total
Bruto Rp54.000, diskon Rp5.400 → bayar Rp48.600.
hitung_total: 1x, sukses 1, error 0
cycles: 2 | token: 1891
```

Tool boleh balikin `dict`/`str`/Pydantic; error di tool otomatis dikembalikan ke model
sebagai `error` sehingga agent bisa memperbaiki sendiri, bukan crash.

### 2. Structured output (`demo/structured.py`)

```python
class Struk(BaseModel):
    merchant: str
    items: list[ItemBelanja]
    total: int
    kategori: list[str]

hasil = agent(teks_struk, structured_output_model=Struk)
struk: Struk = hasil.structured_output      # sudah tervalidasi Pydantic
```

Terverifikasi: teks struk 4 baris → JSON rapi (`total: 33500`, 3 item, kategori
`minuman/makanan/kebersihan`). `stop_reason` jadi `tool_use` karena Strands memaksa model
memanggil tool internal `structured_output`.

### 3. Multi-agent (`demo/multiagent.py`)

```python
# Graph: alur eksplisit
builder = GraphBuilder()
builder.add_node(riset, "riset")
builder.add_node(tulis, "tulis")
builder.add_edge("riset", "tulis")
builder.set_entry_point("riset")
hasil = builder.build()("Topik: kopi dan produktivitas.")
print([n.node_id for n in hasil.execution_order])   # ['riset', 'tulis']

# Swarm: agent saling serah terima lewat tool handoff_to_agent
swarm = Swarm(nodes=[peneliti, penulis], entry_point=peneliti, max_handoffs=4)
print(swarm("Jelaskan kenapa kopi bikin melek."))
```

Bedanya: **Graph** = kamu tentukan urutan; **Swarm** = agent yang pilih siapa lanjut.
Swarm butuh `name=` unik per agent dan `max_handoffs` sebagai rem biaya.

## Pitfall yang sudah kena saat bikin catatan ini

1. **`reasoningContent is not supported in multi-turn conversations with the Chat
   Completions API`** — muncul kalau model (deepseek/other reasoning model) mengirim
   blok reasoning lewat endpoint OpenAI-compatible. Tidak fatal; hilang kalau pakai
   Bedrock/Anthropic native atau model non-reasoning.
2. **`metrics.tool_usage` tidak ada** — statistik tool ada di
   `hasil.metrics.get_summary()["tool_usage"]["<nama>"]["execution_stats"]`.
3. **LiteLLM `model_id` wajib pakai prefix provider** — `openai/deepseek/deepseek-flash`
   untuk endpoint OpenAI-compatible, `ollama/llama3`, `anthropic/claude-...`.
4. **`AgentResult.message["content"]` pesan terakhir cuma berisi teks** — blok `toolUse`
   ada di pesan antara, bukan di hasil akhir. Pakai metrics kalau mau audit tool.
5. **Konstruktor model di-import dari `strands.models`, bukan `strands.models.litellm`
   untuk Bedrock** — `from strands.models import BedrockModel`,
   `from strands.models.litellm import LiteLLMModel`.
6. Swarm tanpa `max_handoffs`/`max_iterations` bisa muter-muter dan bakar token.

## Biaya & keamanan

- Setiap tool call = satu round-trip LLM. `cycles: 2` untuk satu tool = 2 request.
  Rem: `max_iterations`, `max_handoffs`, `execution_timeout` (Swarm), `node_timeout`.
- Tool jalan **di proses kamu** dengan permission penuh — validasi input kalau tool
  menyentuh filesystem/DB/shell. Jangan lempar kredensial ke system prompt.
- Guardrail Bedrock (`guardrail_id`) bisa dipasang di `BedrockModel` untuk filter
  input/output di level AWS.

## Kalau naik ke produksi

```python
from strands.models import BedrockModel
from strands.session import S3SessionManager

agent = Agent(
    model=BedrockModel(model_id="...", region_name="us-east-1"),
    tools=[...],
    session_manager=S3SessionManager(bucket="...", prefix="agent/"),
    callback_handler=None,        # matikan print streaming ke stdout
)
```

- Observability: set `OTEL_EXPORTER_OTLP_ENDPOINT` → trace otomatis (span per cycle,
  per LLM call, per tool). Bisa diarahkan ke Langfuse self-host yang sudah ada.
- Deploy: Bedrock AgentCore Runtime (container, auto-scaling, session terkelola), atau
  Lambda untuk agent pendek, atau Fargate kalau butuh proses panjang.
- MCP: `Agent(tools=[mcp_client])` — server MCP lokal (stdio) atau remote (HTTP) langsung
  jadi tool agent tanpa wrapper.

## Status

Diuji di mesin ini: `strands-agents 1.63.0`, Python 3.12, model
`deepseek/deepseek-flash` via gateway lokal `http://localhost:20128/v1`.
Ketiga sample dijalankan dan keluarannya yang tercatat di atas.
