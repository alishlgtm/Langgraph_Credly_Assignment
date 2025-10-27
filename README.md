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

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/alishlgtm/certification-agent-langgraph.git
cd certification-agent-langgraph
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

Or create a `.env` file:
```
GROQ_API_KEY=your_groq_api_key_here
```

4. **Initialize the database**
```bash
python setup_database.py
```

## 💡 Usage

### With LangGraph Studio (Recommended)

Launch the interactive development environment:

```bash
langgraph dev
```

Then open the Studio UI at: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

### Programmatic Usage

```python
from langgraph_cred_agent import run_agent

# Example: Check credit points for a Credly URL
response = run_agent(
    "How many credit points can I get for https://www.credly.com/badges/e192db17-f8c5-46aa-8f99-8a565223f1d6?"
)
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

### Supported Certifications

- **AWS**: Solutions Architect, Developer, SysOps Administrator, DevOps Engineer, AI Practitioner
- **HashiCorp**: Terraform Associate
- **Microsoft Azure**: Fundamentals, Solutions Architect Expert
- **Google Cloud**: Professional Cloud Architect
- **Kubernetes**: CKA (Certified Kubernetes Administrator)
- **Security**: CompTIA Security+, CISSP
- And many more...

## 📁 Project Structure

```
certification-agent-langgraph/
├── langgraph_cred_agent.py      # Main LangGraph ReAct agent
├── webscrap_cred_v2.py          # Credly web scraper module
├── setup_database.py            # Database initialization script
├── sqlite_cert.py               # Legacy database utilities
├── certifications_data.db       # SQLite database (generated)
├── langgraph.json               # LangGraph configuration
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (create this)
└── README.md                    # Documentation
```

## 🛠️ How It Works

The agent follows this workflow:

1. **Extract**: Scrapes certification data from Credly URL using Selenium
2. **Validate**: Checks expiry date against current date
3. **Categorize**: Matches certification name to database categories
4. **Calculate**: Assigns appropriate credit points
5. **Respond**: Formats response based on validity status

### Tool Chain

```
User Query → extract_certification_data → check_certification_validity → get_certification_points → Formatted Response
```

## 🔧 Configuration

### Database Categories

Edit `setup_database.py` to modify certification categories and point values:

```python
certifications = [
    ('AWS Certified Solutions Architect - Professional', 10.0),
    ('HashiCorp Certified: Terraform Associate', 5.0),
    ('AWS Certified AI Practitioner', 2.5),
    # Add more certifications...
]
```

### LangGraph Settings

Modify `langgraph.json` to adjust graph configuration:

```json
{
    "dependencies": ["."],
    "graphs": {
      "graph_credly": "./langgraph_cred_agent.py:app"
    },
    "env": ".env"
}
```

## 🧪 Testing

Run the agent with test queries:

```bash
python langgraph_cred_agent.py
```

The script includes built-in test cases for:
- Expired certifications
- Valid certifications
- Hypothetical queries

## 🐛 Troubleshooting

### Common Issues

**ChromeDriver not found:**
```bash
# The script auto-installs ChromeDriver, but if issues persist:
pip install --upgrade webdriver-manager
```

**Database errors:**
```bash
# Recreate the database:
rm certifications_data.db
python setup_database.py
```

**Groq API errors:**
- Verify your API key is correctly set
- Check rate limits on your Groq account

## 📝 Dependencies

Key packages:
- `langgraph` - Graph-based agent framework
- `langchain` & `langchain-groq` - LLM integration
- `selenium` - Web scraping
- `beautifulsoup4` - HTML parsing
- `webdriver-manager` - Automatic ChromeDriver management
- `sqlite3` - Database (built-in)

See `requirements.txt` for complete list.

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [Groq](https://groq.com/) inference
- Certification data from [Credly](https://www.credly.com/)

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Made with ❤️ using LangGraph and ReAct pattern**
# Programmatically (run this in Python after setup)
python -c "from langgraph_cred_agent import run_agent; response = run_agent('How many credit points can I get for https://www.credly.com/badges/...'); print(response)"
