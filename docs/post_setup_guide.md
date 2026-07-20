# Next Steps: Running the Multi-Agent System

Once you have completed the [azure_setup_guide.md](file:///C:/Users/VICTUS/.gemini/antigravity/brain/e7a7c5cc-c7d6-4daf-8966-6471848252c7/azure_setup_guide.md) and your Azure resources are provisioned, follow this step-by-step guide to configure, ingest data, and run the multi-agent application.

> [!NOTE]
> All commands below should be executed from within the `multi-agent-azure-v2` directory.

## Step 1: Configure Your Environment

1. Copy the `.env.example` file to create a new `.env` file:
   ```bash
   cp .env.example .env
   ```
2. Open the `.env` file in your editor and fill in the values. You can retrieve all of the Azure keys by running these CLI commands in your terminal (make sure your variables from the setup guide are still exported):

   - **GEMINI_API_KEY**: Get this from [Google AI Studio](https://aistudio.google.com/app/apikey).
   
   - **COSMOS_ENDPOINT**:
     ```bash
     az cosmosdb show --name $COSMOS_NAME --resource-group $RESOURCE_GROUP --query documentEndpoint -o tsv
     ```
   
   - **COSMOS_KEY**:
     ```bash
     az cosmosdb keys list --name $COSMOS_NAME --resource-group $RESOURCE_GROUP --query primaryMasterKey -o tsv
     ```
   
   - **SQL_CONNECTION_STRING**:
     First, get your server's fully qualified domain name (FQDN):
     ```bash
     az sql server show --name $SQL_SERVER_NAME --resource-group $RESOURCE_GROUP --query fullyQualifiedDomainName -o tsv
     ```
     Then, replace `<FQDN>` and `<YOUR_PASSWORD>` in this string:
     `Driver={ODBC Driver 18 for SQL Server};Server=tcp:<FQDN>,1433;Database=RetentionDB;Uid=dbadmin;Pwd=<YOUR_PASSWORD>;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;`
   
   - **STORAGE_CONNECTION_STRING**:
     ```bash
     az storage account show-connection-string --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP --query connectionString -o tsv
     ```
   
   - **APPINSIGHTS_CONNECTION_STRING**:
     ```bash
     az monitor app-insights component show --app $APP_INSIGHTS --resource-group $RESOURCE_GROUP --query connectionString -o tsv
     ```
## Step 2: Install Dependencies

Ensure you are using Python 3.10+ and install the required packages:

```bash
pip install -r requirements.txt
```

## Step 3: Generate and Ingest Data

The system needs mock customer profiles and complaint PDFs to analyze. We will generate these synthetically.

1. **Populate the SQL Database & Storage Account:**
   Run the data generation script. This will use Gemini to write complaint letters, save them as PDFs, upload them to Azure Blob Storage, and insert customer billing data into your Azure SQL Database.
   ```bash
   python scripts/generate_data.py
   ```
   *Expected Output: "🎉 Phase 1: Data Engineering Complete."*

2. **Build the Vector Memory (Cosmos DB):**
   Run the memory building script. This will download the PDFs, chunk the text, generate vector embeddings using Gemini, and index them in Cosmos DB for semantic search.
   ```bash
   python scripts/build_memory.py
   ```
   *Expected Output: "🎉 Phase 2: Memory Build Complete!"*

## Step 4: Run the Multi-Agent API Locally

With your data securely in Azure, you can now start the FastAPI server that hosts the LangGraph agents.

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Step 5: Test the System

You can test the system using `curl` from another terminal tab. We will test it on customer `3668-QPYBK`, which is one of the high-risk profiles we generated.

```bash
curl -X POST "http://localhost:8000/analyze_customer" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: super-secret-key-123" \
     -d '{"customer_id": "3668-QPYBK"}'
```

### What happens behind the scenes:
1. **Researcher Node**: Uses tool-calling to fetch the SQL profile and perform a vector search on Cosmos DB.
2. **Analyst Node**: Evaluates the retrieved data using Gemini and outputs a structured JSON risk score.
3. **Graph Routing**: If the score is >90%, it routes to the **Supervisor Node** (human review). Otherwise, it routes to the **Negotiator Node** to issue an offer.

## (Optional) Step 6: Deploy to Azure Container Apps

When you are ready to deploy this to the cloud:
1. Push this repository to GitHub.
2. Go to your GitHub repository settings -> Secrets and variables -> Actions.
3. Add `ACR_NAME` (e.g., `acrretention12345`).
4. Add `AZURE_CREDENTIALS` (JSON output from creating a service principal).
5. Trigger the GitHub Action, which will build the Docker image and deploy it to Azure Container Apps.
