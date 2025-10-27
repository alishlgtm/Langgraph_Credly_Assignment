"""
Manual LangGraph Definition for Dynamic Certification Credit Points Agent
Updated for LangGraph Studio compatibility
"""

import os
import json
import re
import requests
from typing import Annotated, TypedDict, Dict, List, Any
from datetime import datetime
from urllib.parse import urlparse

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, END, START

# Read GROQ_API_KEY from environment
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set.")

# -------------------- Load Certification Data --------------------

def load_certification_data() -> List[Dict]:
    """Load certification data from JSON file."""
    try:
        with open('certifications.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("certifications.json file not found. Please ensure it exists in the current directory.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in certifications.json: {e}")

CERTIFICATION_DATA = load_certification_data()

# -------------------- State Definition --------------------

class State(TypedDict):
    messages: Annotated[list, add_messages]

# -------------------- Tools (Updated for LangGraph Studio) --------------------

@tool
def extract_certification_data(url: str) -> Dict[str, Any]:
    """
    Extract certification data from ANY Credly or certification URL.
    Returns certification name, dates, and platform information.
    """
    try:
        # Validate URL format
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return {"error": "Invalid URL format"}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {"error": f"Failed to fetch URL: HTTP {response.status_code}"}
        
        # Extract certification name from page title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', response.text, re.IGNORECASE)
        cert_name = "Unknown Certification"
        
        if title_match:
            title = title_match.group(1)
            cert_name = _extract_cert_name_from_title(title)
        
        # Try to extract dates
        issue_date = _extract_date_from_text(response.text, "issued", "issue")
        expiry_date = _extract_date_from_text(response.text, "expires", "expiry", "expiration")
        
        return {
            "cert_name": cert_name,
            "source_url": url,
            "issue_date": issue_date or "Not specified",
            "expiry_date": expiry_date or "Not specified",
            "platform": "Credly"
        }
        
    except Exception as e:
        return {"error": f"Error processing URL: {str(e)}"}

@tool
def get_certification_points(cert_name: str, category: str = "Any Professional or Specialty") -> Dict[str, Any]:
    """
    Get credit points for a certification from the JSON data.
    The category parameter helps in better matching certifications.
    """
    try:
        cert_name_lower = cert_name.lower()
        best_match = None
        best_score = 0
        
        for cert_entry in CERTIFICATION_DATA:
            json_cert_name = cert_entry.get("certificate_name", "")
            json_cert_lower = json_cert_name.lower()
            
            # Calculate match score
            score = _calculate_match_score(cert_name_lower, json_cert_lower)
            
            # Update best match if this is better
            if score > best_score:
                best_score = score
                best_match = cert_entry
        
        if best_match and best_score >= 40:
            return {
                "cert_name": cert_name,
                "category": category,
                "points": best_match.get("credit_points", 0),
                "match_confidence": f"{best_score}%",
                "status": "Found in database"
            }
        else:
            # Estimate points based on category and keywords
            points = _estimate_points_by_category(category, cert_name)
            return {
                "cert_name": cert_name,
                "category": category,
                "points": points,
                "match_confidence": "Estimated by category",
                "status": "Not found in database, using estimation"
            }
            
    except Exception as e:
        return {
            "error": f"Error looking up certification: {str(e)}",
            "cert_name": cert_name,
            "category": category,
            "points": 0
        }

@tool
def check_certification_validity(expiry_date: str) -> Dict[str, Any]:
    """
    Check if a certification is still valid based on expiry date.
    Returns validity status and days remaining if valid.
    """
    try:
        if expiry_date.lower() in ['not specified', 'none', 'no expiry', '']:
            return {
                "is_valid": True,
                "message": "No expiry date specified - assuming valid",
                "expiry_date": "Not specified"
            }
        
        # Parse the date
        today = datetime.now().date()
        
        # Try different date formats
        date_formats = [
            '%B %d, %Y',  # January 15, 2023
            '%b %d, %Y',  # Jan 15, 2023
            '%m/%d/%Y',   # 01/15/2023
            '%Y-%m-%d',   # 2023-01-15
        ]
        
        cert_date = None
        for date_format in date_formats:
            try:
                cert_date = datetime.strptime(expiry_date, date_format).date()
                break
            except ValueError:
                continue
        
        if cert_date is None:
            return {
                "is_valid": True,
                "message": f"Could not parse expiry date: {expiry_date}",
                "expiry_date": expiry_date
            }
        
        is_valid = cert_date >= today
        days_remaining = (cert_date - today).days if is_valid else 0
        status = "Valid" if is_valid else "Expired"
        
        return {
            "is_valid": is_valid,
            "message": status,
            "expiry_date": expiry_date,
            "days_remaining": days_remaining
        }
        
    except Exception as e:
        return {
            "error": f"Error checking validity: {str(e)}",
            "expiry_date": expiry_date
        }

# -------------------- Helper Functions --------------------

def _extract_cert_name_from_title(title: str) -> str:
    """Extract certification name from page title."""
    clean_title = re.sub(r' - Credly$| \| Credly$| - Badge$', '', title, flags=re.IGNORECASE)
    clean_title = re.sub(r'^Badge: ', '', clean_title, flags=re.IGNORECASE)
    return clean_title.strip()

def _extract_date_from_text(text: str, *keywords: str) -> str:
    """Extract date containing any of the specified keywords."""
    date_pattern = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{4}\b|\b\d{1,2}/\d{1,2}/\d{4}\b'
    
    for keyword in keywords:
        keyword_pattern = f"{keyword}[^<]*?({date_pattern})"
        match = re.search(keyword_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return ""

def _calculate_match_score(user_input: str, db_cert: str) -> int:
    """Calculate how well the user input matches a database certification."""
    if user_input == db_cert:
        return 100
    elif user_input in db_cert:
        return 80
    elif db_cert in user_input:
        return 70
    
    user_terms = set(user_input.split())
    db_terms = set(db_cert.split())
    
    common_terms = user_terms.intersection(db_terms)
    if common_terms:
        return len(common_terms) * 15
    
    user_words = user_input.split()
    db_words = db_cert.split()
    
    matching_words = sum(1 for word in user_words if any(db_word.startswith(word) for db_word in db_words))
    if matching_words > 0:
        return matching_words * 20
    
    return 0

def _estimate_points_by_category(category: str, cert_name: str) -> int:
    """Estimate points based on certification category."""
    category_lower = category.lower()
    cert_lower = cert_name.lower()
    
    # Use category if provided
    if 'foundational' in category_lower or 'practitioner' in category_lower:
        return 10
    elif 'associate' in category_lower:
        return 5
    elif 'professional' in category_lower or 'expert' in category_lower:
        return 10
    elif 'specialty' in category_lower or 'advanced' in category_lower:
        return 10
    
    # Fallback to keyword matching in cert name
    if any(word in cert_lower for word in ['foundational', 'fundamental', 'practitioner', 'essentials']):
        return 10
    elif any(word in cert_lower for word in ['associate', 'developer', 'administrator']):
        return 5
    elif any(word in cert_lower for word in ['professional', 'expert', 'architect', 'engineer']):
        return 10
    elif any(word in cert_lower for word in ['specialty', 'specialist', 'advanced']):
        return 10
    else:
        return 5

# -------------------- Graph Definition --------------------

def create_certification_agent():
    """Create and compile the LangGraph ReAct agent."""
    
    # Initialize LLM
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=groq_api_key
    )
    
    # Define tools
    tools = [
        extract_certification_data,
        get_certification_points,
        check_certification_validity
    ]
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    
    def chatbot(state: State):
        """Chatbot node that decides whether to use tools or respond directly."""
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}
    
    # Create graph
    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)
    
    tool_node = ToolNode(tools)
    graph_builder.add_node("tools", tool_node)
    
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
        {
            "tools": "tools",
            "end": END,
        }
    )
    
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")
    
    return graph_builder.compile()

# Create the app instance for LangGraph Studio
app = create_certification_agent()

def run_agent(user_input: str):
    """
    Run the certification credit agent with a user input.
    
    Args:
        user_input: User's question or Credly URL
        
    Returns:
        Agent's response
    """
    # Prepend system message to the conversation
    initial_state = {
        "messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_input)
        ]
    }
    
    result = app.invoke(initial_state)
    
    # Get the last message (agent's final response)
    last_message = result["messages"][-1]
    return last_message.content

# Example usage
if __name__ == "__main__":
    print("Certification Credit Points Agent (ReAct)")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "How many points for AWS Solutions Architect Professional?",
        "Check this certification: https://www.credly.com/badges/e192db17-f8c5-46aa-8f99-8a565223f1d6",
        "Is my Terraform certification still valid if it expires in January 2023?",
        "What about Google Cloud Professional Architect?"
    ]
    
    for query in test_queries:
        print(f"\nUser: {query}")
        try:
            response = run_agent(query)
            print(f"Agent: {response}")
        except Exception as e:
            print(f"Error: {e}")
