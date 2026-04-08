from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from caseware_poc.platform import PlatformApp


class QueryRequest(BaseModel):
    tenant_id: str
    question: str


ROOT_DIR = Path(__file__).resolve().parents[2]
platform_app = PlatformApp(ROOT_DIR)
api = FastAPI(title="Caseware AI-Ready Platform POC", version="0.1.0")


@api.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@api.post("/bootstrap")
def bootstrap() -> dict:
    platform_app.reset()
    return platform_app.bootstrap()


@api.post("/query")
def query(request: QueryRequest) -> dict:
    response = platform_app.answer(request.tenant_id, request.question)
    return response.model_dump(mode="json")
