#!/usr/bin/env python3
"""Test script to check Resend API configuration"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
RESEND_API_URL = 'https://api.resend.com/emails'
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'onboarding@resend.dev')
SENDER_NAME = os.getenv('SENDER_NAME', 'Estada Contact Form')
DEV_MODE = os.getenv('DEV_MODE', 'True').lower() == 'true'
TEST_EMAIL = os.getenv('TEST_EMAIL', 'andrejt@estada.dev')

print("=== Resend API Configuration Test ===")
print(f"RESEND_API_KEY present: {bool(RESEND_API_KEY)}")
print(f"RESEND_API_KEY length: {len(RESEND_API_KEY) if RESEND_API_KEY else 0}")
print(f"DEV_MODE: {DEV_MODE}")
print(f"SENDER_EMAIL: {SENDER_EMAIL}")
print(f"SENDER_NAME: {SENDER_NAME}")
print(f"TEST_EMAIL: {TEST_EMAIL}")
print()

if not RESEND_API_KEY:
    print("ERROR: RESEND_API_KEY not set!")
    exit(1)

# Determine recipients
if DEV_MODE:
    recipients = [TEST_EMAIL]
    print(f"DEV_MODE: Will send to test email: {TEST_EMAIL}")
else:
    recipients = ['andrejt@estada.dev', 'krstem@estada.dev', 'filipm@estada.dev']
    print(f"Production mode: Will send to: {recipients}")

print()
print("Sending test email...")

# Prepare email payload
email_payload = {
    'from': f'{SENDER_NAME} <{SENDER_EMAIL}>',
    'to': recipients,
    'subject': 'Test Email from Estada',
    'text': 'This is a test email from the Estada contact form system.'
}

try:
    response = requests.post(
        RESEND_API_URL,
        headers={
            'Authorization': f'Bearer {RESEND_API_KEY}',
            'Content-Type': 'application/json'
        },
        json=email_payload,
        timeout=10
    )
    
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        response_data = response.json()
        print(f"SUCCESS! Email sent. ID: {response_data.get('id', 'unknown')}")
    else:
        print(f"ERROR! Failed to send email.")
        try:
            error_json = response.json()
            print(f"Error details: {error_json}")
        except:
            pass
            
except Exception as e:
    print(f"EXCEPTION: {str(e)}")
    import traceback
    traceback.print_exc()

