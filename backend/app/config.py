from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", hide_input_in_errors=True
    )
    environment: str = "production"
    data_dir: Path = Path("/data")
    auth_mode: str = "entra"
    demo_token: str = ""
    entra_tenant_id: str = ""
    entra_client_id: str = ""
    entra_audience: str = ""
    entra_group_id: str = ""
    entra_scope: str = "access_as_user"
    llm_provider: str = "b3"
    ollama_url: str = "http://simplfaq-ollama:11434"
    ollama_model: str = "qwen2.5:1.5b"
    llm_timeout: int = 600
    ollama_max_prompt_chars: int = Field(default=18000, ge=2000, le=60000)
    training_model: str = "Qwen/Qwen2.5-0.5B-Instruct"
    b3_api_url: str = ""
    b3_api_key: str = ""
    b3_model: str = ""
    embedding_provider: str = "fastembed"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_cache_dir: Path | None = None
    chunk_size: int = 1400
    chunk_overlap: int = 180
    retrieval_top_k: int = 10
    retrieval_threshold: float = 0.12
    max_upload_mb: int = 25
    max_batch_mb: int = 100
    max_extracted_chars: int = 2_000_000
    prompt_version: str = "simplfaq-template-2.0"

    @model_validator(mode="after")
    def check_config(self):
        if self.auth_mode not in {"entra", "demo", "local"}:
            raise ValueError("AUTH_MODE inválido")
        if self.llm_provider not in {"b3", "demo", "ollama"}:
            raise ValueError("LLM_PROVIDER inválido")
        if self.embedding_provider not in {"fastembed", "hash"}:
            raise ValueError("EMBEDDING_PROVIDER inválido")
        if not 0 <= self.chunk_overlap < self.chunk_size or self.chunk_size < 200:
            raise ValueError("Chunk/overlap inválidos")
        if self.auth_mode == "demo" and (
            self.environment != "development" or len(self.demo_token) < 32
        ):
            raise ValueError(
                "Demo exige DEVELOPMENT e token aleatório de ao menos 32 caracteres"
            )
        if self.auth_mode == "local" and self.environment != "development":
            raise ValueError(
                "Acesso local exige ENVIRONMENT=development e porta publicada apenas em loopback"
            )
        if self.environment != "development" and (
            self.llm_provider == "demo" or self.embedding_provider == "hash"
        ):
            raise ValueError("Produção exige B3 GPT e embeddings semânticos")
        if self.auth_mode == "entra" and not all(
            [
                self.entra_tenant_id,
                self.entra_client_id,
                self.entra_audience,
                self.entra_group_id,
            ]
        ):
            raise ValueError("Configure tenant, client, audience e grupo Entra ID")
        if self.llm_provider == "b3" and (
            not self.b3_api_url.startswith("https://")
            or not self.b3_api_key
            or not self.b3_model
        ):
            raise ValueError("B3 GPT exige URL HTTPS, chave e modelo")
        return self


@lru_cache
def settings():
    return Settings()
