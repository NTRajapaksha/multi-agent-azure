from app.clients.cosmos import get_cosmos_container
from app.clients.sql import get_db_connection
from app.clients.gemini import gemini_client, EMBEDDING_MODEL
from app.logging_config import logger

def search_complaint_history(customer_id: str) -> str:
    """
    Search past complaint records for this customer using semantic search.
    Only call this if the customer's complaint history might affect the risk assessment.
    
    Args:
        customer_id: The ID of the customer to look up.
    """
    logger.info(f"Tool called: search_complaint_history for customer {customer_id}")
    try:
        query_text = f"Complaint from customer {customer_id}"
        response = gemini_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=query_text
        )
        query_vector = response.embeddings[0].values
        
        container = get_cosmos_container()
        query = """
        SELECT TOP 3 c.text_content, VectorDistance(c.embedding, @embedding) as score 
        FROM c 
        WHERE c.customerId = @customerId
        ORDER BY VectorDistance(c.embedding, @embedding)
        """
        results = container.query_items(
            query=query,
            parameters=[
                {"name": "@embedding", "value": query_vector},
                {"name": "@customerId", "value": customer_id}
            ],
            enable_cross_partition_query=False,
            partition_key=customer_id
        )
        
        items = list(results)
        if not items:
            return "No previous complaints found for this customer."
            
        combined_complaints = "\n---\n".join([item['text_content'] for item in items])
        return combined_complaints
    except Exception as e:
        logger.error(f"Error in search_complaint_history: {e}")
        return f"Error retrieving complaints: {str(e)}"

def get_customer_profile(customer_id: str) -> dict:
    """
    Fetch structured billing/tenure data for a customer from the database.
    
    Args:
        customer_id: The ID of the customer to look up.
    """
    logger.info(f"Tool called: get_customer_profile for customer {customer_id}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Tenure, MonthlyCharges, InternetService 
            FROM Customers 
            WHERE CustomerID = ?
        """, customer_id)
        
        row = cursor.fetchone()
        if not row:
            return {"error": "Customer not found"}
            
        return {
            "tenure_months": row.Tenure,
            "monthly_bill": float(row.MonthlyCharges),
            "service_type": row.InternetService
        }
    except Exception as e:
        logger.error(f"Error in get_customer_profile: {e}")
        return {"error": f"Database error: {str(e)}"}
