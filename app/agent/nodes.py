from app.agent.state import AgentState, CustomerProfile, RiskAssessment
from app.agent.tools import search_complaint_history, get_customer_profile
from app.clients.gemini import gemini_client, GEMINI_MODEL
from app.logging_config import logger
from pydantic import BaseModel
from google.genai.types import GenerateContentConfig

class ResearcherOutput(BaseModel):
    customer_profile: CustomerProfile
    complaint_context: str

def researcher_node(state: AgentState) -> dict:
    logger.info(f"--- RESEARCHER NODE: {state.customer_id} (Retry: {state.retry_count}) ---")
    
    prompt = f"""
    You are a Customer Research Agent. Gather all necessary information about customer '{state.customer_id}'.
    Use the provided tools to fetch their profile and complaint history.
    """
    
    try:
        chat = gemini_client.chats.create(
            model=GEMINI_MODEL, 
            config=GenerateContentConfig(
                tools=[search_complaint_history, get_customer_profile],
                temperature=0.0
            )
        )
        
        chat.send_message(prompt)
        
        format_prompt = "Now, output the gathered information exactly according to the requested JSON schema."
        response = chat.send_message(
            format_prompt,
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ResearcherOutput
            )
        )
        
        output = ResearcherOutput.model_validate_json(response.text)
        return {
            "customer_profile": output.customer_profile,
            "complaint_context": output.complaint_context
        }
    except Exception as e:
        logger.error(f"Researcher Error: {e}")
        return {"error": f"Research failed: {str(e)}"}

def analyst_node(state: AgentState) -> dict:
    logger.info(f"--- ANALYST NODE: {state.customer_id} ---")
    
    if state.error:
        return {}
        
    prompt = f"""
    Act as a Churn Analyst. Evaluate the churn risk (0-100%).
    
    Customer Profile:
    - Tenure: {state.customer_profile.tenure_months} months
    - Monthly Bill: ${state.customer_profile.monthly_bill}
    - Service: {state.customer_profile.service_type}
    
    Complaint Context:
    "{state.complaint_context}"
    
    Provide your risk score, reasoning, and your confidence level (high/medium/low).
    """
    
    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RiskAssessment,
                temperature=0.2
            )
        )
        
        assessment = RiskAssessment.model_validate_json(response.text)
        return {"risk_assessment": assessment}
    except Exception as e:
        logger.error(f"Analyst Error: {e}")
        return {"error": f"Analysis failed: {str(e)}"}

def negotiator_node(state: AgentState) -> dict:
    logger.info(f"--- NEGOTIATOR NODE: {state.customer_id} ---")
    
    if state.error or not state.risk_assessment:
        return {}
        
    risk = state.risk_assessment.score
    
    if risk > 80:
        offer = "Full Refund + 1 Month Free Service"
    elif risk > 50:
        offer = "50% Discount on Next Bill"
    else:
        offer = "Free Speed Upgrade"
        
    return {"recommended_offer": offer}

def supervisor_node(state: AgentState) -> dict:
    logger.info(f"--- SUPERVISOR NODE: {state.customer_id} ---")
    
    if state.error:
        return {}
        
    logger.warning(f"High risk ({state.risk_assessment.score}%) detected for {state.customer_id}. Flagging for human review.")
    
    return {
        "requires_human_approval": True,
        "recommended_offer": "PENDING_SUPERVISOR_APPROVAL"
    }
