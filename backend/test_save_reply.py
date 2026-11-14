from app.database import save_incoming_reply, get_connection

reply = {
    "message_id": "test_reply_001",
    "thread_id": "test_thread_001",
    "from": "test@example.com",
    "subject": "Re: Collaboration Opportunity",
    "body": "Thank you for reaching out! I am interested in learning more.",
    "date": "2026-11-13"
}

result = save_incoming_reply(
    influencer_id=2,
    reply=reply
)

print("SAVE RESULT:")
print(result)

connection = get_connection()

influencer = connection.execute(
    "SELECT id, name, status FROM influencers WHERE id = 2"
).fetchone()

print("\nINFLUENCER STATUS:")
print(dict(influencer))

saved_reply = connection.execute(
    "SELECT * FROM influencer_replies WHERE gmail_message_id = ?",
    ("test_reply_001",)
).fetchone()

print("\nSAVED REPLY:")
print(dict(saved_reply))

connection.close()
