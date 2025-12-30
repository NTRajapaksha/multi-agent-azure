import os
from typing import TypedDict, Annotated
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from azure.cosmos import CosmosClient
from google import genai
from langgraph.graph import StateGraph, END

# --- CONFIGURATION (Paste your keys) ---
GEMINI_API_KEY = "PASTE_YOUR_GEMINI_KEY_HERE"
COSMOS_ENDPOINT = "PASTE_YOUR_COSMOS_URI_HERE"
COSMOS_KEY = "PASTE_YOUR_COSMOS_PRIMARY_KEY_HERE"

# --- CLIENT SETUP ---
llm = ChatGoogleGenerativeAI(
    model="models/gemini-flash-latest",
    google_api_key=GEMINI_API_KEY,
    temperature=0
)
embed_client = genai.Client(api_key=GEMINI_API_KEY)
cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
container = cosmos_client.get_database_client("RetentionDB").get_container_client("CustomerContext")

# --- 1. DEFINE THE STATE (Shared Brain) ---
class AgentState(TypedDict):
    customer_id: str
    customer_data: dict         # From Mock DB
    complaint_summary: str      # From Researcher
    churn_risk: int             # From Analyst (0-100)
    risk_reasoning: str         # From Analyst
    recommended_offer: str      # From Negotiator

# --- 2. HELPER FUNCTIONS ---
def search_knowledge_base(query_text):
    try:
        response = embed_client.models.embed_content(
            model="text-embedding-004",
            contents=query_text
        )
        query_vector = response.embeddings[0].values
        
        query = """
        SELECT TOP 1 c.text_content, VectorDistance(c.embedding, @embedding) as score 
        FROM c 
        ORDER BY VectorDistance(c.embedding, @embedding)
        """
        results = container.query_items(
            query=query,
            parameters=[{"name": "@embedding", "value": query_vector}],
            enable_cross_partition_query=True
        )
        items = list(results)
        return items[0]['text_content'] if items else "No record found."
    except Exception as e:
        return f"Error: {e}"

# --- 3. AGENT NODES ---

# AGENT A: RESEARCHER (Gathers Context)
def researcher_node(state: AgentState):
    print(f"\n🕵️  RESEARCHER: Looking up {state['customer_id']}...")
    
    # Mock Data Lookup
    mock_db = {
        '3668-QPYBK': {'tenure': 2, 'bill': 53.85, 'service': 'Fiber Optic'},
        '9237-HQITU': {'tenure': 2, 'bill': 70.70, 'service': 'Fiber Optic'}
    }
    profile = mock_db.get(state['customer_id'], {'tenure': 0, 'bill': 0})
    
    # RAG Lookup
    complaint = search_knowledge_base(f"Complaint from customer {state['customer_id']}")
    
    # Summarization
    prompt = f"Summarize this complaint in 1 sentence: {complaint}"
    summary = llm.invoke(prompt).content
    
    return {"customer_data": profile, "complaint_summary": summary}

# AGENT B: ANALYST (Calculates Risk)
def analyst_node(state: AgentState):
    print("📊 ANALYST: Calculating Churn Risk...")
    
    prompt = f"""
    Act as a Churn Analyst. Evaluate the risk (0-100%).
    
    Profile: Tenure {state['customer_data']['tenure']} months, Bill ${state['customer_data']['bill']}
    Complaint: "{state['complaint_summary']}"
    
    Output strictly in this format:
    Score: [Number]
    Reason: [One sentence explanation]
    """
    
    result = llm.invoke(prompt).content
    
    # Parse the messy LLM output
    try:
        lines = result.split('\n')
        score = int([line for line in lines if "Score:" in line][0].split(":")[1].strip())
        reason = [line for line in lines if "Reason:" in line][0].split(":")[1].strip()
    except:
        score = 85 # Fallback if parsing fails
        reason = "High dissatisfaction detected."

    return {"churn_risk": score, "risk_reasoning": reason}

# AGENT C: NEGOTIATOR (Decides Strategy)
def negotiator_node(state: AgentState):
    print("🤝 NEGOTIATOR: Designing Offer...")
    
    risk = state['churn_risk']
    
    # Business Logic for Offer
    if risk > 80:
        offer = "Full Refund + 1 Month Free Service"
    elif risk > 50:
        offer = "50% Discount on Next Bill"
    else:
        offer = "Free Speed Upgrade"
        
    return {"recommended_offer": offer}

# --- 4. BUILD THE GRAPH (The Workflow) ---
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("researcher", researcher_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("negotiator", negotiator_node)

# Add Edges (The Logic Flow)
workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "analyst")
workflow.add_edge("analyst", "negotiator")
workflow.add_edge("negotiator", END)

# Compile
app = workflow.compile()

# --- 5. EXECUTION ---
if __name__ == "__main__":
    test_id = "3668-QPYBK"
    print(f"--- STARTING RETENTION WORKFLOW FOR {test_id} ---")
    
    result = app.invoke({"customer_id": test_id})
    
    print("\n" + "="*50)
    print("🚀 FINAL DECISION REPORT")
    print("="*50)
    print(f"Customer:  {result['customer_id']}")
    print(f"Complaint: {result['complaint_summary']}")
    print(f"Risk:      {result['churn_risk']}% ({result['risk_reasoning']})")
    print(f"OFFER:     {result['recommended_offer']}")
    print("="*50)