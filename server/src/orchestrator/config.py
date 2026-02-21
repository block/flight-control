from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/orchestrator.db"
    master_key: str = ""  # Fernet key for encrypting credentials
    default_admin_key: str = "admin"  # Default API key for bootstrapping
    server_host: str = "0.0.0.0"
    server_port: int = 8080
    worker_heartbeat_timeout: int = 90  # seconds before worker considered dead
    log_level: str = "INFO"
    artifact_storage_path: str = "./data/artifacts"

    model_config = {"env_prefix": "ORCH_"}


settings = Settings()
