import os
import pandas as pd
from fpdf import FPDF
from google import genai
from azure.storage.blob import BlobServiceClient

# --- CONFIGURATION ---
# 1. Google Gemini Config
GEMINI_API_KEY = "YOUR_GEMINI_KEY"

# 2. Azure Storage Config
STORAGE_CONNECTION_STRING = "PASTE_YOUR_AZURE_CONNECTION_STRING_HERE"
CONTAINER_NAME = "complaints"

# --- SETUP CLIENTS ---

# Configure Gemini (NEW SDK)
genai_client = genai.Client(api_key=GEMINI_API_KEY)
GEMINI_MODEL = "models/gemini-flash-latest"

# Configure Azure Blob Storage
blob_service_client = BlobServiceClient.from_connection_string(
    STORAGE_CONNECTION_STRING
)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

# --- MOCK DATA (High Risk Customers) ---
data = {
    'customerID': ['7590-VHVEG', '5575-GNVDE', '3668-QPYBK', '7795-CFOCW', '9237-HQITU'],
    'Tenure': [1, 34, 2, 45, 2],
    'MonthlyCharges': [29.85, 56.95, 53.85, 42.30, 70.70],
    'InternetService': ['DSL', 'DSL', 'Fiber optic', 'DSL', 'Fiber optic'],
    'Churn': ['No', 'No', 'Yes', 'No', 'Yes']
}

df = pd.DataFrame(data)
target_customers = df[df['Churn'] == 'Yes']

print(f"Targeting {len(target_customers)} customers for synthetic complaint generation...")

# --- FUNCTIONS ---

def generate_complaint_with_gemini(row):
    """Uses Google Gemini to generate a synthetic customer complaint."""
    prompt = f"""
Roleplay as a frustrated customer writing a formal complaint letter to a telecom company.

Context:
- Customer ID: {row['customerID']}
- Tenure: {row['Tenure']} months
- Monthly Bill: ${row['MonthlyCharges']}
- Service: {row['InternetService']}

Issues:
- Frequent connection drops
- Internet speed slower than advertised
- Threatening to cancel service if unresolved

Tone: Angry but professional.
Constraints:
- Under 150 words
- Do NOT include placeholders like [Your Name]
"""

    try:
        response = genai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return "Error generating complaint text."

def create_pdf(text, filename):
    """Converts generated text to a PDF file."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    sanitized_text = text.encode("latin-1", "replace").decode("latin-1")
    pdf.multi_cell(0, 10, sanitized_text)
    pdf.output(filename)

def upload_to_azure(filename, blob_name):
    """Uploads the PDF to Azure Blob Storage."""
    try:
        with open(filename, "rb") as data:
            container_client.upload_blob(
                name=blob_name,
                data=data,
                overwrite=True
            )
        print(f"✅ Success: Uploaded {blob_name} to Azure.")
    except Exception as e:
        print(f"❌ Azure Upload Error: {e}")

# --- EXECUTION LOOP ---
for _, row in target_customers.iterrows():
    cid = row['customerID']
    print(f"\n--- Processing Customer {cid} ---")

    # 1. Generate complaint text
    complaint_text = generate_complaint_with_gemini(row)
    print(f"Generated text ({len(complaint_text)} chars)...")

    # 2. Create PDF
    pdf_filename = f"{cid}_complaint.pdf"
    create_pdf(complaint_text, pdf_filename)

    # 3. Upload to Azure
    upload_to_azure(pdf_filename, pdf_filename)

    # # 4. Cleanup
    # if os.path.exists(pdf_filename):
    #     os.remove(pdf_filename)

print("\n🎉 Data Engineering Phase Complete. Check your Azure Storage Container!")
