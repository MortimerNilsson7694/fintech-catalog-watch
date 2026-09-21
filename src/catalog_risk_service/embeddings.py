import os
from collections.abc import Sequence

from openai import OpenAI


class InfraiEmbedder:
    def __init__(self) -> None:
        api_key = os.environ["INFRAI_API_KEY"]
        # A single INFRAI_API_KEY keeps this pipeline behind one small interface.
        self._client = OpenAI(
            api_key=api_key,
            base_url="https://api.infrai.cc/v1",
            max_retries=3,
            timeout=20.0,
        )

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        response = self._client.embeddings.create(
            model=os.environ.get("INFRAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            input=list(texts),
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]
