from app.ai import classify_influencer_reply

reply = {
    "subject": "Re: Collaboration Opportunity",
    "body": "Thank you for reaching out! I am interested in learning more about the campaign."
}

influencer = {
    "name": "Priya Mehta",
    "niche": "Lifestyle"
}

result = classify_influencer_reply(reply, influencer)

print("\nAI REPLY ANALYSIS:")
print(result)
