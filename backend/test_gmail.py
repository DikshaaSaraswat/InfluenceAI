from app.gmail_service import get_gmail_service

try:
    service = get_gmail_service()
    print("Gmail authentication successful!")
    print("Gmail API service is ready.")

except Exception as e:
    print("Gmail authentication failed:")
    print(e)
