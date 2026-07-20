import os
import sys
import glob
import time
from pypdf import PdfReader
from azure.cosmos import PartitionKey, exceptions
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.clients.gemini import gemini_client, EMBEDDING_MODEL
from app.clients.cosmos import cosmos_client, DB_NAME, CONTAINER_NAME
from app.clients.blob import get_blob_container_client

load_dotenv()

def setup_cosmos_db():
    print("Setting up Cosmos DB...")
    database = cosmos_client.create_database_if_not_exists(id=DB_NAME)
    
    vector_policy = {
        "vectorEmbeddings": [
            {"path": "/embedding", "dataType": "float32", "distanceFunction": "cosine", "dimensions": 768}
        ]
    }

    indexing_policy = {
        "includedPaths": [{"path": "/*"}],
        "excludedPaths": [{"path": "/_etag/?"}, {"path": "/embedding/*"}],
        "vectorIndexes": [{"path": "/embedding", "type": "quantizedFlat"}]
    }

    try:
        container = database.create_container_if_not_exists(
            id=CONTAINER_NAME,
            partition_key=PartitionKey(path="/customerId"),
            vector_embedding_policy=vector_policy,
            indexing_policy=indexing_policy
        )
        print("✅ Container ready (Vector Support Enabled).")
        return container
    except exceptions.CosmosHttpResponseError as e:
        print(f"❌ ERROR creating container: {e.message}")
        return None

def download_pdfs():
    print("Downloading PDFs from Blob Storage...")
    container_client = get_blob_container_client()
    blobs = container_client.list_blobs()
    files = []
    for blob in blobs:
        if blob.name.endswith(".pdf"):
            with open(blob.name, "wb") as f:
                f.write(container_client.download_blob(blob.name).readall())
            files.append(blob.name)
    return files

def get_embedding(text):
    time.sleep(1)
    response = gemini_client.models.embed_content(model=EMBEDDING_MODEL, contents=text)
    return response.embeddings[0].values

if __name__ == "__main__":
    container = setup_cosmos_db()
    if not container:
        sys.exit(1)
        
    pdf_files = download_pdfs()
    print(f"Found {len(pdf_files)} PDFs.")
    
    for pdf_file in pdf_files:
        customer_id = pdf_file.split("_")[0]
        print(f"--- Processing {customer_id} ---")
        
        reader = PdfReader(pdf_file)
        text_content = "".join([page.extract_text() for page in reader.pages])
        
        vector = get_embedding(text_content)
        
        doc = {
            "id": f"{customer_id}_doc",
            "customerId": customer_id,
            "type": "complaint_log",
            "text_content": text_content, 
            "embedding": vector
        }
        
        container.upsert_item(doc)
        print(f"✅ Stored memory for {customer_id}")
        os.remove(pdf_file)
        
    print("\n🎉 Phase 2: Memory Build Complete!")
