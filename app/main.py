from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.agent.graph import agent_app
from app.logging_config import logger

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Multi-Agent Retention System v2",
    description="An Agentic System that autonomously analyzes churn with human-in-the-loop and conditional routing.",
    version="2.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

API_KEY = "super-secret-key-123"

def verify_api_key(request: Request):
    api_key = request.headers.get("X-API-Key")
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

class RetentionRequest(BaseModel):
    customer_id: str

@app.post("/analyze_customer", dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")
async def analyze_customer(request: Request, body: RetentionRequest):
    logger.info(f"📥 API Request received for: {body.customer_id}")
    
    try:
        result = agent_app.invoke({"customer_id": body.customer_id})
        
        if result.get("error"):
            logger.error(f"Workflow error for {body.customer_id}: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])
            
        return {
            "status": "success",
            "customer_id": result.get("customer_id"),
            "analysis": {
                "risk_score": result.get("risk_assessment").score if result.get("risk_assessment") else None,
                "reasoning": result.get("risk_assessment").reasoning if result.get("risk_assessment") else None,
                "confidence": result.get("risk_assessment").confidence if result.get("risk_assessment") else None,
            },
            "decision": {
                "offer": result.get("recommended_offer"),
                "requires_human_approval": result.get("requires_human_approval")
            },
            "retries": result.get("retry_count")
        }
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "retention-agent-v2"}
