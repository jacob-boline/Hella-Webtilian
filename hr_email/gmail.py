# hr_email/gmail.py

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pickle
import os
from django.templatetags.static import static
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import requests
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCOPES = ['https://mail.google.com']


def get_service():

    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        # else:
        #     flow = InstalledAppFlow.from_client_secrets_file(
        #         'credentials.json', SCOPES)
        #     creds = flow.run_local_server(port=0)
        else:
            client_secret_url = static('hr_email/client_secret_desktop.json')
            client_secret_text = requests.get(client_secret_url).text
            with open('client_secret_json.json', 'w') as f:
                json.dump(json.loads(client_secret_text), f)
            flow = InstalledAppFlow.from_client_secrets_file('client_secret_json.json', SCOPES)
            creds = flow.run_local_server(port=8001)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    return service


def send_message(service, user_id, message):
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print(f"Message ID: {message['id']}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def create_message_with_attachment(sender, to, subject, message_text):
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    msg = MIMEText(message_text)
    message.attach(msg)

    raw_message = base64.urlsafe_b64encode(message.as_string().encode('utf-8'))
    return {'raw': raw_message.decode('utf-8')}


def sending_message(msgto, subject, message):
    service = get_service()
    user_id = 'me'
    msg = create_message_with_attachment('Admin: <admin@hellareptilian.com>', msgto, subject, message)
    send_message(service, user_id, msg)
