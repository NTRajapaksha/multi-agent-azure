from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent_graph import app as agent_app  # Import your Graph

# 1. Define the API
app = FastAPI(
    title="Multi-Agent Retention System",
    description="An Agentic System that autonomously analyzes churn and negotiates offers.",
    version="1.0.0"
)

# 2. Define Request Model (Input Schema)
class RetentionRequest(BaseModel):
    customer_id: str

# 3. Define the Endpoint
@app.post("/analyze_customer")
async def analyze_customer(request: RetentionRequest):
    """
    Triggers the Agent Workflow: Researcher -> Analyst -> Negotiator
    """
    print(f"📥 API Request received for: {request.customer_id}")
    
    try:
        # Run the LangGraph Workflow
        result = agent_app.invoke({"customer_id": request.customer_id})
        
        # Return structured JSON
        return {
            "status": "success",
            "customer_id": result["customer_id"],
            "analysis": {
                "risk_score": result["churn_risk"],
                "reasoning": result["risk_reasoning"]
            },
            "decision": {
                "offer": result["recommended_offer"],
                "action": "Authorized" if result["churn_risk"] > 50 else "Monitor"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Health Check (Standard for Cloud Deployments)
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "retention-agent"}

if __name__ == "__main__":
    import uvicorn
    # Run server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)