from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    server_url: str = "http://localhost:8080"
    api_key: str = "admin"
    worker_name: str = ""
    labels: str = ""  # comma-separated key=value pairs
    workspace_id: str = "default"
    poll_interval: int = 5  # seconds
    heartbeat_interval: int = 30  # seconds
    log_batch_interval: int = 2  # seconds

    model_config = {"env_prefix": "ORCH_"}


settings = WorkerSettings()
