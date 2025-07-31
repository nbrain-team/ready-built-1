# Generic RAG Platform

A flexible, reusable Retrieval-Augmented Generation (RAG) platform with MCP server integration, chat interface, and customizable data sources.

## Features

- **Modular Architecture**: Easy to adapt to any data source or use case
- **MCP Server Integration**: Standardized tool interface for data queries
- **Interactive Chat Interface**: With drill-down buttons and formatted responses
- **Configurable Data Schema**: JSON-based configuration for metrics and dimensions
- **Local Database Support**: SQLite for development, PostgreSQL for production
- **Authentication System**: User management and per-user chat history
- **Render-Ready**: Pre-configured for deployment

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Your Use Case

Edit `config/data_config.json` to define your data structure:

```json
{
  "data_sources": [
    {
      "name": "primary_data",
      "display_name": "Primary Data Source",
      "metrics": [
        {
          "id": "metric1",
          "display_name": "Metric 1",
          "type": "number",
          "format": "decimal"
        }
      ],
      "dimensions": [
        {
          "id": "dimension1",
          "display_name": "Dimension 1",
          "type": "string"
        }
      ]
    }
  ]
}
```

### 3. Load Your Data

Place your data files in `data/` directory and run:

```bash
python scripts/load_data.py
```

### 4. Run the Application

```bash
python run.py
```

## Customization Guide

### Adding a New Use Case

1. **Define your data schema** in `config/data_config.json`
2. **Create context files** in `config/context/`
3. **Load your data** using the provided scripts
4. **Customize prompts** in `config/prompts.json`

### Example Use Cases

- Analytics Dashboard (like GA4)
- Sales CRM Data
- Inventory Management
- Financial Reports
- Customer Support Tickets
- IoT Sensor Data

## Architecture

```
generic-rag-platform/
├── app/                    # Flask application
│   ├── main/              # Main routes and logic
│   ├── models.py          # Generic database models
│   └── templates/         # UI templates
├── mcp_server/            # MCP server for data access
├── config/                # Configuration files
│   ├── data_config.json   # Data schema definition
│   ├── prompts.json       # AI prompt templates
│   └── context/           # Use-case specific context
├── data/                  # Your data files go here
└── scripts/               # Utility scripts
```

## Deployment

### Render Deployment

1. Fork this repository
2. Connect to Render
3. Add environment variables:
   - `DATABASE_URL`
   - `OPENAI_API_KEY`
   - `FLASK_SECRET_KEY`
4. Deploy!

## License

MIT 