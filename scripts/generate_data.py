import os
import sys
import pandas as pd
from fpdf import FPDF
from google import genai
from dotenv import load_dotenv
import pyodbc
import time
from tenacity import retry, wait_exponential, stop_after_attempt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.clients.blob import get_blob_container_client
from app.clients.sql import get_db_connection
from app.clients.gemini import gemini_client, GEMINI_MODEL

load_dotenv()

data = {
    'CustomerID': ['7590-VHVEG', '5575-GNVDE', '3668-QPYBK', '7795-CFOCW', '9237-HQITU'],
    'Tenure': [1, 34, 2, 45, 2],
    'MonthlyCharges': [29.85, 56.95, 53.85, 42.30, 70.70],
    'InternetService': ['DSL', 'DSL', 'Fiber optic', 'DSL', 'Fiber optic'],
    'Churn': ['No', 'No', 'Yes', 'No', 'Yes']
}

df = pd.DataFrame(data)

def setup_sql_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Customers' and xtype='U')
        CREATE TABLE Customers (
            CustomerID VARCHAR(50) PRIMARY KEY,
            Tenure INT,
            MonthlyCharges FLOAT,
            InternetService VARCHAR(50),
            Churn VARCHAR(3)
        )
    """)
    conn.commit()
    print("✅ SQL Table 'Customers' is ready.")
    
    for _, row in df.iterrows():
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Customers WHERE CustomerID = ?)
            INSERT INTO Customers (CustomerID, Tenure, MonthlyCharges, InternetService, Churn)
            VALUES (?, ?, ?, ?, ?)
        """, row['CustomerID'], row['CustomerID'], row['Tenure'], row['MonthlyCharges'], row['InternetService'], row['Churn'])
    conn.commit()
    print("✅ Customer data inserted into SQL.")

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5))
def generate_complaint(row):
    prompt = f"""
    Roleplay as a frustrated customer writing a formal complaint letter to a telecom company.
    Context: Customer ID {row['CustomerID']}, Tenure {row['Tenure']} months, Bill ${row['MonthlyCharges']}, Service {row['InternetService']}.
    Issues: Frequent connection drops, slow speed.
    Tone: Angry but professional. Under 150 words. No placeholders.
    """
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    return response.text

def create_pdf(text, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    sanitized_text = text.encode("latin-1", "replace").decode("latin-1")
    pdf.multi_cell(0, 10, sanitized_text)
    pdf.output(filename)

def upload_to_blob(filename, blob_name):
    container_client = get_blob_container_client()
    try:
        if not container_client.exists():
            container_client.create_container()
            
        with open(filename, "rb") as data:
            container_client.upload_blob(name=blob_name, data=data, overwrite=True)
        print(f"✅ Uploaded {blob_name} to Blob Storage.")
    except Exception as e:
        print(f"❌ Blob Upload Error: {e}")

if __name__ == "__main__":
    setup_sql_table()
    
    target_customers = df[df['Churn'] == 'Yes']
    for _, row in target_customers.iterrows():
        cid = row['CustomerID']
        print(f"\n--- Generating complaint for {cid} ---")
        text = generate_complaint(row)
        pdf_name = f"{cid}_complaint.pdf"
        create_pdf(text, pdf_name)
        upload_to_blob(pdf_name, pdf_name)
        os.remove(pdf_name)
        time.sleep(2) # Give the API a brief rest
        
    print("\n🎉 Phase 1: Data Engineering Complete.")
