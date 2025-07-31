#!/usr/bin/env python3
"""
Generic data loader script
Loads data from CSV files into the database
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app, db
from app.models import DataSource, DataEntry

def load_csv_data(file_path, source_name, entity_column, date_column, metrics_columns):
    """Load data from a CSV file into the database."""
    
    app = create_app()
    
    with app.app_context():
        # Check if data source exists
        source = DataSource.query.filter_by(name=source_name).first()
        
        if not source:
            # Load config to get source details
            config_path = Path(__file__).parent.parent / "config" / "data_config.json"
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Find source config
            source_config = next((s for s in config['data_sources'] if s['name'] == source_name), None)
            if not source_config:
                print(f"Error: Source '{source_name}' not found in configuration")
                return
            
            # Create data source
            source = DataSource(
                name=source_name,
                display_name=source_config['display_name'],
                description=source_config.get('description', ''),
                source_type='csv',
                config=source_config
            )
            db.session.add(source)
            db.session.commit()
            print(f"Created data source: {source_name}")
        
        # Load CSV
        df = pd.read_csv(file_path)
        print(f"Loading {len(df)} rows from {file_path}")
        
        # Process each row
        entries_added = 0
        for _, row in df.iterrows():
            # Parse date
            try:
                timestamp = pd.to_datetime(row[date_column])
            except:
                print(f"Warning: Could not parse date '{row[date_column]}', skipping row")
                continue
            
            # Build data dictionary
            data = {}
            for col in metrics_columns:
                if col in row:
                    data[col] = float(row[col]) if pd.notna(row[col]) else None
            
            # Add any additional columns as dimensions
            for col in df.columns:
                if col not in [entity_column, date_column] + metrics_columns:
                    data[col] = row[col] if pd.notna(row[col]) else None
            
            # Create entry
            entry = DataEntry(
                source_id=source.id,
                entity_id=str(row[entity_column]),
                timestamp=timestamp,
                data=data
            )
            db.session.add(entry)
            entries_added += 1
            
            # Commit in batches
            if entries_added % 1000 == 0:
                db.session.commit()
                print(f"  Loaded {entries_added} entries...")
        
        # Final commit
        db.session.commit()
        print(f"Successfully loaded {entries_added} entries for {source_name}")

def main():
    """Main function to load sample data."""
    
    # Example usage - modify based on your data
    data_dir = Path(__file__).parent.parent / "data"
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)
    
    # Example: Create sample data if no CSV exists
    sample_file = data_dir / "sample_data.csv"
    if not sample_file.exists():
        print("Creating sample data...")
        
        # Generate sample data
        import numpy as np
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        
        data = []
        for date in dates:
            for entity in ['Entity_A', 'Entity_B', 'Entity_C']:
                data.append({
                    'date': date,
                    'entity_name': entity,
                    'total_value': np.random.randint(1000, 10000),
                    'count': np.random.randint(10, 100),
                    'average_rate': np.random.uniform(0.1, 0.9),
                    'category': np.random.choice(['Category1', 'Category2', 'Category3'])
                })
        
        df = pd.DataFrame(data)
        df.to_csv(sample_file, index=False)
        print(f"Created sample data at {sample_file}")
    
    # Load the data
    load_csv_data(
        file_path=sample_file,
        source_name='example_analytics',
        entity_column='entity_name',
        date_column='date',
        metrics_columns=['total_value', 'count', 'average_rate']
    )

if __name__ == "__main__":
    main() 