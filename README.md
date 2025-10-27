# LangGraph Certification Credit Points Agent

An intelligent autonomous agent built with LangGraph that processes Credly certification URLs and calculates credit points based on certification type and validity status.

## 🎯 Goal

Provide an automated system to track, validate, and assign credit points to professional certifications from **Credly URLs**, streamlining the certification evaluation process for organizations and learning platforms.

## ✨ Features

- 🔍 **Smart URL Processing**: Automatically extracts certification details from Credly badge URLs
- ✅ **Expiry Validation**: Checks certification validity against current dates
- 🎓 **Intelligent Categorization**: Assigns credit points based on certification tier and type
- 🤖 **ReAct Pattern**: Uses LangGraph's create_react_agent for autonomous tool execution
- 💬 **Natural Language Support**: Handles both direct URLs and hypothetical certification queries
- ⚡ **Powered by Groq**: Fast inference using Llama-3.3-70B model

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Groq API Key ([Get one here](https://console.groq.com))

## Setup

### Prerequisites
- Python 3.8+
- Groq API Key

## Usage

### With LangGraph Studio
```bash
langgraph dev
```

### Programmatically
```python
from credly_updated import run_agent

response = run_agent("How many credit points can I get for https://www.credly.com/badges/...")
print(response)
```

## 🗣️ User Interaction Examples

### Query Type 1: Expired Certification

**User Input:**
```
How many credit points can I get for https://www.credly.com/badges/e192db17-f8c5-46aa-8f99-8a565223f1d6?
```

**Agent Response:**
```
Sorry, your cert has expired. So you won't get any credit points. 
But otherwise you would have stood to obtain 5 credit points for your HashiCorp Terraform Associate.
```

### Query Type 2: Valid Certification

**User Input:**
```
What about https://www.credly.com/badges/90ee2ee9-f6cf-4d9b-8a52-f631d8644d58?
```

**Agent Response:**
```
I see that this is an AWS Certified AI Practitioner. And it is still valid. 
So you can be granted 2.5 credit points for it.
```

### Query Type 3: Hypothetical Certification

**User Input:**
```
If I clear AWS Solutions Architect Professional, how many points will I get?
```

**Agent Response:**
```
You will get 10 credit points for that cert.
```

## 📊 Credit Point System

| Certification Category | Credit Points |
|------------------------|---------------|
| Professional or Specialty | 10.0 |
| Associate or HashiCorp | 5.0 |
| Fundamentals or Other | 2.5 |

## 🛠️ How It Works

The agent follows this workflow:

1. **Extract**: Scrapes certification data from Credly URL using Selenium
2. **Validate**: Checks expiry date against current date
3. **Categorize**: Matches certification name to database categories
4. **Calculate**: Assigns appropriate credit points
5. **Respond**: Formats response based on validity status


The script includes built-in test cases for:
- Expired certifications
- Valid certifications
- Hypothetical queries
## Query & Traces (Reference Screenshots)
![image](https://github.com/user-attachments/assets/a3fbdb9e-b033-451c-b62d-291c94864ecd)

