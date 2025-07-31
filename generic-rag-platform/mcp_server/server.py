#!/usr/bin/env python3
"""
Generic MCP Server for RAG Platform
Provides tools for querying any configured data source
"""

import os
import sys
import json
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import our models
from app.models import DataSource, DataEntry, SystemConfig

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instance/generic_rag.db")
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if not db_path.startswith("/"):
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path)
        DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Create MCP server
server = Server("generic-rag-mcp")

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / "config" / "data_config.json"
with open(CONFIG_PATH, 'r') as f:
    DATA_CONFIG = json.load(f)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List all available tools."""
    return [
        types.Tool(
            name="query_data",
            description="Query data from configured sources with flexible filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Name of the data source to query"
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of metrics to retrieve"
                    },
                    "dimensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of dimensions to group by"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Filters to apply (e.g., date range, entity filters)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 100
                    }
                },
                "required": ["source"]
            }
        ),
        types.Tool(
            name="compare_periods",
            description="Compare metrics between two time periods",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Name of the data source"
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metrics to compare"
                    },
                    "period1": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "string", "format": "date"},
                            "end": {"type": "string", "format": "date"}
                        },
                        "description": "First period to compare"
                    },
                    "period2": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "string", "format": "date"},
                            "end": {"type": "string", "format": "date"}
                        },
                        "description": "Second period to compare"
                    }
                },
                "required": ["source", "metrics", "period1", "period2"]
            }
        ),
        types.Tool(
            name="get_trend",
            description="Get trend data for metrics over time",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Name of the data source"
                    },
                    "metric": {
                        "type": "string",
                        "description": "Metric to analyze"
                    },
                    "start_date": {
                        "type": "string",
                        "format": "date",
                        "description": "Start date for trend analysis"
                    },
                    "end_date": {
                        "type": "string",
                        "format": "date",
                        "description": "End date for trend analysis"
                    },
                    "granularity": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly"],
                        "description": "Time granularity for trend data",
                        "default": "daily"
                    }
                },
                "required": ["source", "metric", "start_date", "end_date"]
            }
        ),
        types.Tool(
            name="list_sources",
            description="List all available data sources and their configurations",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution."""
    
    if name == "list_sources":
        return await list_data_sources()
    elif name == "query_data":
        return await query_data(arguments)
    elif name == "compare_periods":
        return await compare_periods(arguments)
    elif name == "get_trend":
        return await get_trend_data(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def list_data_sources():
    """List all configured data sources."""
    session = Session()
    try:
        sources = session.query(DataSource).all()
        
        result = {
            "sources": [
                {
                    "name": source.name,
                    "display_name": source.display_name,
                    "description": source.description,
                    "type": source.source_type,
                    "metrics": source.config.get("metrics", []),
                    "dimensions": source.config.get("dimensions", [])
                }
                for source in sources
            ]
        }
        
        # Also include configured sources from config file
        for config_source in DATA_CONFIG.get("data_sources", []):
            if not any(s["name"] == config_source["name"] for s in result["sources"]):
                result["sources"].append({
                    "name": config_source["name"],
                    "display_name": config_source["display_name"],
                    "description": config_source.get("description", ""),
                    "type": "config",
                    "metrics": config_source.get("metrics", []),
                    "dimensions": config_source.get("dimensions", [])
                })
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    finally:
        session.close()

async def query_data(arguments: dict):
    """Query data from a specified source."""
    source_name = arguments.get("source")
    metrics = arguments.get("metrics", [])
    dimensions = arguments.get("dimensions", [])
    filters = arguments.get("filters", {})
    limit = arguments.get("limit", 100)
    
    session = Session()
    try:
        # Get data source configuration
        source = session.query(DataSource).filter_by(name=source_name).first()
        if not source:
            # Check config file
            config_source = next((s for s in DATA_CONFIG.get("data_sources", []) 
                                if s["name"] == source_name), None)
            if not config_source:
                return [types.TextContent(
                    type="text",
                    text=f"Error: Data source '{source_name}' not found"
                )]
        
        # Build query
        query = session.query(DataEntry).filter(DataEntry.source_id == source.id if source else None)
        
        # Apply filters
        if "start_date" in filters and "end_date" in filters:
            start = datetime.fromisoformat(filters["start_date"])
            end = datetime.fromisoformat(filters["end_date"])
            query = query.filter(DataEntry.timestamp.between(start, end))
        
        if "entity_id" in filters:
            query = query.filter(DataEntry.entity_id == filters["entity_id"])
        
        # Execute query
        results = query.limit(limit).all()
        
        # Format results
        data = []
        for entry in results:
            row = {
                "timestamp": entry.timestamp.isoformat(),
                "entity_id": entry.entity_id
            }
            
            # Extract requested metrics from JSON data
            entry_data = entry.data or {}
            for metric in metrics:
                row[metric] = entry_data.get(metric)
            
            # Extract dimensions
            for dimension in dimensions:
                row[dimension] = entry_data.get(dimension)
            
            data.append(row)
        
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "source": source_name,
                "count": len(data),
                "data": data
            }, indent=2, default=str)
        )]
        
    finally:
        session.close()

async def compare_periods(arguments: dict):
    """Compare metrics between two periods."""
    source_name = arguments["source"]
    metrics = arguments["metrics"]
    period1 = arguments["period1"]
    period2 = arguments["period2"]
    
    # Query data for both periods
    period1_data = await query_data({
        "source": source_name,
        "metrics": metrics,
        "filters": {
            "start_date": period1["start"],
            "end_date": period1["end"]
        }
    })
    
    period2_data = await query_data({
        "source": source_name,
        "metrics": metrics,
        "filters": {
            "start_date": period2["start"],
            "end_date": period2["end"]
        }
    })
    
    # Parse results
    p1_result = json.loads(period1_data[0].text)
    p2_result = json.loads(period2_data[0].text)
    
    # Calculate aggregates and changes
    comparison = {
        "source": source_name,
        "period1": period1,
        "period2": period2,
        "metrics": {}
    }
    
    for metric in metrics:
        p1_values = [row.get(metric, 0) for row in p1_result["data"] if row.get(metric) is not None]
        p2_values = [row.get(metric, 0) for row in p2_result["data"] if row.get(metric) is not None]
        
        p1_sum = sum(p1_values) if p1_values else 0
        p2_sum = sum(p2_values) if p2_values else 0
        
        change = p2_sum - p1_sum
        change_pct = (change / p1_sum * 100) if p1_sum != 0 else 0
        
        comparison["metrics"][metric] = {
            "period1_value": p1_sum,
            "period2_value": p2_sum,
            "change": change,
            "change_percentage": round(change_pct, 2)
        }
    
    return [types.TextContent(
        type="text",
        text=json.dumps(comparison, indent=2)
    )]

async def get_trend_data(arguments: dict):
    """Get trend data for a metric over time."""
    source_name = arguments["source"]
    metric = arguments["metric"]
    start_date = datetime.fromisoformat(arguments["start_date"])
    end_date = datetime.fromisoformat(arguments["end_date"])
    granularity = arguments.get("granularity", "daily")
    
    session = Session()
    try:
        # Get source
        source = session.query(DataSource).filter_by(name=source_name).first()
        if not source:
            return [types.TextContent(
                type="text",
                text=f"Error: Data source '{source_name}' not found"
            )]
        
        # Query data
        entries = session.query(DataEntry).filter(
            DataEntry.source_id == source.id,
            DataEntry.timestamp.between(start_date, end_date)
        ).order_by(DataEntry.timestamp).all()
        
        # Aggregate by granularity
        trend_data = {}
        for entry in entries:
            # Determine bucket based on granularity
            if granularity == "daily":
                bucket = entry.timestamp.date().isoformat()
            elif granularity == "weekly":
                bucket = entry.timestamp.date().isocalendar()[:2]  # (year, week)
                bucket = f"{bucket[0]}-W{bucket[1]:02d}"
            else:  # monthly
                bucket = f"{entry.timestamp.year}-{entry.timestamp.month:02d}"
            
            if bucket not in trend_data:
                trend_data[bucket] = []
            
            value = entry.data.get(metric)
            if value is not None:
                trend_data[bucket].append(value)
        
        # Calculate aggregates for each bucket
        result = {
            "source": source_name,
            "metric": metric,
            "granularity": granularity,
            "data": []
        }
        
        for bucket, values in sorted(trend_data.items()):
            result["data"].append({
                "period": bucket,
                "value": sum(values),
                "count": len(values),
                "average": sum(values) / len(values) if values else 0
            })
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    finally:
        session.close()

async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="generic-rag-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 