from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import researcher_node, analyst_node, negotiator_node, supervisor_node
from app.logging_config import logger

def route_after_analyst(state: AgentState) -> str:
    if state.error:
        return END

    if not state.risk_assessment:
        if state.retry_count >= 2:
            return END
        return "increment_retry"
        
    if state.risk_assessment.confidence == "low":
        if state.retry_count >= 2:
            logger.warning(f"Max retries reached for low confidence on {state.customer_id}. Forcing supervisor route.")
            return "supervisor"
        return "increment_retry"
        
    if state.risk_assessment.score > 90:
        return "supervisor"
        
    return "negotiator"

def increment_retry(state: AgentState):
    return {"retry_count": state.retry_count + 1}

workflow = StateGraph(AgentState)

workflow.add_node("researcher", researcher_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("negotiator", negotiator_node)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("increment_retry", increment_retry)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "analyst")

workflow.add_conditional_edges(
    "analyst",
    route_after_analyst,
    {
        "increment_retry": "increment_retry",
        "supervisor": "supervisor",
        "negotiator": "negotiator",
        END: END
    }
)

workflow.add_edge("increment_retry", "researcher")
workflow.add_edge("negotiator", END)
workflow.add_edge("supervisor", END)

agent_app = workflow.compile()
