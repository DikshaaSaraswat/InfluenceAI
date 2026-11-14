from app.gmail_service import send_email

recipient = input("Enter your own Gmail address: ")

try:
    result = send_email(
        to_email=recipient,
        subject="InfluenceAI - Gmail Integration Test",
        body="""Hello!

This is a test email from InfluenceAI.

Gmail API integration is working successfully.

No influencer outreach has been sent.

Regards,
InfluenceAI"""
    )

    print("\nSUCCESS!")
    print(result)

except Exception as e:
    print("\nEMAIL SENDING FAILED!")
    print(e)
