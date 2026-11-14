from app.gmail_service import get_thread_messages

thread_id = "1a1d1f28249c1114"

messages = get_thread_messages(thread_id)

print("Gmail thread retrieval successful!")
print("Messages in thread:", len(messages))

for message in messages:
    print("\nFrom:", message["from"])
    print("To:", message["to"])
    print("Subject:", message["subject"])
    print("Date:", message["date"])
    print("Body retrieved:", bool(message["body"]))
