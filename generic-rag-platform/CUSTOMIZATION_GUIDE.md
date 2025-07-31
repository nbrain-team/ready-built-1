# Customization Guide

This guide explains how to adapt the Generic RAG Platform for your specific use case.

## Quick Start Customization

### 1. Define Your Data Structure

Edit `config/data_config.json` to match your data:

```json
{
  "data_sources": [
    {
      "name": "your_data_source",
      "display_name": "Your Data Source Name",
      "description": "Description of your data",
      "metrics": [
        {
          "id": "revenue",
          "display_name": "Revenue",
          "type": "number",
          "format": "currency",
          "aggregation": "sum"
        }
      ],
      "dimensions": [
        {
          "id": "product",
          "display_name": "Product",
          "type": "string"
        }
      ]
    }
  ]
}
```

### 2. Load Your Data

#### Option A: CSV Files

1. Place your CSV files in the `data/` directory
2. Modify `scripts/load_data.py`:

```python
load_csv_data(
    file_path='data/your_data.csv',
    source_name='your_data_source',
    entity_column='product_id',
    date_column='date',
    metrics_columns=['revenue', 'quantity', 'profit']
)
```

3. Run: `python scripts/load_data.py`

#### Option B: Direct Database Connection

Create a custom loader in `scripts/`:

```python
from app.models import DataSource, DataEntry
import your_database_connector

def load_from_database():
    # Your database connection logic
    data = your_database_connector.query("SELECT * FROM your_table")
    
    # Transform and load into DataEntry model
    for row in data:
        entry = DataEntry(
            source_id=source.id,
            entity_id=row['id'],
            timestamp=row['date'],
            data={
                'metric1': row['value1'],
                'metric2': row['value2']
            }
        )
        db.session.add(entry)
```

### 3. Customize AI Prompts

Edit `config/prompts.json`:

```json
{
  "system_prompts": {
    "default": "You are an expert in [YOUR DOMAIN]. Help users understand their [YOUR DATA TYPE].",
    "analytics": "Provide insights about [YOUR SPECIFIC METRICS]..."
  }
}
```

### 4. Add Context Documents

Place context documents in `config/context/`:
- `domain_knowledge.txt` - Background information
- `metric_definitions.txt` - Explanations of your metrics
- `business_rules.txt` - Specific rules or calculations

## Advanced Customization

### Custom Metrics Processing

Add custom metric calculations in `app/main/routes.py`:

```python
def calculate_custom_metric(data):
    # Your custom calculation
    return processed_data
```

### Custom Drill-Down Actions

Modify the deep dive functionality in `chat.html`:

```javascript
function addDeepDiveButtons(html) {
    // Add your metrics pattern
    const metricsPattern = /\b(your_metric1|your_metric2)\b/gi;
    
    html = html.replace(metricsPattern, (match) => {
        return `${match} <button class="deep-dive-btn" onclick="deepDive('${match.toLowerCase()}')">[↓]</button>`;
    });
    
    return html;
}
```

### Custom Visualizations

Add chart types in the chat response processing:

```javascript
// In processAIResponse function
if (response.includes('[CHART:')) {
    // Parse and render your custom charts
}
```

## Use Case Examples

### 1. Sales Analytics

```json
{
  "metrics": [
    {"id": "revenue", "display_name": "Revenue", "format": "currency"},
    {"id": "units_sold", "display_name": "Units Sold", "format": "integer"},
    {"id": "avg_order_value", "display_name": "Average Order Value", "format": "currency"}
  ],
  "dimensions": [
    {"id": "product_category", "display_name": "Product Category"},
    {"id": "region", "display_name": "Sales Region"},
    {"id": "sales_rep", "display_name": "Sales Representative"}
  ]
}
```

### 2. IoT Sensor Data

```json
{
  "metrics": [
    {"id": "temperature", "display_name": "Temperature", "format": "decimal", "unit": "°C"},
    {"id": "humidity", "display_name": "Humidity", "format": "percentage"},
    {"id": "pressure", "display_name": "Pressure", "format": "decimal", "unit": "hPa"}
  ],
  "dimensions": [
    {"id": "sensor_id", "display_name": "Sensor ID"},
    {"id": "location", "display_name": "Location"},
    {"id": "sensor_type", "display_name": "Sensor Type"}
  ]
}
```

### 3. Customer Support Tickets

```json
{
  "metrics": [
    {"id": "resolution_time", "display_name": "Resolution Time", "format": "duration"},
    {"id": "satisfaction_score", "display_name": "Satisfaction Score", "format": "decimal"},
    {"id": "ticket_count", "display_name": "Ticket Count", "format": "integer"}
  ],
  "dimensions": [
    {"id": "category", "display_name": "Issue Category"},
    {"id": "priority", "display_name": "Priority Level"},
    {"id": "agent", "display_name": "Support Agent"}
  ]
}
```

## Integration Points

### 1. External APIs

Add API integrations in `app/main/routes.py`:

```python
@main.route('/api/external-data')
@login_required
def fetch_external_data():
    # Call your external API
    response = requests.get('https://your-api.com/data')
    # Process and return
```

### 2. Real-time Data

For real-time updates, add WebSocket support:

```python
# In app/__init__.py
from flask_socketio import SocketIO
socketio = SocketIO(app)

# In routes.py
@socketio.on('subscribe_updates')
def handle_subscription(data):
    # Stream real-time updates
```

### 3. Custom Authentication

Replace the default auth with your system:

```python
# In app/main/routes.py
from your_auth_system import authenticate

@main.route('/login', methods=['POST'])
def custom_login():
    token = request.headers.get('Authorization')
    user = authenticate(token)
    # Process login
```

## Deployment Customization

### Environment Variables

Create `.env` for your deployment:

```bash
# Your specific configuration
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
YOUR_CUSTOM_API_KEY=...
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
```

## Troubleshooting

### Common Issues

1. **Data not loading**: Check date format and column names
2. **AI responses generic**: Add more context in `config/context/`
3. **Metrics not recognized**: Update patterns in JavaScript

### Debug Mode

Enable debug logging:

```python
# In .env
FLASK_ENV=development
LOG_LEVEL=DEBUG
```

## Support

For questions or issues:
1. Check the logs in `logs/`
2. Review the data schema in the database
3. Verify configuration files are valid JSON 