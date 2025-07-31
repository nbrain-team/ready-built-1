#!/bin/bash
# Setup script for Generic RAG Platform

echo "🚀 Setting up Generic RAG Platform..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOL
# Flask Configuration
FLASK_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
FLASK_ENV=development

# Database Configuration
DATABASE_URL=sqlite:///instance/generic_rag.db

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# MCP Server Configuration
USE_MCP=true
EOL
    echo "⚠️  Please update .env with your OpenAI API key"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p instance data logs config/context migrations/versions

# Initialize database
echo "🗄️  Initializing database..."
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# Create sample data
echo "📊 Creating sample data..."
python scripts/load_data.py

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your OpenAI API key"
echo "2. Run the application: python run.py"
echo "3. Visit http://localhost:5000"
echo "4. Check CUSTOMIZATION_GUIDE.md for customization instructions" 