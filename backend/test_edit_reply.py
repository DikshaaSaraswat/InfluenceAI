from app.database import edit_reply_draft

result = edit_reply_draft(
    reply_id=1,
    suggested_reply="""Hi Priya,

Thank you for your interest in our collaboration!

We would be happy to share our campaign details with you.

Looking forward to hearing from you!

Best regards,
InfluenceAI Team"""
)

print("EDIT RESULT:")
print(result)
