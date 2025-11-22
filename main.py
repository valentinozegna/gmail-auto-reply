#!/usr/bin/env python3
"""
Gmail Auto-Reply Script
Monitors Gmail inbox and auto-replies to emails from a specific sender
Uses IMAP IDLE for minimal latency (2-3 seconds)
"""

import os
import sys
import time
import base64
import email
import imaplib
import socket
from email.mime.text import MIMEText
from datetime import datetime
from typing import Optional, List, Any, cast
from email.message import Message

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Import configuration
try:
    from config import (
        TARGET_SENDER_EMAIL,
        AUTO_REPLY_MESSAGE,
        CREDENTIALS_FILE,
        TOKEN_FILE,
        GMAIL_SCOPES
    )
except ImportError:
    print("\nERROR: config.py not found!")
    print("Please create config.py with your settings.")
    print("See config.py.example for reference.")
    sys.exit(1)

# Validate configuration - NO DEFAULTS ALLOWED
if not TARGET_SENDER_EMAIL:
    print("\nERROR: TARGET_SENDER_EMAIL is not configured!")
    print("Please edit config.py and set your target sender email address.")
    print("Example: TARGET_SENDER_EMAIL = 'their.email@example.com'")
    sys.exit(1)

if not AUTO_REPLY_MESSAGE:
    print("\nERROR: AUTO_REPLY_MESSAGE is not configured!")
    print("Please edit config.py and set your auto-reply message.")
    print("Example: AUTO_REPLY_MESSAGE = 'Got it! I can do it.'")
    sys.exit(1)

# Your Gmail address (will be populated from credentials)
YOUR_EMAIL = ''


def get_gmail_credentials() -> Credentials:
    """
    Authenticates and returns Gmail credentials.
    First run will open browser for OAuth2 authorization.
    """
    creds: Optional[Credentials] = None

    # Token file stores access and refresh tokens
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)

    # If no valid credentials, do OAuth2 flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"\nERROR: {CREDENTIALS_FILE} not found!")
                print("Please download OAuth2 credentials from Google Cloud Console")
                print("See README.md for setup instructions")
                sys.exit(1)

            print("Starting OAuth2 authentication flow...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, GMAIL_SCOPES)
            creds = cast(Credentials, flow.run_local_server(port=0))

        # Save credentials for future runs
        if creds:
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            print(f"Credentials saved to {TOKEN_FILE}")

    if not creds:
        print("\nERROR: Failed to get credentials")
        sys.exit(1)

    return creds


def generate_oauth2_string(username: str, access_token: str) -> str:
    """
    Generates OAuth2 authentication string for IMAP.
    """
    auth_string = f'user={username}\x01auth=Bearer {access_token}\x01\x01'
    return auth_string


def send_reply(
    gmail_service: Any,
    to_email: str,
    subject: str,
    message_id: str,
    thread_id: Optional[str],
    references: str
) -> bool:
    """
    Sends an auto-reply using Gmail API.

    Args:
        gmail_service: Authorized Gmail API service instance
        to_email: Recipient email address
        subject: Original email subject
        message_id: Message-ID of original email for threading
        thread_id: Gmail thread ID
        references: References header for proper threading

    Returns:
        True if reply sent successfully, False otherwise
    """
    try:
        # Create reply message
        message = MIMEText(AUTO_REPLY_MESSAGE)
        message['to'] = to_email
        message['from'] = YOUR_EMAIL
        message['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject

        # Add threading headers for proper conversation threading
        if message_id:
            message['In-Reply-To'] = message_id
            message['References'] = f"{references} {message_id}" if references else message_id

        # Encode and send
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}

        if thread_id:
            body['threadId'] = thread_id

        result = gmail_service.users().messages().send(
            userId='me',
            body=body
        ).execute()

        print(f"  ✓ Reply sent! Message ID: {result['id']}")
        return True

    except Exception as e:
        print(f"  ✗ Failed to send reply: {e}")
        return False


def parse_email_from(from_header: str) -> str:
    """
    Extracts email address from From header.
    Handles formats like "Name <email@example.com>" or "email@example.com"
    """
    if '<' in from_header and '>' in from_header:
        return from_header.split('<')[1].split('>')[0].strip().lower()
    return from_header.strip().lower()


class ImapIdleClient:
    """IMAP client with IDLE support using standard imaplib."""

    def __init__(self, host: str, username: str, access_token: str):
        self.host = host
        self.username = username
        self.access_token = access_token
        self.imap: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> None:
        """Connect to IMAP server and authenticate."""
        self.imap = imaplib.IMAP4_SSL(self.host)

        # Authenticate using OAuth2
        auth_string = generate_oauth2_string(self.username, self.access_token)
        self.imap.authenticate('XOAUTH2', lambda _: auth_string.encode())

        # Select INBOX
        self.imap.select('INBOX')

    def start_idle(self) -> None:
        """Start IDLE mode."""
        if self.imap:
            tag = self.imap._new_tag().decode()
            self.imap.send(f'{tag} IDLE\r\n'.encode())
            # Wait for continuation response
            self.imap.readline()

    def check_idle(self, timeout: int = 300) -> bool:
        """
        Check for IDLE responses.

        Args:
            timeout: Timeout in seconds

        Returns:
            True if new data received, False if timeout
        """
        if not self.imap:
            return False

        try:
            # Set socket timeout
            self.imap.sock.settimeout(timeout)

            # Read response
            line = self.imap.readline()

            if line:
                return b'EXISTS' in line or b'RECENT' in line
            return False

        except socket.timeout:
            return False
        except Exception:
            return False

    def stop_idle(self) -> None:
        """Stop IDLE mode."""
        if self.imap:
            self.imap.send(b'DONE\r\n')
            # Read tagged response
            self.imap.readline()
            self.imap.readline()

    def search_unseen_from(self, sender: str) -> List[str]:
        """Search for unseen messages from specific sender."""
        if not self.imap:
            return []

        try:
            search_criteria = f'(UNSEEN FROM "{sender}")'
            print(f"  → DEBUG: IMAP search criteria: {search_criteria}")
            status, data = self.imap.search(None, search_criteria)
            print(f"  → DEBUG: IMAP search status: {status}, data: {data}")
            if data and data[0]:
                msg_ids = data[0].decode().split()
                print(f"  → DEBUG: Found message IDs: {msg_ids}")
                return msg_ids
            return []
        except Exception as e:
            print(f"  → DEBUG: IMAP search exception: {e}")
            return []

    def fetch_message(self, msg_id: str) -> Optional[Message]:
        """Fetch a message by ID."""
        if not self.imap:
            return None

        try:
            _, data = self.imap.fetch(msg_id, '(RFC822)')
            if data and data[0] and isinstance(data[0], tuple):
                email_body = data[0][1]
                if isinstance(email_body, bytes):
                    return email.message_from_bytes(email_body)
            return None
        except Exception:
            return None

    def noop(self) -> None:
        """Send NOOP command (keepalive)."""
        if self.imap:
            self.imap.noop()

    def logout(self) -> None:
        """Logout from IMAP server."""
        if self.imap:
            try:
                self.imap.logout()
            except Exception:
                pass


def monitor_inbox() -> None:
    """
    Main monitoring loop using IMAP IDLE for instant notifications.
    """
    global YOUR_EMAIL

    print("=" * 60)
    print("Gmail Auto-Reply Monitor")
    print("=" * 60)

    # Authenticate with Gmail
    print("\n[1/3] Authenticating with Gmail...")
    creds = get_gmail_credentials()

    # Build Gmail API service for sending replies
    gmail_service = build('gmail', 'v1', credentials=creds)

    # Get user's email address
    profile = gmail_service.users().getProfile(userId='me').execute()
    YOUR_EMAIL = profile['emailAddress']
    print(f"  ✓ Authenticated as: {YOUR_EMAIL}")

    print(f"\n[2/3] Monitoring for emails from: {TARGET_SENDER_EMAIL}")
    print("  ✓ Using IMAP IDLE (2-3 second latency)")
    print(f"  ✓ Auto-reply message: '{AUTO_REPLY_MESSAGE}'")

    print("\n[3/3] Connecting to Gmail IMAP...")

    # Track processed message IDs to avoid duplicates
    processed_messages: set[str] = set()

    while True:
        imap_client: Optional[ImapIdleClient] = None
        try:
            # Refresh token if needed
            if creds.expired and creds.refresh_token:
                print("  → Refreshing access token...")
                creds.refresh(Request())

            # Connect to Gmail IMAP with OAuth2
            imap_client = ImapIdleClient('imap.gmail.com', YOUR_EMAIL, creds.token or '')
            imap_client.connect()

            print("  ✓ Connected to Gmail IMAP")

            # Check for existing unread messages on startup
            print("\n  → Checking for existing unread messages...")
            existing_messages = imap_client.search_unseen_from(TARGET_SENDER_EMAIL)
            if existing_messages:
                print(f"  ⚠ Found {len(existing_messages)} existing unread message(s) from {TARGET_SENDER_EMAIL}")
                print("  → Processing existing messages...")

                for msg_id in existing_messages:
                    if msg_id in processed_messages:
                        continue

                    processed_messages.add(msg_id)
                    email_message = imap_client.fetch_message(msg_id)

                    if email_message:
                        from_addr = parse_email_from(email_message.get('From', ''))
                        subject = email_message.get('Subject', '(no subject)')
                        message_id_header = email_message.get('Message-ID', '')
                        references = email_message.get('References', '')

                        print(f"  → From: {from_addr}")
                        print(f"  → Subject: {subject}")

                        if from_addr == TARGET_SENDER_EMAIL.lower():
                            print("  → Sending auto-reply...")

                            try:
                                gmail_msg = gmail_service.users().messages().list(
                                    userId='me',
                                    q=f'from:{TARGET_SENDER_EMAIL}',
                                    maxResults=1
                                ).execute()

                                thread_id = None
                                if 'messages' in gmail_msg and gmail_msg['messages']:
                                    thread_id = gmail_msg['messages'][0]['threadId']

                                send_reply(
                                    gmail_service,
                                    from_addr,
                                    subject,
                                    message_id_header,
                                    thread_id,
                                    references
                                )
                            except Exception as e:
                                print(f"  ✗ Error: {e}")
                                send_reply(
                                    gmail_service,
                                    from_addr,
                                    subject,
                                    message_id_header,
                                    None,
                                    references
                                )
            else:
                print("  ✓ No existing unread messages")

            print("\n" + "=" * 60)
            print(f"MONITORING ACTIVE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            print("Waiting for emails... (Press Ctrl+C to stop)\n")

            # IDLE monitoring loop
            while True:
                # Start IDLE mode
                imap_client.start_idle()

                # Wait for notifications (5-minute timeout for keepalive)
                has_new = imap_client.check_idle(timeout=300)

                # Stop IDLE mode
                imap_client.stop_idle()

                if has_new:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] New activity detected!")

                    # Search for unread emails from target sender
                    messages = imap_client.search_unseen_from(TARGET_SENDER_EMAIL)
                    print(f"  → DEBUG: search_unseen_from returned {len(messages)} message(s)")

                    if messages:
                        print(f"  → Found {len(messages)} new message(s) from {TARGET_SENDER_EMAIL}")

                        for msg_id in messages:
                            # Skip if already processed
                            if msg_id in processed_messages:
                                continue

                            processed_messages.add(msg_id)

                            # Fetch message
                            email_message = imap_client.fetch_message(msg_id)

                            if not email_message:
                                continue

                            # Extract details
                            from_addr = parse_email_from(email_message.get('From', ''))
                            subject = email_message.get('Subject', '(no subject)')
                            message_id_header = email_message.get('Message-ID', '')
                            references = email_message.get('References', '')

                            print(f"  → From: {from_addr}")
                            print(f"  → Subject: {subject}")

                            # Double-check sender (case-insensitive)
                            if from_addr == TARGET_SENDER_EMAIL.lower():
                                print("  → Sending auto-reply...")

                                # Get Gmail message for thread ID
                                try:
                                    # Search for the message by sender to get thread ID
                                    gmail_msg = gmail_service.users().messages().list(
                                        userId='me',
                                        q=f'from:{TARGET_SENDER_EMAIL}',
                                        maxResults=1
                                    ).execute()

                                    thread_id = None
                                    if 'messages' in gmail_msg and gmail_msg['messages']:
                                        thread_id = gmail_msg['messages'][0]['threadId']

                                    # Send reply
                                    send_reply(
                                        gmail_service,
                                        from_addr,
                                        subject,
                                        message_id_header,
                                        thread_id,
                                        references
                                    )

                                except Exception as e:
                                    print(f"  ✗ Error getting thread ID: {e}")
                                    # Try sending without thread ID
                                    send_reply(
                                        gmail_service,
                                        from_addr,
                                        subject,
                                        message_id_header,
                                        None,
                                        references
                                    )
                            else:
                                print("  → Skipped (sender mismatch)")

                    print()
                else:
                    # Timeout - send keepalive NOOP
                    imap_client.noop()

                # Check if token needs refresh
                if creds.expired:
                    print("  → Token expired, reconnecting...")
                    break

        except KeyboardInterrupt:
            print("\n\nStopping monitor (user interrupt)...")
            if imap_client:
                imap_client.logout()
            sys.exit(0)

        except Exception as e:
            print(f"\n✗ Connection error: {e}")
            print("  → Reconnecting in 5 seconds...")
            if imap_client:
                imap_client.logout()
            time.sleep(5)


if __name__ == '__main__':
    monitor_inbox()
