from app.gmail_service import get_gmail_service

service = get_gmail_service()

result = service.users().messages().list(
    userId="me",
    q="in:inbox",
    maxResults=5
).execute()

messages = result.get("messages", [])

print("Gmail read access successful!")
print("Inbox messages retrieved:", len(messages))

for message in messages:
    print("Message ID:", message["id"])
    print("Thread ID:", message["threadId"])
