from azure.storage.blob import BlobServiceClient
from app.config import settings

blob_service_client = BlobServiceClient.from_connection_string(settings.storage_connection_string)
CONTAINER_NAME = "complaints"

def get_blob_container_client():
    return blob_service_client.get_container_client(CONTAINER_NAME)
