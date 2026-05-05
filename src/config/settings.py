"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for CocoMind.

    All values are loaded from environment variables (or .env file).
    """

    # Azure Document Intelligence
    azure_docint_key: str = ""
    azure_docint_endpoint: str = ""

    # Anthropic Claude
    anthropic_api_key: str = ""

    # PostgreSQL
    database_url: str = "postgresql://cocomind:cocomind@localhost:5432/cocomind"

    # ChromaDB
    chromadb_path: str = "./data/chromadb"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Whoosh
    whoosh_index_path: str = "./data/whoosh_index"

    # Audit
    audit_db_path: str = "./data/audit/audit.db"

    # DSC
    dsc_pkcs11_lib: str = ""

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Confidence thresholds
    ocr_confidence_floor: float = 0.72
    retrieval_score_floor: float = 0.35
    llm_confidence_floor: float = 0.70

    # Blacklist matching
    blacklist_jaro_winkler_threshold: float = 0.92

    # EMD
    emd_min_validity_days: int = 45
    emd_min_percentage: float = 2.0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
