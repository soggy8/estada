"""
Flask backend for Estada website

Email Setup:
1. Get your Resend API key from https://resend.com/api-keys
2. Set it as an environment variable: export RESEND_API_KEY=re_xxxxx
   Or create a .env file with: RESEND_API_KEY=re_xxxxx

The email will be sent FROM the user's email address TO all three recipients.
"""

from flask import Flask, request, jsonify, render_template
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')

# Resend API configuration
RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
RESEND_API_URL = 'https://api.resend.com/emails'

# Recipient emails
RECIPIENT_EMAILS = [
    'andrejt@estada.dev',
    'krstem@estada.dev',
    'filipm@estada.dev'
]

@app.route('/')
def index():
    """Serve the main index.html page"""
    return render_template('index.html')

@app.route('/about')
def about():
    """Serve the about.html page"""
    return render_template('about.html')

@app.route('/technologies')
def technologies():
    """Serve the technologies.html page"""
    return render_template('technologies.html')

@app.route('/api/contact', methods=['POST'])
def contact():
    """Handle contact form submissions"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('email'):
            return jsonify({'success': False, 'message': 'Name and email are required'}), 400
        
        # Prepare email content
        name = data.get('name', '')
        email = data.get('email', '')
        service = data.get('service', 'Not specified')
        message = data.get('message', 'No message provided')
        
        # Create email subject
        subject = f'New Contact Form Submission from {name}'
        
        # Create email body
        body = f"""
New contact form submission from Estada website:

Name: {name}
Email: {email}
Service: {service}

Message:
{message}

---
This email was sent from the Estada contact form.
"""
        
        # Send email to all recipients using Resend API
        try:
            if not RESEND_API_KEY:
                app.logger.error('RESEND_API_KEY not configured')
                return jsonify({'success': False, 'message': 'Email service not configured.'}), 500
            
            # Send email FROM the user's email TO all recipients
            response = requests.post(
                RESEND_API_URL,
                headers={
                    'Authorization': f'Bearer {RESEND_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'from': f'{name} <{email}>',
                    'to': RECIPIENT_EMAILS,
                    'subject': subject,
                    'text': body,
                    'reply_to': email
                }
            )
            
            if response.status_code == 200:
                return jsonify({'success': True, 'message': 'Message sent successfully!'}), 200
            else:
                app.logger.error(f'Resend API error: {response.status_code} - {response.text}')
                return jsonify({'success': False, 'message': 'Failed to send email. Please try again later.'}), 500
                
        except Exception as e:
            app.logger.error(f'Email sending failed: {str(e)}')
            return jsonify({'success': False, 'message': 'Failed to send email. Please try again later.'}), 500
            
    except Exception as e:
        app.logger.error(f'Contact form error: {str(e)}')
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8082)

