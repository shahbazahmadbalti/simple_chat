from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

def get_openai_client():
    """Initialize OpenAI client with multiple fallback options"""
    # Try multiple possible environment variable names
    api_key = (
        os.getenv('OPENAI_API_KEY') or
        os.getenv('OPENAI_KEY') or
        os.getenv('API_KEY')
    )
    
    # Debug: Print what we found
    print(f"DEBUG: Looking for API key...")
    print(f"DEBUG: OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"DEBUG: OPENAI_KEY exists: {bool(os.getenv('OPENAI_KEY'))}")
    print(f"DEBUG: API_KEY exists: {bool(os.getenv('API_KEY'))}")
    
    if api_key:
        print(f"DEBUG: Found API key, length: {len(api_key)}")
        print(f"DEBUG: API key starts with: {api_key[:10]}...")
        
        # Validate key format
        if api_key.startswith('sk-'):
            print("SUCCESS: Valid OpenAI API key format detected")
            return OpenAI(api_key=api_key)
        else:
            print(f"WARNING: API key doesn't start with 'sk-'. Starts with: {api_key[:10]}")
            # Still try to use it, might be a different format
            return OpenAI(api_key=api_key)
    else:
        print("ERROR: No API key found in any environment variable")
        return None

# Initialize client
client = get_openai_client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    """Comprehensive health check"""
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY') or os.getenv('API_KEY')
    
    health_info = {
        'status': 'healthy',
        'api_key_configured': bool(api_key),
        'api_key_length': len(api_key) if api_key else 0,
        'openai_client_initialized': bool(client),
        'environment_variables': {
            'OPENAI_API_KEY_set': bool(os.getenv('OPENAI_API_KEY')),
            'OPENAI_KEY_set': bool(os.getenv('OPENAI_KEY')),
            'API_KEY_set': bool(os.getenv('API_KEY')),
            'PORT': os.getenv('PORT', '5000')
        }
    }
    
    return jsonify(health_info)

@app.route('/debug')
def debug():
    """Detailed debug information"""
    all_env_vars = dict(os.environ)
    # Hide actual API key values for security
    safe_env_vars = {}
    for key, value in all_env_vars.items():
        if 'API' in key or 'KEY' in key or 'SECRET' in key:
            safe_env_vars[key] = f"***{value[-4:]}" if value else "Not set"
        else:
            safe_env_vars[key] = value
    
    debug_info = {
        'python_version': os.sys.version,
        'working_directory': os.getcwd(),
        'files_in_directory': os.listdir('.'),
        'environment_variables': safe_env_vars,
        'openai_client_status': 'Initialized' if client else 'Failed',
        'available_openai_models': get_available_models() if client else 'Client not initialized'
    }
    
    return jsonify(debug_info)

def get_available_models():
    """Try to get available models to test API connection"""
    try:
        models = client.models.list()
        return [model.id for model in models.data[:5]]  # First 5 models
    except Exception as e:
        return f"Error fetching models: {str(e)}"

@app.route('/test-api')
def test_api():
    """Test the OpenAI API directly"""
    if not client:
        return jsonify({'error': 'OpenAI client not initialized'}), 500
    
    try:
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Hello World'"}],
            max_tokens=10
        )
        
        return jsonify({
            'status': 'success',
            'response': response.choices[0].message.content,
            'model': response.model
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Check if client is properly initialized
        if not client:
            # Try to reinitialize client
            global client
            client = get_openai_client()
            if not client:
                return jsonify({
                    'error': 'OpenAI API not configured. Please check your API key in Railway environment variables.',
                    'debug_info': 'Visit /health endpoint to check configuration'
                }), 500
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        bot_reply = response.choices[0].message.content.strip()
        return jsonify({'reply': bot_reply})
    
    except Exception as e:
        return jsonify({'error': f'API Error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=== Starting Server ===")
    print(f"Port: {port}")
    print(f"OpenAI Client Initialized: {bool(client)}")
    app.run(host='0.0.0.0', port=port, debug=False)
