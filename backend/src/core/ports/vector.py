from abc import ABC, abstractmethod
from typing import Any, Dict, List


class IVectorDatabase(ABC):
    @abstractmethod
    async def upsert(
        self,
        collection_name: str,
        vector_id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ) -> None:
        """Upserts a vector and corresponding metadata payload."""
        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        filter_payload: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """Queries vectors using optional metadata filtering."""
        pass


class IObjectStorage(ABC):
    @abstractmethod
    async def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Uploads file data and returns the reachable URI/Key."""
        pass

    @abstractmethod
    async def download_file(self, bucket_name: str, object_name: str) -> bytes:
        """Downloads raw bytes of a file."""
        pass
