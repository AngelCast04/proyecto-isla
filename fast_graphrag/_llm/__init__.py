__all__ = [
    "BaseLLMService",
    "BaseEmbeddingService",
    "DefaultEmbeddingService",
    "DefaultLLMService",
    "format_and_send_prompt",
    "OpenAIEmbeddingService",
    "OpenAILLMService",
    "GeminiLLMService",
    "GeminiEmbeddingService",
    "VoyageAIEmbeddingService",
]

from ._base import BaseEmbeddingService, BaseLLMService, format_and_send_prompt
from ._default import DefaultEmbeddingService, DefaultLLMService
from ._llm_openai import OpenAIEmbeddingService, OpenAILLMService


def __getattr__(name: str):
    """Carga diferida de proveedores opcionales (Gemini/Voyage) para builds más ligeros (p. ej. Vercel)."""
    if name in ("GeminiLLMService", "GeminiEmbeddingService"):
        from ._llm_genai import GeminiEmbeddingService, GeminiLLMService

        return GeminiLLMService if name == "GeminiLLMService" else GeminiEmbeddingService
    if name == "VoyageAIEmbeddingService":
        from ._llm_voyage import VoyageAIEmbeddingService

        return VoyageAIEmbeddingService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
