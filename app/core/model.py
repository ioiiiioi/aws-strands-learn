"""Model builder: satu tempat untuk ganti backend LLM.

Default demo: LiteLLM -> OmniRoute lokal (OpenAI-compatible).
Produksi di AWS: hapus LiteLLM, pakai BedrockModel() — kredensial dari IAM role.
Semua konfigurasi diambil dari app.core.config (pydantic settings), bukan os.getenv.
"""

from strands.models import BedrockModel
from strands.models.litellm import LiteLLMModel

from app.core.config import settings


def local_model() -> LiteLLMModel:
    """LiteLLM menembak endpoint OpenAI-compatible mana pun (Ollama, vLLM, gateway)."""
    return LiteLLMModel(
        client_args={
            "api_base": settings.OPENAI_BASE_URL,
            "api_key": settings.OPENAI_API_KEY,
        },
        model_id=settings.STRANDS_MODEL,
        params={"max_tokens": 800, "temperature": 0.3},
    )


def bedrock_model() -> BedrockModel:
    """Jalur AWS asli: tanpa api_key, kredensial dari env/role."""
    return BedrockModel(
        model_id=settings.BEDROCK_MODEL_ID,
        region_name=settings.AWS_REGION,
    )


def get_model():
    return bedrock_model() if settings.USE_BEDROCK else local_model()
