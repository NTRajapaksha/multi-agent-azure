# Multi-Agent Customer Retention System

> An Autonomous AI System that prevents customer churn by correlating structured billing data with unstructured complaint logs to negotiate retention offers in real-time.

[![Azure](https://img.shields.io/badge/Azure-Cloud-0078D4?logo=microsoftazure)](https://azure.microsoft.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-Microservice-009688?logo=fastapi)](https://fastapi.tiangolo.com)

**Role Target:** Associate Lead Data Scientist / AI Engineer  
**Core Competencies:** Agentic AI, MLOps, Cloud Architecture (Azure), Microservices

---

## 🏗 System Architecture

This project moves beyond simple chatbots to a **Multi-Agent Cognitive Architecture**. It uses a "Team of Experts" approach where specialized AI agents collaborate to solve a business problem.

### The Workflow

1. **Ingestion (Data Engineering)**: A synthetic data pipeline generates multi-modal data:
   - **Structured**: Customer Tenure, Monthly Bill, Service Type (SQL-like data)
   - **Unstructured**: PDF Complaint Letters (Blob Storage)

2. **Perception (RAG)**: The Researcher Agent uses Vector Search (Azure Cosmos DB) to find relevant historical complaints

3. **Cognition (Reasoning)**:
   - **Analyst Agent**: Calculates a dynamic "Churn Risk Score" (0-100%) based on sentiment intensity and customer value
   - **Negotiator Agent**: Applies business logic to authorize specific offers (e.g., Full Refund vs. 10% Discount)

4. **Action (API)**: The decision is exposed via a RESTful Microservice (FastAPI) for integration with CRM systems

---

## 🚀 Key Features

### 🕵️ Agentic RAG (Retrieval-Augmented Generation)
Unlike standard RAG, the agents autonomously decide when to search the database and how to interpret the results.

### 💾 Vector Memory
Utilizes Azure Cosmos DB for NoSQL with Vector Indexing (quantizedFlat) for millisecond-latency retrieval of semantic context.

### ☁️ Serverless & Scalable
- **Data Lake**: Azure Blob Storage for raw document handling
- **Compute**: Dockerized microservice designed for Azure Container Apps (ACA) with KEDA auto-scaling capabilities

### 🛡 Enterprise-Ready Code
- **Type Safety**: Uses Pydantic models for data validation
- **Environment Isolation**: Strict separation of secrets via `.env`
- **Containerization**: Full Docker support for "Build Once, Run Anywhere"

---

## 🛠 Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Orchestration** | LangGraph | Provides cyclic graph control flow (Loops/State) superior to linear chains |
| **LLM Backend** | Google Gemini Flash | Ultra-fast, cost-effective reasoning engine with high token limits |
| **Vector Database** | Azure Cosmos DB | Native Azure integration with built-in Vector Search capabilities |
| **Data Lake** | Azure Blob Storage | Scalable storage for unstructured artifacts (PDFs) |
| **API Framework** | FastAPI | High-performance, async-native Python framework |
| **DevOps** | Docker | Ensures consistent environments from Dev to Prod |

---

## 💻 Installation & Setup

### Prerequisites

- Python 3.10+
- Docker Desktop (Optional, for containerization)
- Azure Subscription (Free Tier works)
- Google Gemini API Key (Free Tier)

### 1. Clone the Repository

```bash
git clone https://github.com/NTRajapaksha/multi-agent-azure.git
cd retention-agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the root directory (or set system variables):

```ini
GEMINI_API_KEY="your_google_ai_key"
COSMOS_ENDPOINT="https://your-cosmos-db.documents.azure.com:443/"
COSMOS_KEY="your_primary_key"
# Note: Storage connection is handled within generate_data.py for the ETL phase
```

---

## 📊 Usage Guide

### Phase 1: Data Engineering (ETL)

Generate synthetic customers and upload their "Complaint PDFs" to the Azure Data Lake.

```bash
python generate_data.py
# Output: ✅ Success: Uploaded 3668-QPYBK_complaint.pdf to Azure.
```

### Phase 2: Knowledge Injection

Read the PDFs, generate Vector Embeddings, and index them in Cosmos DB.

```bash
python build_memory.py
# Output: 🎉 PHASE 2 COMPLETE: Agent Memory is built!
```

### Phase 3: Run the Agent Microservice

Start the FastAPI server (Local or Docker).

**Option A: Local Python**

```bash
python main.py
```

**Option B: Docker Container**

```bash
docker build -t retention-agent:v1 .
docker run -p 8000:8000 --env-file .env retention-agent:v1
```

---

## 🧪 Testing the API

You can interact with the system via the built-in Swagger UI or curl.

### Swagger UI
Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

### CURL Command

```bash
curl -X POST "http://localhost:8000/analyze_customer" \
     -H "Content-Type: application/json" \
     -d '{"customer_id": "3668-QPYBK"}'
```

### Sample Response

```json
{
  "status": "success",
  "customer_id": "3668-QPYBK",
  "analysis": {
    "risk_score": 85,
    "reasoning": "High dissatisfaction detected due to unmet speed promises."
  },
  "decision": {
    "offer": "Full Refund + 1 Month Free Service",
    "action": "Authorized"
  }
}
```

---

## 🔮 Future Roadmap

- **Production Deployment**: Migrate the container to Azure Kubernetes Service (AKS) using Helm charts for scaling
- **Observability**: Integrate Azure Monitor / Application Insights to track Agent decision latency and token usage
- **Human-in-the-Loop**: Add a "Supervisor Node" in LangGraph to route extremely high-risk cases (>95%) to a human operator via Slack API

---

## 👨‍💻 Author

**Thathsara Rajapaksha**  
Data Science Professional | Sri Lanka 🇱🇰

Built with ❤️ using Azure & Python

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## ⭐ Show Your Support

Give a ⭐️ if this project helped you!
