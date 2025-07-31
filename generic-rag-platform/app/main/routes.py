from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models import User, ChatHistory, DataSource, DataEntry
from datetime import datetime, timedelta
import json
import os
import openai
import uuid
from pathlib import Path

main = Blueprint('main', __name__)

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent.parent / "config"
with open(CONFIG_PATH / "data_config.json", 'r') as f:
    DATA_CONFIG = json.load(f)
with open(CONFIG_PATH / "prompts.json", 'r') as f:
    PROMPTS_CONFIG = json.load(f)

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

@main.route('/')
@main.route('/index')
def index():
    """Home page - redirect to login if not authenticated."""
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    return redirect(url_for('main.chat'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.chat'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.chat'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.chat'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user exists
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('main.register'))
        
        # Create new user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html')

@main.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/chat')
@login_required
def chat():
    """Main chat interface."""
    # Get available data sources
    sources = DataSource.query.all()
    if not sources:
        # Use config sources as fallback
        sources = DATA_CONFIG.get('data_sources', [])
    
    return render_template('chat.html', 
                         data_sources=sources,
                         ui_config=DATA_CONFIG.get('ui_config', {}))

@main.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    """Handle chat messages via API."""
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', str(uuid.uuid4()))
    context = data.get('context', {})
    
    try:
        # Get relevant context from database
        db_context = get_relevant_context(user_message, context)
        
        # Build system prompt
        prompt_type = context.get('prompt_type', 'default')
        system_prompt = PROMPTS_CONFIG['system_prompts'].get(prompt_type, PROMPTS_CONFIG['system_prompts']['default'])
        
        # Add context to system prompt
        if db_context:
            system_prompt += f"\n\nRelevant data context:\n{json.dumps(db_context, indent=2)}"
        
        # Call OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        ai_response = response.choices[0].message.content
        
        # Save to chat history
        chat_entry = ChatHistory(
            user_id=current_user.id,
            session_id=session_id,
            query=user_message,
            response=ai_response,
            context_data=context
        )
        db.session.add(chat_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/api/deep-dive', methods=['POST'])
@login_required
def deep_dive():
    """Handle deep dive requests for specific metrics."""
    data = request.json
    metric = data.get('metric')
    source = data.get('source')
    date_range = data.get('date_range', {})
    
    try:
        # Get detailed data for the metric
        detailed_data = get_metric_details(source, metric, date_range)
        
        # Generate analysis using AI
        analysis_prompt = PROMPTS_CONFIG['query_templates']['deep_dive'].format(
            metric=metric,
            data_source=source
        )
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": PROMPTS_CONFIG['system_prompts']['analytics']},
                {"role": "user", "content": f"{analysis_prompt}\n\nData: {json.dumps(detailed_data)}"}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        return jsonify({
            'success': True,
            'analysis': response.choices[0].message.content,
            'data': detailed_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/api/data-sources')
@login_required
def list_data_sources():
    """List available data sources."""
    sources = DataSource.query.all()
    
    result = []
    for source in sources:
        result.append({
            'id': source.id,
            'name': source.name,
            'display_name': source.display_name,
            'description': source.description,
            'metrics': source.config.get('metrics', []),
            'dimensions': source.config.get('dimensions', [])
        })
    
    # Add config sources if no DB sources
    if not result:
        for config_source in DATA_CONFIG.get('data_sources', []):
            result.append({
                'name': config_source['name'],
                'display_name': config_source['display_name'],
                'description': config_source.get('description', ''),
                'metrics': config_source.get('metrics', []),
                'dimensions': config_source.get('dimensions', [])
            })
    
    return jsonify(result)

@main.route('/api/chat-history')
@login_required
def get_chat_history():
    """Get chat history for current user."""
    session_id = request.args.get('session_id')
    
    query = ChatHistory.query.filter_by(user_id=current_user.id)
    if session_id:
        query = query.filter_by(session_id=session_id)
    
    history = query.order_by(ChatHistory.timestamp.desc()).limit(50).all()
    
    return jsonify([{
        'id': h.id,
        'timestamp': h.timestamp.isoformat(),
        'query': h.query,
        'response': h.response,
        'session_id': h.session_id
    } for h in history])

# Helper functions
def get_relevant_context(query, context):
    """Get relevant data based on the query and context."""
    source_name = context.get('data_source')
    date_range = context.get('date_range', {})
    
    if not source_name:
        return None
    
    # Get data source
    source = DataSource.query.filter_by(name=source_name).first()
    if not source:
        return None
    
    # Build date filter
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Default to last 30 days
    
    if date_range:
        if 'start' in date_range:
            start_date = datetime.fromisoformat(date_range['start'])
        if 'end' in date_range:
            end_date = datetime.fromisoformat(date_range['end'])
    
    # Query recent data
    entries = DataEntry.query.filter(
        DataEntry.source_id == source.id,
        DataEntry.timestamp.between(start_date, end_date)
    ).limit(100).all()
    
    # Format data
    data = []
    for entry in entries:
        data.append({
            'timestamp': entry.timestamp.isoformat(),
            'entity_id': entry.entity_id,
            'data': entry.data
        })
    
    return {
        'source': source.display_name,
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'sample_data': data[:10],  # Just first 10 for context
        'total_records': len(data)
    }

def get_metric_details(source_name, metric, date_range):
    """Get detailed data for a specific metric."""
    source = DataSource.query.filter_by(name=source_name).first()
    if not source:
        return None
    
    # Build date filter
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    if date_range:
        if 'start' in date_range:
            start_date = datetime.fromisoformat(date_range['start'])
        if 'end' in date_range:
            end_date = datetime.fromisoformat(date_range['end'])
    
    # Query data
    entries = DataEntry.query.filter(
        DataEntry.source_id == source.id,
        DataEntry.timestamp.between(start_date, end_date)
    ).all()
    
    # Extract metric values
    daily_data = {}
    for entry in entries:
        date_key = entry.timestamp.date().isoformat()
        if date_key not in daily_data:
            daily_data[date_key] = []
        
        value = entry.data.get(metric)
        if value is not None:
            daily_data[date_key].append(value)
    
    # Aggregate by day
    result = []
    for date, values in sorted(daily_data.items()):
        result.append({
            'date': date,
            'value': sum(values),
            'count': len(values),
            'average': sum(values) / len(values) if values else 0
        })
    
    return {
        'metric': metric,
        'source': source_name,
        'daily_data': result,
        'total': sum(d['value'] for d in result),
        'average': sum(d['value'] for d in result) / len(result) if result else 0
    } 