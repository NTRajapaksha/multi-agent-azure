from azure.cosmos import CosmosClient
from app.config import settings

cosmos_client = CosmosClient(settings.cosmos_endpoint, credential=settings.cosmos_key)

DB_NAME = "RetentionDB"
CONTAINER_NAME = "CustomerContext"

def get_cosmos_container():
    database = cosmos_client.get_database_client(DB_NAME)
    container = database.get_container_client(CONTAINER_NAME)
    return container
