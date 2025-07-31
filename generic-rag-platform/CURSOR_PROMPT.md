# Cursor AI Assistant Prompt for Generic RAG Platform Customization

## Context

You are working with a Generic RAG (Retrieval-Augmented Generation) Platform that provides:
- A flexible data ingestion system supporting any data structure
- An AI-powered chat interface with drill-down capabilities
- MCP (Model Context Protocol) server for standardized data access
- User authentication and session management
- Configurable metrics, dimensions, and AI prompts

## Project Structure

```
generic-rag-platform/
├── app/                    # Flask web application
│   ├── __init__.py        # App initialization and configuration
│   ├── models.py          # Database models (User, DataSource, DataEntry, etc.)
│   ├── main/              # Main blueprint
│   │   ├── routes.py      # API endpoints and page routes
│   │   └── __init__.py    
│   └── templates/         # HTML templates
│       ├── base.html      # Base template with navigation
│       ├── login.html     # User authentication
│       ├── register.html  # User registration
│       └── chat.html      # Main chat interface with drill-downs
├── mcp_server/            # MCP server for data queries
│   └── server.py          # Query tools: query_data, compare_periods, get_trend
├── config/                # Configuration files
│   ├── data_config.json   # Define metrics, dimensions, UI settings
│   ├── prompts.json       # AI system prompts and templates
│   └── context/           # Domain-specific context documents
├── scripts/               # Utility scripts
│   └── load_data.py       # CSV data loader with example
├── data/                  # Your data files go here
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment configuration
├── build.sh              # Build script for deployment
├── run.py                # Local development server
└── setup.sh              # One-click setup script
```

## Key Files to Modify

### 1. **config/data_config.json** - Define your data structure
- Specify metrics (numerical values to analyze)
- Define dimensions (categorical groupings)
- Configure UI behavior

### 2. **config/prompts.json** - Customize AI behavior
- System prompts for different contexts
- Query templates for common analyses
- Response formatting preferences

### 3. **scripts/load_data.py** - Load your data
- Modify to match your CSV structure
- Set entity_column, date_column, metrics_columns
- Or create custom loaders for other data sources

### 4. **app/templates/chat.html** - Customize UI
- Line 467: Update metric patterns for drill-down buttons
- Modify deep dive functionality
- Add custom visualizations

## Getting Started

1. **Setup Environment**:
   ```bash
   ./setup.sh
   ```

2. **Configure for Your Use Case**:
   - Edit `config/data_config.json` with your metrics/dimensions
   - Update `config/prompts.json` with domain-specific prompts
   - Add context documents to `config/context/`

3. **Load Your Data**:
   ```bash
   python scripts/load_data.py
   ```

4. **Run Locally**:
   ```bash
   python run.py
   ```

5. **Deploy to Render**:
   - Push to GitHub
   - Follow RENDER_SETUP.md instructions

## Customization Tasks

When customizing this platform, focus on:

1. **Data Schema**: Define what metrics and dimensions make sense for your domain
2. **AI Context**: Provide domain knowledge so the AI can give relevant insights
3. **UI Elements**: Customize which metrics get drill-down buttons
4. **Data Loading**: Adapt the loader for your data format
5. **Authentication**: Integrate with existing auth systems if needed

---

## USE CASE CONTEXT PLACEHOLDER

**[REPLACE THIS SECTION WITH YOUR SPECIFIC USE CASE DETAILS]**

To effectively customize this platform, please provide:

### 1. Domain Overview
- What type of data will you be analyzing?
- Who are the end users?
- What decisions will they make based on this data?

### 2. Data Structure
- What are your key metrics (numerical values)?
  - Example: revenue, temperature, response_time, etc.
- What are your dimensions (categories)?
  - Example: product_category, sensor_location, department, etc.
- What time granularity do you need?
  - Example: hourly, daily, monthly

### 3. Example Data
Provide a sample of your data structure:
```csv
date,entity_id,metric1,metric2,dimension1,dimension2
2024-01-01,ABC123,1500.50,85,CategoryA,Region1
```

### 4. Key Questions Users Will Ask
- "What is the trend of [metric] over the last [period]?"
- "Which [dimension] has the highest [metric]?"
- "Compare [metric] between [dimension values]"
- [Add your specific questions]

### 5. Domain-Specific Knowledge
- Important calculations or formulas
- Business rules or thresholds
- Industry terminology
- Relationships between metrics

### 6. Integration Requirements
- External APIs to connect?
- Existing databases to query?
- Authentication systems to integrate?
- Real-time data needs?

### 7. UI/UX Preferences
- Specific visualizations needed?
- Custom drill-down actions?
- Branding requirements?
- Mobile responsiveness needs?

**Example Use Case Description:**

```
We are building an IoT sensor monitoring platform for a manufacturing facility.

Data: Temperature, humidity, and pressure readings from 50 sensors across 5 production lines, 
collected every 5 minutes.

Users: Plant managers and maintenance technicians who need to identify anomalies, 
predict equipment failures, and optimize environmental conditions.

Key metrics: temperature (°C), humidity (%), pressure (hPa), uptime (%)
Key dimensions: sensor_id, production_line, sensor_type, location

The AI should understand manufacturing processes, alert on readings outside normal ranges, 
and suggest maintenance actions based on sensor patterns.
```

**[END OF PLACEHOLDER - PROVIDE YOUR DETAILS ABOVE]** 