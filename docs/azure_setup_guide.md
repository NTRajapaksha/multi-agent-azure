# Azure Setup Guide

This guide provides the necessary Azure CLI scripts to provision all required resources for the Multi-Agent Customer Retention System (v2). 

> [!NOTE]
> Run these scripts in your WSL terminal in VS Code. Ensure you are logged into Azure first by running `az login`.

## 1. Define Variables
First, set up your variables in the terminal. The script uses a random string to ensure globally unique names for resources like Storage Accounts and Key Vaults.

```bash
RESOURCE_GROUP="rg-retention-agent"
LOCATION="centralindia"
RANDOM_STR=$RANDOM
COSMOS_NAME="cosmos-retention-$RANDOM_STR"
SQL_SERVER_NAME="sql-server-retention-$RANDOM_STR"
SQL_DB_NAME="RetentionDB"
SQL_ADMIN_USER="dbadmin"
SQL_ADMIN_PASS="ComplexPassword123!" # Change this before running!
STORAGE_ACCOUNT="stretention$RANDOM_STR"
LOG_ANALYTICS="log-retention-$RANDOM_STR"
APP_INSIGHTS="appi-retention-$RANDOM_STR"
KEY_VAULT="kv-retention-$RANDOM_STR"
ACR_NAME="acrretention$RANDOM_STR"
CONTAINER_APP_ENV="cae-retention-$RANDOM_STR"
```

## 2. Resource Group
Create the resource group to hold all your services.
```bash
az group create --name $RESOURCE_GROUP --location $LOCATION
```

## 3. Azure Cosmos DB (Vector Search Enabled)
Create a Serverless Cosmos DB account for storing our vector embeddings.
```bash
az cosmosdb create \
    --name $COSMOS_NAME \
    --resource-group $RESOURCE_GROUP \
    --kind GlobalDocumentDB \
    --locations regionName=$LOCATION failoverPriority=0 isZoneRedundant=False \
    --capabilities EnableServerless EnableNoSQLVectorSearch
```

## 4. Azure SQL Database
Create the SQL Server and Database for the structured customer profiles. We'll also open the firewall so you can connect from your local WSL environment.
```bash
az sql server create \
    --name $SQL_SERVER_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --admin-user $SQL_ADMIN_USER \
    --admin-password $SQL_ADMIN_PASS \
    --enable-public-network true

az sql db create \
    --resource-group $RESOURCE_GROUP \
    --server $SQL_SERVER_NAME \
    --name $SQL_DB_NAME \
    --edition Basic

# Allow your local machine to access SQL Server
az sql server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --server $SQL_SERVER_NAME \
    --name "AllowLocalClient" \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 255.255.255.255
```

## 5. Azure Blob Storage
Create the storage account and container for the raw complaint PDFs.
```bash
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS \
    --allow-blob-public-access false

# Get connection string to create container
AZURE_STORAGE_CONNECTION_STRING=$(az storage account show-connection-string --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP --output tsv)

az storage container create \
    --name complaints \
    --connection-string $AZURE_STORAGE_CONNECTION_STRING
```

## 6. Observability (Application Insights)
Set up logging for the agent execution.
```bash
az monitor log-analytics workspace create \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $LOG_ANALYTICS

az monitor app-insights component create \
    --app $APP_INSIGHTS \
    --location $LOCATION \
    --kind web \
    --resource-group $RESOURCE_GROUP \
    --workspace $LOG_ANALYTICS
```

## 7. Azure Key Vault
Securely store your Gemini API Key and other database connection strings.
```bash
az keyvault create \
    --name $KEY_VAULT \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --enable-rbac-authorization false

# Give your user account permission to add secrets
USER_OID=$(az ad signed-in-user show --query id -o tsv)
az keyvault set-policy \
    --name $KEY_VAULT \
    --resource-group $RESOURCE_GROUP \
    --object-id $USER_OID \
    --secret-permissions get list set delete
```

## 8. Deployment Infrastructure
Set up the Container Registry to hold Docker images and the Container Apps environment for serverless execution.
```bash
az acr create \
    --name $ACR_NAME \
    --resource-group $RESOURCE_GROUP \
    --sku Basic \
    --admin-enabled true

az containerapp env create \
    --name $CONTAINER_APP_ENV \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION
```

## Summary Check
Run this final script to print out the names of the resources you've created. You will need these when updating your `.env` file for the application.

```bash
echo "--- SETUP COMPLETE ---"
echo "Cosmos DB Account: $COSMOS_NAME"
echo "SQL Server: $SQL_SERVER_NAME.database.windows.net"
echo "Storage Account: $STORAGE_ACCOUNT"
echo "Application Insights: $APP_INSIGHTS"
echo "Key Vault: $KEY_VAULT"
echo "Container Registry: $ACR_NAME"
```

## 9. 💰 Managing Your Student Credits
Since you are on an Azure for Students subscription ($100 credit), this guide has been heavily optimized to be as cheap as possible:
- **Cosmos DB** uses Serverless (you only pay per query, almost $0).
- **Azure SQL** uses the Basic tier (~$5/month flat rate).
- **Container Registry** uses the Basic tier (~$5/month).
- **Container Apps** uses the Consumption tier (first 2 million requests are free).
- **App Insights / Blob / Key Vault** are practically free for small workloads.

**Total Expected Cost:** ~$10 per month.

### 🛑 How to stop all billing
When you are completely done with this project and want to ensure you don't use up any more of your $100 credit, run this single command to delete everything we just created:
```bash
az group delete --name rg-retention-agent --yes --no-wait
```
