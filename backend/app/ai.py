import os
import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API key not found!")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(api_version="v1beta")
)


def generate_json(prompt):
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )

    if not response.text:
        raise ValueError("AI returned an empty response.")

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        raise ValueError("AI returned an invalid JSON response.")


def analyze_influencer(influencer, brand):

    prompt = f"""
    You are an expert influencer marketing analyst.

    Analyse the influencer's suitability for the given brand campaign.

    INFLUENCER:
    Name: {influencer['name']}
    Username: {influencer['username']}
    Niche: {influencer['niche']}
    Followers: {influencer['followers']}
    Location: {influencer['location']}

    BRAND:
    Name: {brand['name']}
    Niche: {brand['niche']}
    Campaign: {brand['campaign']}

    Return a JSON object with exactly these fields:

    {{
        "relevance_score": number between 0 and 100,
        "category": "influencer category",
        "summary": "short profile summary",
        "reason": "explanation of campaign suitability",
        "recommendation": "High Priority, Medium Priority, or Low Priority"
    }}

    ANALYSIS RULES:

    1. Base the analysis only on the supplied information.
    2. Evaluate relevance primarily through niche and campaign alignment.
    3. Do not invent audience demographics or engagement statistics.
    4. Do not assume followers are interested in the brand.
    5. Do not claim that the influencer has particular audience interests.
    6. Do not assume that location guarantees campaign success.
    7. Do not invent content quality, achievements or brand partnerships.
    8. Use follower count only as contextual information.
    9. Explain limitations when information is insufficient.
    10. Give a reasonable relevance score based on available evidence.
    11. High Priority means strong niche alignment.
    12. Medium Priority means partial alignment or insufficient evidence.
    13. Low Priority means weak or no campaign alignment.
    """

    analysis = generate_json(prompt)

    required_fields = [
        "relevance_score",
        "category",
        "summary",
        "reason",
        "recommendation"
    ]

    for field in required_fields:
        if field not in analysis:
            raise ValueError(
                f"AI analysis is missing the field: {field}"
            )

    score = analysis["relevance_score"]

    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not 0 <= score <= 100
    ):
        raise ValueError("Invalid relevance score returned by AI.")

    if analysis["recommendation"] not in [
        "High Priority",
        "Medium Priority",
        "Low Priority"
    ]:
        raise ValueError("Invalid recommendation returned by AI.")

    return analysis


def generate_outreach_email(influencer, brand):

    if influencer.get("recommendation") == "Low Priority":
        raise ValueError(
            "Cannot generate outreach email for a low-priority influencer."
        )

    prompt = f"""
    You are a professional influencer marketing manager.

    Generate a personalized, friendly and professional
    collaboration outreach email.

    INFLUENCER DETAILS:
    Name: {influencer['name']}
    Username: {influencer['username']}
    Niche: {influencer['niche']}
    Location: {influencer['location']}
    Followers: {influencer['followers']}

    PROFILE ANALYSIS:
    Summary: {influencer.get('summary', 'Not available')}
    Suitability reason: {influencer.get('reason', 'Not available')}

    BRAND DETAILS:
    Name: {brand['name']}
    Niche: {brand['niche']}
    Campaign: {brand['campaign']}

    EMAIL REQUIREMENTS:

    1. Address the influencer by their supplied name.
    2. Introduce the brand and its campaign.
    3. Explain why the influencer was selected using only supplied information.
    4. Mention their niche naturally.
    5. Include a clear call to action asking whether they are interested.
    6. Keep the email concise, natural and professional.
    7. Use [Your Name] and [Your Title] as sender placeholders.
    8. Do not imply that the influencer has already agreed.
    9. Do not invent audience demographics or engagement statistics.
    10. Never claim to have viewed or reviewed their content.
    11. Do not invent achievements, partnerships or brand values.
    12. Do not make unsupported claims about audience interests.
    13. Do not exaggerate the influencer's suitability.
    14. Do not include misleading urgency or false promises.
    15. Do not include an invented sender email address.

    Return a JSON object with exactly these fields:

    {{
        "subject": "Email subject",
        "body": "Complete email body"
    }}
    """

    email = generate_json(prompt)

    if "subject" not in email or "body" not in email:
        raise ValueError("AI returned an incomplete email draft.")

    subject = str(email["subject"]).strip()
    body = str(email["body"]).strip()

    if not subject or not body:
        raise ValueError("Generated email subject or body is empty.")

    opt_out_sentence = (
        "If you would prefer not to receive further collaboration "
        "emails from us, simply reply with 'opt out' and we will "
        "respect your request."
    )

    opt_out_terms = [
        "opt out",
        "unsubscribe",
        "stop receiving"
    ]

    if not any(term in body.lower() for term in opt_out_terms):
        body = body.rstrip() + "\n\n" + opt_out_sentence

    return {
        "subject": subject,
        "body": body
    }


def classify_influencer_reply(reply, influencer):

    prompt = f"""
    You are an expert influencer marketing communication assistant.

    Analyze the incoming influencer email reply.

    INFLUENCER:
    Name: {influencer.get('name', 'Unknown')}
    Niche: {influencer.get('niche', 'Unknown')}

    INCOMING EMAIL:
    Subject: {reply.get('subject', '')}
    Message: {reply.get('body', '')}

    Classify the reply into exactly one category:

    - Interested
    - Not Interested
    - Asking Questions
    - Negotiating
    - Opt-Out
    - Other

    Return a JSON object with exactly these fields:

    {{
        "classification": "category",
        "summary": "short summary of the reply",
        "suggested_reply": "professional response draft",
        "stop_followups": true
    }}

    RULES:

    1. Classify using only the actual email content.
    2. Do not invent information or commitments.
    3. Keep the summary concise.
    4. Draft a polite, professional response.
    5. Never promise payment, products or deliverables.
    6. For questions, acknowledge them without inventing answers.
    7. For Not Interested, draft a polite acknowledgement.
    8. For Opt-Out, draft a confirmation respecting their request.
    9. For Opt-Out and Not Interested, stop_followups must be true.
    10. For all other categories, stop_followups must be false.
    11. Never send the response automatically.
    12. This is only a draft for human approval.

    Return valid JSON only.
    """

    result = generate_json(prompt)

    required_fields = [
        "classification",
        "summary",
        "suggested_reply",
        "stop_followups"
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(
                f"AI reply analysis is missing: {field}"
            )

    valid_categories = [
        "Interested",
        "Not Interested",
        "Asking Questions",
        "Negotiating",
        "Opt-Out",
        "Other"
    ]

    if result["classification"] not in valid_categories:
        raise ValueError("Invalid reply classification.")

    if not isinstance(result["stop_followups"], bool):
        raise ValueError("Invalid follow-up decision.")

    if not str(result["summary"]).strip():
        raise ValueError("AI returned an empty summary.")

    if not str(result["suggested_reply"]).strip():
        raise ValueError("AI returned an empty suggested reply.")

    expected_stop = result["classification"] in [
        "Opt-Out",
        "Not Interested"
    ]

    if result["stop_followups"] != expected_stop:
        raise ValueError("Inconsistent follow-up decision.")

    return result


def generate_followup_email(
    influencer,
    brand,
    followup_number,
    previous_email_subject,
    previous_email_body
):

    if followup_number not in [1, 2]:
        raise ValueError("Follow-up number must be 1 or 2.")

    if not previous_email_subject or not previous_email_body:
        raise ValueError("Original outreach email details are required.")

    prompt = f"""
    You are a professional influencer marketing communication assistant.

    Generate a personalized follow-up email for an influencer
    who has not responded to an earlier collaboration outreach email.

    INFLUENCER DETAILS:
    Name: {influencer.get('name', 'Unknown')}
    Username: {influencer.get('username', 'Unknown')}
    Niche: {influencer.get('niche', 'Unknown')}
    Location: {influencer.get('location', 'Unknown')}

    BRAND DETAILS:
    Name: {brand.get('name', 'Unknown')}
    Niche: {brand.get('niche', 'Unknown')}
    Campaign: {brand.get('campaign', 'Unknown')}

    ORIGINAL OUTREACH EMAIL:
    Subject: {previous_email_subject}
    Body: {previous_email_body}

    FOLLOW-UP NUMBER: {followup_number}

    EMAIL REQUIREMENTS:

    1. Address the influencer by their supplied name.
    2. Refer naturally to the earlier collaboration email.
    3. Keep the message short, friendly and professional.
    4. Remind them briefly about the brand and campaign.
    5. Do not repeat the entire original email.
    6. Include a simple call to action asking whether they are interested.
    7. Do not suggest that the influencer has already agreed.
    8. Do not invent achievements, audience statistics or partnerships.
    9. Do not create false urgency or pressure the recipient.
    10. Do not promise payment, products or deliverables.
    11. Do not invent sender details.
    12. Use [Your Name] and [Your Title] as sender placeholders.
    13. Respect the recipient's choice not to respond.
    14. Include a polite opt-out instruction.
    15. For follow-up 2, make this a final polite follow-up and
        clearly indicate that no further follow-up will be sent.

    Return a JSON object with exactly these fields:

    {{
        "subject": "Follow-up email subject",
        "body": "Complete follow-up email body"
    }}

    Return valid JSON only.
    """

    email = generate_json(prompt)

    if "subject" not in email or "body" not in email:
        raise ValueError("AI returned an incomplete follow-up draft.")

    subject = str(email["subject"]).strip()
    body = str(email["body"]).strip()

    if not subject or not body:
        raise ValueError("Generated follow-up subject or body is empty.")

    opt_out_sentence = (
        "If you would prefer not to receive further collaboration "
        "emails from us, simply reply with 'opt out' and we will "
        "respect your request."
    )

    opt_out_terms = [
        "opt out",
        "unsubscribe",
        "stop receiving"
    ]

    if not any(term in body.lower() for term in opt_out_terms):
        body = body.rstrip() + "\n\n" + opt_out_sentence

    return {
        "subject": subject,
        "body": body
    }
