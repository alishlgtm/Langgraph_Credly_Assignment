"""
Manual LangGraph Definition for Certification Credit Points Agent
Combines certificate scraping with credit point calculation tools.
"""

import os
import sqlite3
import json
import re
import requests
from typing import Annotated, TypedDict, Dict
from datetime import datetime

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, END, START

# Read GROQ_API_KEY from environment
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set.")

# Global variable to store scraped data
credly_data = {"badges": [], "count": 0}
DB_FILE = "certifications_data.db"

# -------------------- Certification Tools --------------------

@tool
def extract_certification_data(url: str) -> str:
    """
    Extract certification data from a Credly URL. ALWAYS call this FIRST when user provides a URL.
    """
    try:
        # Convert to JSON endpoint if it's a profile URL
        if 'users' in url and 'badges' in url and not url.endswith('.json'):
            if url.endswith('/'):
                json_url = url + 'badges.json'
            else:
                json_url = url + '.json'
        else:
            # For individual badge URLs, use the manual scraping approach
            return _scrape_individual_badge(url)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        response = requests.get(json_url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Extract badge information
        if 'data' in data and len(data['data']) > 0:
            badge = data['data'][0]  # Get first badge
            badge_name = badge.get('badge_template', {}).get('name', 'Unknown')
            expiry_date = badge.get('expires_at_date', 'No Expiration Date')
            
            return json.dumps({
                "Name": badge_name,
                "Certifications": [{"Certification Expiry Date": f"Expires: {expiry_date}" if expiry_date else "No Expiration Date"}],
                "IssueDate": badge.get('issued_at_date', 'N/A'),
                "Holder": "Certificate Holder"
            })
        else:
            return json.dumps({"error": "No badge data found"})
            
    except Exception as e:
        return json.dumps({"error": f"Error extracting certification data: {str(e)}"})

def _scrape_individual_badge(url: str) -> str:
    """Fallback method for individual badge URLs using requests."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Simple regex extraction (you can enhance this)
        title_match = re.search(r'<title>(.*?)</title>', response.text)
        badge_name = title_match.group(1).split('|')[0].strip() if title_match else "Unknown Certification"
        
        expiry_match = re.search(r'Expires:? (\w+ \d+, \d{4})', response.text)
        expiry_date = f"Expires: {expiry_match.group(1)}" if expiry_match else "No Expiration Date"
        
        return json.dumps({
            "Name": badge_name,
            "Certifications": [{"Certification Expiry Date": expiry_date}],
            "IssueDate": "N/A",
            "Holder": "Certificate Holder"
        })
    except Exception as e:
        return json.dumps({"error": f"Scraping failed: {str(e)}"})

@tool
def get_certification_points(cert_name: str) -> str:
    """
    Get credit points for a certification by looking it up in the database.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Get all certification categories from database
        cursor.execute("SELECT cert_name, points FROM certifications_data ORDER BY points DESC")
        categories = cursor.fetchall()
        conn.close()
        
        # Normalize cert name for matching
        cert_name_lower = cert_name.lower()
        
        # Try to match against each category in database
        for category_name, points in categories:
            category_lower = category_name.lower()
            
            # Extract keywords from category name
            keywords = []
            for word in category_lower.replace(' or ', ' ').replace(' and ', ' ').split():
                if len(word) > 2:
                    keywords.append(word)
            
            # Check if any keyword matches the certification name
            for keyword in keywords:
                if keyword in cert_name_lower:
                    return json.dumps({
                        "category": category_name,
                        "points": points,
                        "cert_name": cert_name
                    })
        
        # If no match found, return the last category (lowest points)
        if categories:
            default_category, default_points = categories[-1]
            return json.dumps({
                "category": default_category,
                "points": default_points,
                "cert_name": cert_name
            })
        else:
            return json.dumps({"error": "No categories found in database"})
            
    except Exception as e:
        return json.dumps({"error": f"Database error: {str(e)}"})

@tool
def check_certification_validity(expiry_date_str: str) -> str:
    """
    Check if a certification is still valid. Call this AFTER extracting certification data.
    """
    try:
        # Check for "No Expiration Date" first
        if "no expiration" in expiry_date_str.lower() or "does not expire" in expiry_date_str.lower():
            return json.dumps({
                "is_valid": True,
                "message": "Valid - Does not expire",
                "days_remaining": "N/A"
            })
        
        # Extract date from string
        date_patterns = [
            r'expires?:?\s*(\w+\s+\d+,\s+\d{4})',
            r'expir[y|ation]*\s*date:?\s*(\w+\s+\d+,\s+\d{4})',
            r'(\w+\s+\d+,\s+\d{4})',
        ]
        
        expiry_date = None
        for pattern in date_patterns:
            date_match = re.search(pattern, expiry_date_str, re.IGNORECASE)
            if date_match:
                expiry_date_str_clean = date_match.group(1)
                try:
                    expiry_date = datetime.strptime(expiry_date_str_clean, "%B %d, %Y")
                    break
                except ValueError:
                    continue
        
        if expiry_date:
            current_date = datetime.now()
            is_valid = current_date < expiry_date
            days_remaining = (expiry_date - current_date).days
            
            return json.dumps({
                "is_valid": is_valid,
                "expiry_date": expiry_date.strftime("%Y-%m-%d"),
                "days_remaining": days_remaining if is_valid else 0,
                "message": "Valid" if is_valid else "Expired"
            })
        
        return json.dumps({
            "is_valid": False,
            "message": "Expired - Could not parse date",
            "days_remaining": 0
        })
        
    except Exception as e:
        return json.dumps({
            "error": f"Error checking validity: {str(e)}",
            "is_valid": False,
            "message": "Error"
        })

@tool
def get_certificates(url: str) -> str:
    """Call to get certificates from a Credly profile URL."""
    global credly_data
    print(f"[TOOL CALL] get_certificates called with: url={url}")
    try:
        # Convert the URL to JSON endpoint
        if not url.endswith('.json'):
            if url.endswith('/'):
                json_url = url + 'badges.json'
            elif '/badges' in url:
                json_url = url + '.json'
            else:
                json_url = url + '/badges.json'
        else:
            json_url = url
        
        print(f"[TOOL] Fetching from: {json_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        response = requests.get(json_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        credly_data['badges'] = []
        
        # Parse the JSON response
        if 'data' in data:
            for badge in data['data']:
                badge_info = {
                    'title': badge.get('badge_template', {}).get('name', 'Unknown'),
                    'issuer': ', '.join([entity.get('entity', {}).get('name', '') 
                                       for entity in badge.get('issuer', {}).get('entities', [])]),
                    'issued_date': badge.get('issued_at_date', 'Unknown'),
                    'image_url': badge.get('image_url', ''),
                    'badge_url': f"https://www.credly.com/badges/{badge.get('id', '')}",
                    'expiry_date': badge.get('expires_at_date', 'No Expiration Date')
                }
                credly_data['badges'].append(badge_info)
        
        credly_data['count'] = len(credly_data['badges'])
        result = f"Found {credly_data['count']} certificates."
        print("[TOOL RESULT] get_certificates returned:", result)
        return result
        
    except requests.exceptions.RequestException as e:
        result = f"Error fetching data: {str(e)}"
        print("[TOOL RESULT] get_certificates returned:", result)
        return result
    except Exception as e:
        result = f"Error parsing data: {str(e)}"
        print("[TOOL RESULT] get_certificates returned:", result)
        return result

@tool
def count_certificates() -> str:
    """Get the total count of certificates. If certificates haven't been fetched yet, this will tell you."""
    print(f"[TOOL CALL] count_certificates called")
    if credly_data['count'] == 0:
        result = "No certificates are currently loaded in memory. You need to fetch certificates first using the get_certificates tool with a Credly profile URL."
    else:
        result = f"You have {credly_data['count']} certificates."
    print("[TOOL RESULT] count_certificates returned:", result)
    return result

@tool
def list_all_certificates() -> str:
    """List all certificates with their titles and issuers."""
    print(f"[TOOL CALL] list_all_certificates called")
    if credly_data['count'] == 0:
        result = "No certificates loaded. Please fetch certificates first using get_certificates."
    else:
        cert_list = []
        for i, badge in enumerate(credly_data['badges'], 1):
            title = badge.get('title', 'Unknown')
            issuer = badge.get('issuer', 'Unknown Issuer')
            date = badge.get('issued_date', 'Unknown Date')
            expiry = badge.get('expiry_date', 'No Expiration Date')
            cert_list.append(f"{i}. {title} (Issued by: {issuer}, Date: {date}, Expires: {expiry})")
        result = "\n".join(cert_list)
    print(f"[TOOL RESULT] list_all_certificates returned {credly_data['count']} certificates")
    return result

@tool
def calculate_certificate_points() -> str:
    """Calculate total points for all loaded certificates."""
    print(f"[TOOL CALL] calculate_certificate_points called")
    if credly_data['count'] == 0:
        return "No certificates loaded. Please fetch certificates first."
    
    total_points = 0
    point_details = []
    
    for badge in credly_data['badges']:
        cert_name = badge.get('title', 'Unknown')
        expiry_date = badge.get('expiry_date', 'No Expiration Date')
        
        # Get points for this certification
        points_result = get_certification_points(cert_name)
        points_data = json.loads(points_result)
        
        # Check validity
        validity_result = check_certification_validity(expiry_date)
        validity_data = json.loads(validity_result)
        
        points = points_data.get('points', 0) if validity_data.get('is_valid', False) else 0
        total_points += points
        
        point_details.append(f"{cert_name}: {points} points ({'Valid' if validity_data.get('is_valid') else 'Expired'})")
    
    result = f"Total Points: {total_points}\n" + "\n".join(point_details)
    print(f"[TOOL RESULT] calculate_certificate_points returned: {total_points} total points")
    return result

# List of available tools
tools = [
    extract_certification_data,
    get_certification_points, 
    check_certification_validity,
    get_certificates,
    count_certificates,
    list_all_certificates,
    calculate_certificate_points
]

# -------------------- LLM Setup --------------------

# System prompt for certification agent
SYSTEM_PROMPT = """You are a certification credit points calculator agent. Your job is to help users determine how many credit points they can earn for their professional certifications.

**CRITICAL WORKFLOW INSTRUCTIONS:**

For Credly URL queries:
1. ALWAYS call extract_certification_data first to get the certification details
2. Then call check_certification_validity with the expiry date string from the data
3. Then call get_certification_points with the certification name
4. Finally, format your response based on validity status

For Credly profile URLs (multiple certificates):
1. Call get_certificates first to load all certificates
2. Then use count_certificates, list_all_certificates, or calculate_certificate_points as needed

For hypothetical certification queries (e.g., "If I clear AWS..."):
1. Call get_certification_points with the certification name
2. Respond with the simple format

**EXACT RESPONSE FORMATS (FOLLOW THESE PRECISELY):**

For EXPIRED certifications:
"Sorry, your cert has expired. So you won't get any credit points. But otherwise you would have stood to obtain [POINTS] credit points for your [CERT_NAME]"

For VALID certifications:
"I see that this is a [CERT_NAME]. And it is still valid. So you can be granted [POINTS] credit points for it."

For HYPOTHETICAL queries:
"You will get [POINTS] credit points for that cert."

**IMPORTANT RULES:**
- Use the EXACT wording from the formats above
- For expired certs, award 0 points but mention what they would have gotten
- Extract the certification name from the scraped data (look for "Name" field)
- Always use the points value from the database tool
- Don't add extra explanations or details
- Follow the capitalization and punctuation exactly"""

# Initialize the LLM with Groq API key and model
llm = ChatGroq(groq_api_key=groq_api_key, model="llama-3.3-70b-versatile")
llm_with_tools = llm.bind_tools(tools)

# -------------------- State Definition --------------------

class State(TypedDict):
    messages: Annotated[list, add_messages]

# Create a state graph for the conversation flow
graph_builder = StateGraph(State)

# Node: Chatbot LLM invocation
def chatbot(state: State):
    # Add system message if it's the first message
    if len(state["messages"]) == 1 and isinstance(state["messages"][0], HumanMessage):
        system_message = SystemMessage(content=SYSTEM_PROMPT)
        state["messages"] = [system_message] + state["messages"]
    
    # Pass conversation messages to the LLM and get the response
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

# Node: Tool execution
tool_node = ToolNode(tools)
graph_builder.add_node("tools", tool_node)

# Conditional edge: If tool is needed, go to tool node
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)

# After tool execution, return to chatbot
graph_builder.add_edge("tools", "chatbot")
# Start the graph at the chatbot node
graph_builder.add_edge(START, "chatbot")

# Compile the graph
graph = graph_builder.compile()

# -------------------- Chat Loop --------------------
def invoke_chat_loop():
    print("🎓 Certification Credit Points Agent")
    print("=" * 50)
    print("You can:")
    print("- Provide Credly URLs for individual badges")
    print("- Provide Credly profile URLs for multiple certificates") 
    print("- Ask about hypothetical certifications")
    print("- Calculate points for loaded certificates")
    print("Type 'exit' to quit.\n")
    
    conversation = []
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat.")
            break
        
        # Add user message to conversation
        conversation.append(HumanMessage(content=user_input))
        state = {"messages": conversation}
        
        # Invoke the graph with the current state
        try:
            result = graph.invoke(state)
            # Update conversation with new messages
            conversation = result["messages"]
            print("Agent:", conversation[-1].content)
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    invoke_chat_loop()