"""Model builder: satu tempat untuk ganti backend LLM.

Default demo: LiteLLM -> OmniRoute lokal (OpenAI-compatible).
Produksi di AWS: hapus LiteLLM, pakai BedrockModel() — kredensial dari IAM role.
"""

import os

from strands.models import BedrockModel
from strands.models.litellm import LiteLLMModel

# Model yang dipakai demo (lewat gateway lokal)
LOCAL_MODEL = os.getenv("STRANDS_MODEL", "openai/deepseek/deepseek-flash")
LOCAL_BASE = os.getenv("OPENAI_BASE_URL", "http://localhost:20128/v1")


def local_model() -> LiteLLMModel:
    """LiteLLM menembak endpoint OpenAI-compatible mana pun (Ollama, vLLM, gateway)."""
    return LiteLLMModel(
        client_args={
            "api_base": LOCAL_BASE,
            "api_key": os.getenv("OPENAI_API_KEY", "dummy"),
        },
        model_id=LOCAL_MODEL,
        params={"max_tokens": 800, "temperature": 0.3},
    )


def bedrock_model() -> BedrockModel:
    """Jalur AWS asli: tanpa api_key, kredensial dari env/role."""
    return BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def get_model():
    return bedrock_model() if os.getenv("USE_BEDROCK") == "1" else local_model()
