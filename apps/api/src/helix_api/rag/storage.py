import asyncio
from pathlib import Path
from uuid import UUID

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob.aio import BlobServiceClient


class LocalDocumentStorage:
    """Filesystem stand-in for Azure Blob Storage during local development."""

    def __init__(self, root: Path) -> None:
        self.root = root

    async def save(
        self,
        *,
        tenant_id: UUID,
        document_id: UUID,
        filename: str,
        content: bytes,
    ) -> str:
        # Keep only the final filename component so an upload cannot escape the
        # configured storage root with path traversal such as "../../secret".
        safe_name = Path(filename).name
        relative = Path("blobs") / str(tenant_id) / str(document_id) / safe_name
        target = self.root / relative

        def write() -> None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

        await asyncio.to_thread(write)
        return relative.as_posix()


class AzureBlobDocumentStorage:
    """Persist original uploads in Azure Blob Storage."""

    def __init__(self, *, connection_string: str, container_name: str) -> None:
        self.connection_string = connection_string
        self.container_name = container_name

    async def save(
        self,
        *,
        tenant_id: UUID,
        document_id: UUID,
        filename: str,
        content: bytes,
    ) -> str:
        safe_name = Path(filename).name
        blob_name = f"{tenant_id}/{document_id}/{safe_name}"

        # The async Azure client shares its connection pool beneath child clients.
        async with BlobServiceClient.from_connection_string(self.connection_string) as service:
            container = service.get_container_client(self.container_name)

            try:
                await container.create_container()
            except ResourceExistsError:
                # Creating the container is idempotent for our application setup.
                pass

            await container.upload_blob(
                name=blob_name,
                data=content,
                overwrite=True,
            )

        return blob_name
