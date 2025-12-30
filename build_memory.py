import os
import glob
import time
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from google import genai 
from pypdf import PdfReader

# --- CONFIGURATION ---
GEMINI_API_KEY = "PASTE_YOUR_GEMINI_KEY_HERE"
COSMOS_ENDPOINT = "PASTE_YOUR_COSMOS_URI_HERE"
COSMOS_KEY = "PASTE_YOUR_COSMOS_PRIMARY_KEY_HERE"

# Database Details
DB_NAME = "RetentionDB"
CONTAINER_NAME = "CustomerContext"
EMBEDDING_MODEL = "text-embedding-004" # The standard embedding model

# --- CLIENT SETUP ---
# 1. Setup Google Client (New SDK Style)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# 2. Setup Cosmos Client
cosmos_client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)

# --- 1. SETUP DATABASE WITH VECTORS ---
def setup_database():
    print("Connecting to Cosmos DB...")
    database = cosmos_client.create_database_if_not_exists(id=DB_NAME)
    
    # Define Vector Policy (768 Dimensions for Gemini)
    vector_embedding_policy = {
        "vectorEmbeddings": [
            {
                "path": "/embedding",
                "dataType": "float32",
                "distanceFunction": "cosine",
                "dimensions": 768 
            }
        ]
    }

    # Define Indexing Policy
    indexing_policy = {
        "includedPaths": [{"path": "/*"}],
        "excludedPaths": [{"path": "/_etag/?"}, {"path": "/embedding/*"}],
        "vectorIndexes": [
            {"path": "/embedding", "type": "quantizedFlat"}
        ]
    }

    # Create Container
    try:
        container = database.create_container_if_not_exists(
            id=CONTAINER_NAME,
            partition_key=PartitionKey(path="/customerId"),
            vector_embedding_policy=vector_embedding_policy,
            indexing_policy=indexing_policy
        )
        print("✅ Container 'CustomerContext' ready (Vector Support Enabled).")
        return container
    except exceptions.CosmosHttpResponseError as e:
        print(f"\n❌ ERROR: Could not create container. Details: {e.message}")
        return None

# --- 2. HELPER FUNCTIONS ---

def get_embedding(text):
    """Uses the NEW Google GenAI SDK to create embeddings."""
    try:
        # Rate limit safety (free tier)
        time.sleep(1) 
        
        # New SDK Syntax
        response = ai_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text
        )
        
        # The new SDK returns an object with an 'embeddings' list.
        # We need the first one's values.
        return response.embeddings[0].values
    except Exception as e:
        print(f"Embedding Error: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    """Reads the PDF file text."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"PDF Read Error: {e}")
        return ""

# --- 3. EXECUTION LOOP ---
def run_ingestion():
    container = setup_database()
    if not container: return

    # Find PDFs (make sure they are in the same folder as this script)
    pdf_files = glob.glob("*_complaint.pdf")
    
    if not pdf_files:
        print("⚠️ No PDF files found! Did you run generate_data.py?")
        return

    print(f"Found {len(pdf_files)} PDFs to process.")

    for pdf_file in pdf_files:
        customer_id = pdf_file.split("_")[0]
        print(f"--- Processing {customer_id} ---")
        
        # A. Read Text
        text_content = extract_text_from_pdf(pdf_file)
        if not text_content: continue
        
        # B. Generate Vector
        vector = get_embedding(text_content)
        if not vector: 
            print("Skipping due to empty vector.")
            continue

        # C. Prepare Document
        doc = {
            "id": f"{customer_id}_doc",
            "customerId": customer_id,
            "type": "complaint_log",
            "text_content": text_content, 
            "embedding": vector
        }
        
        # D. Upload to Cosmos DB
        container.upsert_item(doc)
        print(f"✅ Stored memory for {customer_id}")

    print("\n🎉 PHASE 2 COMPLETE: Agent Memory is built!")

if __name__ == "__main__":
    run_ingestion()