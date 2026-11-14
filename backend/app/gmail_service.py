import base64
from pathlib import Path
from email.message import EmailMessage
from email.utils import parseaddr

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


BASE_DIR = Path(__file__).resolve().parent.parent

CREDENTIALS_FILE = BASE_DIR / "credentials" / "client_secret.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly"
]


def get_gmail_service():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            str(TOKEN_FILE), SCOPES
        )

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                "Google OAuth client_secret.json not found."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE), SCOPES
        )

        creds = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


def send_email(to_email, subject, body):

    if not to_email or not subject or not body:
        raise ValueError(
            "Recipient, subject and email body are required."
        )

    message = EmailMessage()

    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(body)

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    gmail_service = get_gmail_service()

    result = gmail_service.users().messages().send(
        userId="me",
        body={"raw": encoded_message}
    ).execute()

    return {
        "message_id": result["id"],
        "thread_id": result["threadId"],
        "status": "Email sent successfully"
    }


def decode_message_body(payload):

    plain_text = []
    html_text = []

    def extract_parts(part):

        mime_type = part.get("mimeType", "")
        body_data = part.get("body", {}).get("data")

        if body_data:
            decoded = base64.urlsafe_b64decode(
                body_data + "=" * (-len(body_data) % 4)
            ).decode("utf-8", errors="replace")

            if mime_type == "text/plain":
                plain_text.append(decoded)

            elif mime_type == "text/html":
                html_text.append(decoded)

        for nested_part in part.get("parts", []):
            extract_parts(nested_part)

    extract_parts(payload)

    if plain_text:
        return "\n".join(plain_text)

    if html_text:
        return "\n".join(html_text)

    return ""


def get_thread_messages(thread_id):

    if not thread_id:
        raise ValueError("Gmail thread ID is required.")

    gmail_service = get_gmail_service()

    thread = gmail_service.users().threads().get(
        userId="me",
        id=thread_id,
        format="full"
    ).execute()

    messages = []

    for message in thread.get("messages", []):

        headers = {
            header["name"].lower(): header["value"]
            for header in message.get("payload", {}).get("headers", [])
        }

        messages.append({
            "message_id": message.get("id"),
            "thread_id": message.get("threadId"),
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "subject": headers.get("subject", ""),
            "date": headers.get("date", ""),
            "rfc_message_id": headers.get("message-id", ""),
            "references": headers.get("references", ""),
            "in_reply_to": headers.get("in-reply-to", ""),
            "snippet": message.get("snippet", ""),
            "body": decode_message_body(
                message.get("payload", {})
            )
        })

    return messages


def get_incoming_replies(
    thread_id,
    influencer_email,
    original_message_id
):

    if not thread_id:
        raise ValueError("Gmail thread ID is required.")

    if not influencer_email:
        raise ValueError("Influencer email is required.")

    if not original_message_id:
        raise ValueError("Original message ID is required.")

    influencer_email = influencer_email.strip().lower()

    messages = get_thread_messages(thread_id)

    replies = []

    for message in messages:

        if message["message_id"] == original_message_id:
            continue

        sender_email = parseaddr(message["from"])[1].strip().lower()

        if sender_email != influencer_email:
            continue

        message["from"] = sender_email
        replies.append(message)

    return replies


def send_thread_reply(
    thread_id,
    to_email,
    subject,
    body,
    reply_to_message_id
):

    if not thread_id:
        raise ValueError("Gmail thread ID is required.")

    if not to_email:
        raise ValueError("Recipient email is required.")

    if not subject:
        raise ValueError("Email subject is required.")

    if not body or not body.strip():
        raise ValueError("Reply body cannot be empty.")

    if not reply_to_message_id:
        raise ValueError("Original reply message ID is required.")

    messages = get_thread_messages(thread_id)

    original_message = next(
        (
            message for message in messages
            if message["message_id"] == reply_to_message_id
        ),
        None
    )

    if not original_message:
        raise ValueError(
            "Reply-to message was not found in the specified Gmail thread."
        )

    original_rfc_id = original_message["rfc_message_id"]

    if not original_rfc_id:
        raise ValueError(
            "Original email RFC Message-ID header is missing."
        )

    message = EmailMessage()

    message["To"] = to_email
    message["Subject"] = subject
    message["In-Reply-To"] = original_rfc_id

    existing_references = original_message["references"].strip()

    reference_ids = existing_references.split() if existing_references else []

    if original_rfc_id not in reference_ids:
        reference_ids.append(original_rfc_id)

    message["References"] = " ".join(reference_ids)

    message.set_content(body)

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    gmail_service = get_gmail_service()

    result = gmail_service.users().messages().send(
        userId="me",
        body={
            "raw": encoded_message,
            "threadId": thread_id
        }
    ).execute()

    return {
        "message_id": result["id"],
        "thread_id": result["threadId"],
        "status": "Thread reply sent successfully"
    }
