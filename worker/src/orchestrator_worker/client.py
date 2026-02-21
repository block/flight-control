import httpx

from orchestrator_worker.config import settings


class ServerClient:
    def __init__(self):
        self.base_url = f"{settings.server_url}/api/v1"
        self.headers = {
            "Authorization": f"Bearer {settings.api_key}",
            "X-Workspace-ID": settings.workspace_id,
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=30.0,
        )

    async def register(self, name: str, labels: dict) -> dict:
        async with self._client() as client:
            resp = await client.post(
                "/workers/register",
                json={"name": name, "labels": labels},
            )
            resp.raise_for_status()
            return resp.json()

    async def heartbeat(self, worker_id: str, status: str = "online") -> None:
        async with self._client() as client:
            resp = await client.post(
                "/workers/heartbeat",
                json={"worker_id": worker_id, "status": status},
            )
            resp.raise_for_status()

    async def poll(self, worker_id: str) -> dict | None:
        async with self._client() as client:
            resp = await client.post(
                "/workers/poll",
                params={"worker_id": worker_id},
            )
            resp.raise_for_status()
            data = resp.json()
            return data if data else None

    async def post_logs(self, run_id: str, lines: list[dict]) -> None:
        async with self._client() as client:
            resp = await client.post(
                f"/workers/runs/{run_id}/logs",
                json={"lines": lines},
            )
            resp.raise_for_status()

    async def upload_artifact(
        self,
        run_id: str,
        filename: str,
        data: bytes,
        content_type: str = "text/plain",
    ) -> dict:
        async with self._client() as client:
            resp = await client.post(
                f"/workers/runs/{run_id}/artifacts",
                files={"file": (filename, data, content_type)},
            )
            resp.raise_for_status()
            return resp.json()

    async def complete_run(
        self,
        run_id: str,
        worker_id: str,
        status: str,
        result: str | None = None,
        exit_code: int | None = None,
    ) -> None:
        async with self._client() as client:
            resp = await client.post(
                f"/workers/runs/{run_id}/complete",
                params={"worker_id": worker_id},
                json={
                    "status": status,
                    "result": result,
                    "exit_code": exit_code,
                },
            )
            resp.raise_for_status()
