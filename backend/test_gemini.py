from app.ai import client

response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="Say hello to InfluenceAI in one sentence."
)

print(response.text)
