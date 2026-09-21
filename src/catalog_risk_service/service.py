from fastapi import FastAPI

from .decision import assess_catalog_event
from .embeddings import InfraiEmbedder
from .models import CatalogCheckRequest, CatalogDecision

app = FastAPI(title="Fintech Catalog Watch")


@app.post("/catalog/check", response_model=CatalogDecision)
def check_catalog(request: CatalogCheckRequest) -> CatalogDecision:
    embedder = InfraiEmbedder()
    return assess_catalog_event(request, embedder.embed)


def run() -> None:
    import uvicorn

    uvicorn.run("catalog_risk_service.service:app", host="127.0.0.1", port=8000)
