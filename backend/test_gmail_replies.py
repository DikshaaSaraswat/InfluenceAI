import os
from app.gmail_service import get_incoming_replies

thread_id = os.getenv("TEST_GMAIL_THREAD_ID", "").strip()
original_message_id = os.getenv("TEST_GMAIL_MESSAGE_ID", "").strip()
influencer_email = os.getenv("TEST_INFLUENCER_EMAIL", "").strip()

if not all([thread_id, original_message_id, influencer_email]):
    raise ValueError("Set TEST_GMAIL_THREAD_ID, TEST_GMAIL_MESSAGE_ID and TEST_INFLUENCER_EMAIL before running this test.")

replies = get_incoming_replies(
    thread_id=thread_id,
    influencer_email=influencer_email,
    original_message_id=original_message_id
)

print("Reply detection test completed!")
print("Incoming replies found:", len(replies))

for reply in replies:
    print("\nSender:", reply["from"])
    print("Subject:", reply["subject"])
    print("Date:", reply["date"])
    print("Reply body retrieved:", bool(reply["body"]))
