import os
import sys
from google import genai
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings

def list_embedding_models():
    # Initialize the client using the API key from your .env
    client = genai.Client(api_key=settings.gemini_api_key)
    
    print("Fetching available models...")
    models = client.models.list()
    
    print("\n--- Available Embedding Models ---")
    found = False
    for model in models:
        if "embed" in model.name.lower() or (model.description and "embed" in model.description.lower()):
            found = True
            print(f"Model ID: {model.name}")
            print(f"Display Name: {model.display_name}")
            print(f"Description: {model.description}")
            print("-" * 40)
            
    if not found:
        print("No embedding models found for this API key.")

if __name__ == "__main__":
    list_embedding_models()
