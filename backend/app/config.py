import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str = ""
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "claims_processor"
    upload_dir: str = "./uploads"
    log_level: str = "INFO"
    
    policy_terms_path: str = str(Path(__file__).parent.parent / "policy_terms.json")
    test_cases_path: str = str(Path(__file__).parent.parent / "test_cases.json")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
