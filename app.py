from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

def get_openai_client():
    """Initialize OpenAI client with proper error handling"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is not set")
        return None
    
    if api_key.startswith('sk-') and len(api_key) > 10:
        print("SUCCESS: OpenAI API key found and appears valid")
        return OpenAI(api_key=api_key)
    else:
        print(f"ERROR: Invalid API key format. Key starts with: {api_key[:10] if api_key else 'None'}")
        return None

# Initialize client
client = get_openai_client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    api_key_status = "configured" if os.getenv('OPENAI_API_KEY') else "missing"
    client_status = "connected" if client else "failed"
    
    return jsonify({
        'status': 'healthy', 
        'api_key': api_key_status,
        'openai_client': client_status
    })

@app.route('/env-check')
def env_check():
    """Debug endpoint to check environment variables"""
    env_vars = {
        'OPENAI_API_KEY_set': bool(os.getenv('OPENAI_API_KEY')),
        'OPENAI_API_KEY_length': len(os.getenv('OPENAI_API_KEY', '')),
        'OPENAI_API_KEY_prefix': os.getenv('OPENAI_API_KEY', '')[:10] + '...' if os.getenv('OPENAI_API_KEY') else 'None',
        'PORT': os.getenv('PORT', '5000'),
        'PYTHON_VERSION': os.getenv('PYTHON_VERSION', 'Not set')
    }
    return jsonify(env_vars)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Check if client is properly initialized
        if not client:
            error_msg = "OpenAI client not initialized. Please check API key configuration."
            print(f"ERROR: {error_msg}")
            return jsonify({'error': error_msg}), 500
        
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
        print("SUCCESS: OpenAI API call completed successfully")
        
        return jsonify({'reply': bot_reply})
    
    except Exception as e:
        error_msg = f"OpenAI API error: {str(e)}"
        print(f"ERROR: {error_msg}")
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    print(f"OPENAI_API_KEY set: {bool(os.getenv('OPENAI_API_KEY'))}")
    app.run(host='0.0.0.0', port=port, debug=False)
