"""
Flask backend for Estada website

Email Setup:
1. Get your Resend API key from https://resend.com/api-keys
2. Set it as an environment variable: export RESEND_API_KEY=re_xxxxx
   Or create a .env file with: RESEND_API_KEY=re_xxxxx

Optional (for production):
- SENDER_EMAIL: Verified sender email (e.g., contact@estada.dev)
- SENDER_NAME: Display name for sender (default: "Estada Contact Form")
- DEV_MODE: Set to "False" to send to all recipients (requires verified domain)
- TEST_EMAIL: Your Resend account email (for testing, default: atrendov1@gmail.com)

IMPORTANT: 
- In DEV_MODE (default), emails only go to TEST_EMAIL (Resend test mode limitation)
- To send to all recipients, you must:
  1. Verify estada.dev domain at resend.com/domains
  2. Set SENDER_EMAIL=contact@estada.dev (or your verified domain)
  3. Set DEV_MODE=False in .env file

Emails include user's email in reply_to for direct replies.
"""

from flask import Flask, request, jsonify, render_template, make_response, g, url_for
from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import os
import requests
import logging
import re
from dotenv import load_dotenv

import business
from i18n import LANGS, DEFAULT_LANG, OG_LOCALES, STRINGS

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
# Keep Cyrillic readable in JSON-LD and API responses instead of \u escapes
app.json.ensure_ascii = False

# Configure logging to show all levels
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
app.logger.setLevel(logging.INFO)

# Production settings
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())

# Public origin used in canonical links, sitemap, and structured data
SITE_URL = os.getenv('SITE_URL', 'https://estada.dev').rstrip('/')

# CSRF Protection
csrf = CSRFProtect(app)

# Request size limits (16KB max payload)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024  # 16KB

# Email validation regex (RFC 5322 compliant pattern)
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?@'
    r'[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$'
)

# Simple rate limiting storage (in production, use Redis or similar)
rate_limit_storage = {}

# Resend API configuration
RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
RESEND_API_URL = 'https://api.resend.com/emails'

# Sender email (must be from a verified domain in Resend)
# Options: 
# - Use your verified domain: 'contact@estada.dev'
# - Or use Resend's test domain: 'onboarding@resend.dev' (for testing only)
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'onboarding@resend.dev')
SENDER_NAME = os.getenv('SENDER_NAME', 'Estada Contact Form')

# Development mode: If True, only sends to TEST_EMAIL (for Resend's test mode)
# Set to False and verify domain to send to all recipients
DEV_MODE = os.getenv('DEV_MODE', 'True').lower() == 'true'
TEST_EMAIL = os.getenv('TEST_EMAIL', 'atrendov1@gmail.com')  # Your Resend account email

# Recipient emails (only used when DEV_MODE=False and domain is verified)
# IMPORTANT: These email addresses MUST have working mail servers (MX records)
# If using @estada.dev addresses, you must set up email hosting/forwarding first
# For testing, use real email addresses (e.g., Gmail) that definitely work
RECIPIENT_EMAILS = [
    'atrendov1@gmail.com',
]

# Once email forwarding is set up, uncomment these and comment out the Gmail above:
# RECIPIENT_EMAILS = [
#     'your-real-email@gmail.com',  # Replace with actual working email
#     'another-real-email@gmail.com',  # Replace with actual working email
# ]

# Rate limiting configuration
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '5'))  # requests per window
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))  # seconds

def rate_limit(f):
    """Simple rate limiting decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not RATE_LIMIT_ENABLED:
            return f(*args, **kwargs)
        
        client_ip = request.remote_addr
        now = datetime.now()
        
        # Clean old entries
        if client_ip in rate_limit_storage:
            rate_limit_storage[client_ip] = [
                ts for ts in rate_limit_storage[client_ip]
                if now - ts < timedelta(seconds=RATE_LIMIT_WINDOW)
            ]
        else:
            rate_limit_storage[client_ip] = []
        
        # Check rate limit
        if len(rate_limit_storage[client_ip]) >= RATE_LIMIT_REQUESTS:
            return jsonify({
                'success': False,
                'code': 'rate_limited',
                'message': 'Too many requests. Please try again later.'
            }), 429
        
        # Add current request timestamp
        rate_limit_storage[client_ip].append(now)
        
        return f(*args, **kwargs)
    return decorated_function

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle request size limit exceeded"""
    return jsonify({'success': False, 'code': 'too_large', 'message': 'Request too large. Please reduce the size of your message.'}), 413

# Everything is served from this origin: fonts, scripts, styles, images, video.
# 'unsafe-inline' for styles covers the @font-face block in the page head and
# the style attributes script.js sets. JSON-LD blocks are data, not scripts.
CONTENT_SECURITY_POLICY = '; '.join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "font-src 'self'",
    "media-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])

@app.after_request
def set_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = CONTENT_SECURITY_POLICY
    if not app.config['DEBUG']:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # static_url() adds a content hash as ?v=, so a versioned file never changes
    if request.path.startswith('/static/') and request.args.get('v') and response.status_code in (200, 206, 304):
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    return response

# ----------------------------------------
# Pages: Macedonian at the root, English under /en/
# ----------------------------------------

# lastmod goes into the sitemap. Update it when a page's content changes.
PAGES = {
    'index': {'template': 'index.html', 'paths': {'mk': '/', 'en': '/en/'}, 'lastmod': '2026-10-07'},
    'about': {'template': 'about.html', 'paths': {'mk': '/about', 'en': '/en/about'}, 'lastmod': '2026-10-07'},
    'technologies': {'template': 'technologies.html', 'paths': {'mk': '/technologies', 'en': '/en/technologies'}, 'lastmod': '2026-10-07'},
    'privacy': {'template': 'privacy.html', 'paths': {'mk': '/privacy', 'en': '/en/privacy'}, 'lastmod': '2026-10-07'},
}

def make_page_view(endpoint, template):
    def view(lang):
        g.lang = lang
        return render_template(template, page=endpoint)
    view.__name__ = endpoint
    return view

for _endpoint, _page in PAGES.items():
    _view = make_page_view(_endpoint, _page['template'])
    for _lang, _path in _page['paths'].items():
        app.add_url_rule(_path, _endpoint, _view, defaults={'lang': _lang})

def current_lang():
    return g.get('lang', DEFAULT_LANG)

def translate(key, **kwargs):
    value = STRINGS[current_lang()][key]
    return value.format(**kwargs) if kwargs else value

def pick(value):
    """Return the current language's entry from a {'mk': ..., 'en': ...} dict."""
    return value[current_lang()] if isinstance(value, dict) else value

def page_url(endpoint, lang=None):
    return url_for(endpoint, lang=lang or current_lang())

def absolute_url(endpoint, lang=None):
    return SITE_URL + page_url(endpoint, lang)

_static_hashes = {}

def static_url(filename):
    """URL for a static file with a content hash, so it can be cached for a year."""
    path = os.path.join(app.static_folder, filename)
    mtime = os.path.getmtime(path)
    cached = _static_hashes.get(filename)
    if cached is None or cached[0] != mtime:
        with open(path, 'rb') as f:
            cached = (mtime, hashlib.sha256(f.read()).hexdigest()[:10])
        _static_hashes[filename] = cached
    return url_for('static', filename=filename, v=cached[1])

def hreflang_alternates(endpoint):
    links = [{'hreflang': lang, 'href': absolute_url(endpoint, lang)} for lang in LANGS]
    links.append({'hreflang': 'x-default', 'href': absolute_url(endpoint, DEFAULT_LANG)})
    return links

BUSINESS_DESCRIPTION = {
    'mk': 'Веб студио од Струмица што дизајнира, изработува и хостира веб-сајтови и апликации за клиенти низ Македонија, и снима и монтира видео за социјални мрежи.',
    'en': 'Web studio in Strumica that designs, builds, and hosts websites and apps for clients across North Macedonia, and films and edits video for social media.',
}

def build_schema(page):
    """JSON-LD graph for a page. Every page carries the full entity set, so no @id points at another URL."""
    lang = current_lang()
    website_id = f'{SITE_URL}/#website'
    business_id = f'{SITE_URL}/#business'
    founder_id = f'{SITE_URL}/#founder'
    url = absolute_url(page)

    organization = {
        '@type': 'ProfessionalService',
        '@id': business_id,
        'name': business.NAME,
        'url': f'{SITE_URL}/',
        'description': BUSINESS_DESCRIPTION[lang],
        'logo': SITE_URL + url_for('static', filename='img/apple-touch-icon.png'),
        'image': SITE_URL + url_for('static', filename='img/og.png'),
        'email': business.EMAIL,
        'address': {
            '@type': 'PostalAddress',
            'addressLocality': business.CITY['en'],
            'postalCode': business.POSTAL_CODE,
            'addressCountry': business.COUNTRY_CODE,
        },
        'areaServed': [
            {'@type': 'City', 'name': business.CITY['en']},
            {'@type': 'Country', 'name': 'North Macedonia'},
        ],
        'knowsLanguage': list(LANGS),
        'founder': {'@id': founder_id},
        'sameAs': [u for u in (business.INSTAGRAM, business.FACEBOOK, business.LINKEDIN, business.GITHUB) if u],
        'hasOfferCatalog': {
            '@type': 'OfferCatalog',
            'name': STRINGS[lang]['services.title'],
            'itemListElement': [
                {'@type': 'Offer', 'itemOffered': {
                    '@type': 'Service',
                    'name': STRINGS[lang]['services.web.title'],
                    'description': STRINGS[lang]['services.web.desc'],
                }},
                {'@type': 'Offer', 'itemOffered': {
                    '@type': 'Service',
                    'name': STRINGS[lang]['services.video.title'],
                    'description': STRINGS[lang]['services.video.desc'],
                }},
            ],
        },
    }
    if business.PHONE:
        organization['telephone'] = business.PHONE

    founder = {
        '@type': 'Person',
        '@id': founder_id,
        'name': business.FOUNDER['en'],
        'alternateName': business.FOUNDER['mk'],
        'url': business.FOUNDER_URL,
        'jobTitle': 'Founder',
        'worksFor': {'@id': business_id},
        'image': SITE_URL + url_for('static', filename='img/andrej.webp'),
        'knowsAbout': ['Web development', 'Web design', 'Python', 'Flask', 'FastAPI', 'React', 'Video editing'],
    }

    website = {
        '@type': 'WebSite',
        '@id': website_id,
        'url': f'{SITE_URL}/',
        'name': business.NAME,
        'inLanguage': list(LANGS),
        'publisher': {'@id': business_id},
    }

    webpage = {
        '@type': 'AboutPage' if page == 'about' else 'WebPage',
        '@id': f'{url}#webpage',
        'url': url,
        'name': STRINGS[lang][f'meta.{page}.title'],
        'description': STRINGS[lang][f'meta.{page}.description'],
        'inLanguage': lang,
        'isPartOf': {'@id': website_id},
        'about': {'@id': business_id},
    }
    if page == 'about':
        webpage['mainEntity'] = {'@id': founder_id}

    return {'@context': 'https://schema.org', '@graph': [website, organization, founder, webpage]}

@app.context_processor
def inject_template_helpers():
    lang = current_lang()
    return {
        'site_url': SITE_URL,
        'lang': lang,
        'other_lang': next(l for l in LANGS if l != lang),
        'og_locale': OG_LOCALES[lang],
        'og_locale_alternate': [OG_LOCALES[l] for l in LANGS if l != lang],
        't': translate,
        'pick': pick,
        'page_url': page_url,
        'absolute_url': absolute_url,
        'static_url': static_url,
        'hreflang_alternates': hreflang_alternates,
        'build_schema': build_schema,
        'js_messages': lambda: {k[len('js.'):]: v for k, v in STRINGS[lang].items() if k.startswith('js.')},
        'strings': STRINGS,
        'business': business,
        'year': datetime.now().year,
    }

def text_response(template, mimetype, **context):
    response = make_response(render_template(template, **context))
    response.mimetype = mimetype
    return response

@app.route('/robots.txt')
def robots_txt():
    return text_response('seo/robots.txt', 'text/plain')

@app.route('/sitemap.xml')
def sitemap_xml():
    entries = [
        {
            'loc': absolute_url(endpoint, lang),
            'lastmod': page['lastmod'],
            'alternates': hreflang_alternates(endpoint),
        }
        for endpoint, page in PAGES.items()
        for lang in LANGS
    ]
    return text_response('seo/sitemap.xml', 'application/xml', entries=entries)

@app.route('/llms.txt')
def llms_txt():
    return text_response('seo/llms.txt', 'text/plain')

@app.route('/api/csrf-token')
def get_csrf_token():
    """Get CSRF token for form submission"""
    return jsonify({'csrf_token': generate_csrf()})

@app.route('/api/debug/config')
def debug_config():
    """Debug endpoint to check configuration (protected - only available in DEBUG mode)"""
    if not app.config['DEBUG']:
        return jsonify({'error': 'Not found'}), 404
    
    return jsonify({
        'RESEND_API_KEY_present': bool(RESEND_API_KEY),
        'RESEND_API_KEY_length': len(RESEND_API_KEY) if RESEND_API_KEY else 0,
        'DEV_MODE': DEV_MODE,
        'SENDER_EMAIL': SENDER_EMAIL,
        'SENDER_NAME': SENDER_NAME,
        'TEST_EMAIL': TEST_EMAIL,
        'RECIPIENT_EMAILS': RECIPIENT_EMAILS,
        'will_send_to': [TEST_EMAIL] if DEV_MODE else RECIPIENT_EMAILS
    })

@app.route('/api/contact', methods=['POST'])
@csrf.exempt  # We'll handle CSRF manually via token in request
@rate_limit
def contact():
    """Handle contact form submissions"""
    try:
        # Check request size
        if request.content_length and request.content_length > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'success': False, 'code': 'too_large', 'message': 'Request too large.'}), 413
        
        data = request.get_json()
        
        # Validate CSRF token
        csrf_token = data.get('csrf_token')
        if not csrf_token:
            app.logger.warning('Contact form submission missing CSRF token')
            return jsonify({'success': False, 'code': 'csrf', 'message': 'Security validation failed. Please refresh the page and try again.'}), 403
        
        try:
            # Validate CSRF token (this will raise an exception if invalid)
            validate_csrf(csrf_token)
        except Exception as e:
            app.logger.warning(f'Invalid CSRF token: {str(e)}')
            return jsonify({'success': False, 'code': 'csrf', 'message': 'Security validation failed. Please refresh the page and try again.'}), 403
        
        # Honeypot field check (bots often fill hidden fields)
        honeypot = data.get('website', '').strip()  # Hidden field that should be empty
        if honeypot:
            app.logger.warning(f'Honeypot triggered from IP {request.remote_addr}')
            # Return success to avoid revealing the honeypot
            return jsonify({'success': True, 'message': 'Message sent successfully!'}), 200
        
        # Validate required fields
        if not data.get('name') or not data.get('email'):
            return jsonify({'success': False, 'code': 'missing_fields', 'message': 'Name and email are required'}), 400
        
        # Sanitize and validate input
        name = str(data.get('name', '')).strip()[:100]  # Limit length
        email = str(data.get('email', '')).strip().lower()[:255]  # Limit length
        service = str(data.get('service', 'Not specified')).strip()[:50]
        message = str(data.get('message', 'No message provided')).strip()[:2000]  # Limit length
        
        # Enhanced email validation using regex
        if not EMAIL_REGEX.match(email):
            return jsonify({'success': False, 'code': 'invalid_email', 'message': 'Invalid email address format.'}), 400
        
        # Additional email validation: check for suspicious patterns
        if email.count('@') != 1:
            return jsonify({'success': False, 'code': 'invalid_email', 'message': 'Invalid email address format.'}), 400
        
        # Block common disposable email domains (optional - can be expanded)
        disposable_domains = ['tempmail.com', 'guerrillamail.com', '10minutemail.com']
        email_domain = email.split('@')[1].lower()
        if email_domain in disposable_domains:
            app.logger.warning(f'Blocked disposable email domain: {email_domain}')
            return jsonify({'success': False, 'code': 'disposable_email', 'message': 'Please use a valid business email address.'}), 400
        
        # Basic spam protection - check for common spam patterns
        spam_keywords = ['http://', 'https://', 'www.']
        if any(keyword in message.lower() for keyword in spam_keywords) and len(message) < 20:
            app.logger.warning(f'Potential spam detected from {email}')
            # Still send but log it for monitoring
        
        # Create email subject (avoid spam trigger words)
        subject = f'New Inquiry from {name} - Estada Contact Form'
        
        # Create plain text email body with proper formatting
        text_body = f"""New Contact Form Submission

Name: {name}
Email: {email}
Service: {service}

Message:
{message}

---
This email was sent from the Estada contact form.
To reply directly to the sender, use the Reply button.
"""
        
        # Create HTML email body for better deliverability
        # Escape HTML special characters in user input
        def escape_html(text):
            return (str(text)
                    .replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&#x27;'))
        
        name_escaped = escape_html(name)
        email_escaped = escape_html(email)
        service_escaped = escape_html(service)
        message_escaped = escape_html(message).replace('\n', '<br>')
        
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff;">
    <div style="background-color: #006cc4; color: #ffffff; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
        <h1 style="margin: 0; font-size: 24px; font-weight: 600;">New Contact Form Submission</h1>
    </div>
    <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; border: 1px solid #e9ecef; border-top: none;">
        <div style="margin-bottom: 20px;">
            <strong style="color: #006cc4; display: inline-block; min-width: 100px;">Name:</strong>
            <span>{name_escaped}</span>
        </div>
        <div style="margin-bottom: 20px;">
            <strong style="color: #006cc4; display: inline-block; min-width: 100px;">Email:</strong>
            <a href="mailto:{email_escaped}" style="color: #006cc4; text-decoration: none;">{email_escaped}</a>
        </div>
        <div style="margin-bottom: 20px;">
            <strong style="color: #006cc4; display: inline-block; min-width: 100px;">Service:</strong>
            <span>{service_escaped}</span>
        </div>
        <hr style="border: none; border-top: 2px solid #e9ecef; margin: 30px 0;">
        <div style="margin-bottom: 20px;">
            <strong style="color: #006cc4; display: block; margin-bottom: 10px;">Message:</strong>
            <div style="background-color: #ffffff; padding: 15px; border-radius: 4px; border-left: 4px solid #006cc4; white-space: pre-wrap;">{message_escaped}</div>
        </div>
        <hr style="border: none; border-top: 1px solid #e9ecef; margin: 30px 0;">
        <p style="font-size: 12px; color: #6c757d; margin: 0; text-align: center;">
            This email was sent from the Estada contact form.<br>
            To reply directly to the sender, use the Reply button.
        </p>
    </div>
</body>
</html>
"""
        
        # Send email to all recipients using Resend API
        try:
            app.logger.info(f'=== Contact Form Submission ===')
            app.logger.info(f'RESEND_API_KEY present: {bool(RESEND_API_KEY)}')
            app.logger.info(f'RESEND_API_KEY length: {len(RESEND_API_KEY) if RESEND_API_KEY else 0}')
            app.logger.info(f'DEV_MODE: {DEV_MODE}')
            app.logger.info(f'SENDER_EMAIL: {SENDER_EMAIL}')
            app.logger.info(f'TEST_EMAIL: {TEST_EMAIL}')
            
            if not RESEND_API_KEY:
                app.logger.error('RESEND_API_KEY not configured')
                return jsonify({'success': False, 'message': 'Email service not configured. Please contact support.'}), 500
            
            # Determine recipients based on mode
            if DEV_MODE:
                # Development mode: send to test email only (Resend test mode requirement)
                recipients = [TEST_EMAIL]
                app.logger.info(f'DEV_MODE: Sending to test email {TEST_EMAIL} only')
            else:
                # Production mode: send to all recipients (requires verified domain)
                recipients = RECIPIENT_EMAILS
                app.logger.info(f'Production mode: Sending to {len(recipients)} recipients: {recipients}')
            
            # Prepare email payload with improved deliverability
            # Using verified sender email, with user's email in reply_to for direct replies
            email_payload = {
                'from': f'{SENDER_NAME} <{SENDER_EMAIL}>',
                'to': recipients,
                'subject': subject,
                'text': text_body,  # Plain text version
                'html': html_body,   # HTML version for better deliverability
                'reply_to': email,   # Replies will go directly to the user
                'headers': {
                    'X-Entity-Ref-ID': f'estada-contact-{int(datetime.now().timestamp())}',
                    'X-Priority': '1',  # Normal priority (not urgent, not bulk)
                    'X-Mailer': 'Estada Contact Form',  # Identifies the sender
                }
            }
            
            app.logger.info(f'Sending email via Resend: {subject} from {email}')
            
            # Send email via Resend API
            response = requests.post(
                RESEND_API_URL,
                headers={
                    'Authorization': f'Bearer {RESEND_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json=email_payload,
                timeout=10  # 10 second timeout
            )
            
            # Check response
            app.logger.info(f'Resend API response status: {response.status_code}')
            app.logger.info(f'Resend API response body: {response.text}')
            
            if response.status_code == 200:
                response_data = response.json()
                app.logger.info(f'Email sent successfully: {response_data.get("id", "unknown")}')
                return jsonify({
                    'success': True, 
                    'message': 'Message sent successfully! We\'ll be in touch soon.'
                }), 200
            else:
                # Log detailed error
                error_text = response.text
                app.logger.error(f'Resend API error: {response.status_code} - {error_text}')
                try:
                    error_json = response.json()
                    app.logger.error(f'Resend API error details: {error_json}')
                except:
                    pass
                
                # Provide user-friendly error message
                if response.status_code == 401:
                    error_msg = 'Email service authentication failed. Please contact support.'
                elif response.status_code == 403:
                    # Resend test mode limitation - only can send to account owner
                    if DEV_MODE:
                        error_msg = 'Email service configuration issue. Please contact support.'
                    else:
                        error_msg = 'Domain verification required. Please verify your domain in Resend or enable DEV_MODE for testing.'
                elif response.status_code == 422:
                    error_msg = 'Invalid email address. Please check and try again.'
                else:
                    error_msg = 'Failed to send email. Please try again later or contact us directly.'
                
                return jsonify({'success': False, 'code': 'send_failed', 'message': error_msg}), 500
                
        except requests.exceptions.Timeout:
            app.logger.error('Resend API request timed out')
            return jsonify({'success': False, 'message': 'Request timed out. Please try again.'}), 500
        except requests.exceptions.RequestException as e:
            app.logger.error(f'Network error sending email: {str(e)}')
            return jsonify({'success': False, 'message': 'Network error. Please check your connection and try again.'}), 500
        except Exception as e:
            app.logger.error(f'Unexpected error sending email: {str(e)}')
            return jsonify({'success': False, 'message': 'An unexpected error occurred. Please try again later.'}), 500
            
    except Exception as e:
        app.logger.error(f'Contact form error: {str(e)}')
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500


if __name__ == '__main__':
    # Production server configuration
    port = int(os.getenv('PORT', 8082))
    debug = app.config['DEBUG']
    
    if debug:
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        # For production, use a proper WSGI server like gunicorn
        # Run with: gunicorn -w 4 -b 0.0.0.0:8082 app:app
        app.run(host='0.0.0.0', port=port, debug=False)

