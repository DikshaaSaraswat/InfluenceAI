# InfluenceAI — AI-Powered Influencer Outreach CRM

InfluenceAI is an AI-powered influencer research and email outreach management system designed to simplify influencer collaboration workflows. It combines AI-based influencer analysis, personalized email generation, Gmail integration, and reply management in one dashboard.

## Features

### 1. Influencer Management
- Add and manage influencer profiles.
- Store usernames, niches, locations, follower counts, email addresses, and profile URLs.
- Prevent duplicate Instagram usernames using case-insensitive validation.
- Track influencer outreach statuses through the CRM.

### 2. AI-Powered Influencer Analysis
- Analyze influencer profiles using Google Gemini.
- Generate relevance and suitability scores.
- Categorize influencers based on their niche.
- Identify priority levels and generate analysis summaries.

### 3. Personalized Email Outreach
- Generate personalized outreach emails using AI.
- Edit and save email drafts.
- Require human approval before sending.
- Send approved emails through the Gmail API.
- Include opt-out instructions in outreach emails.

### 4. Follow-up Management
- Schedule the first follow-up four days after the initial outreach.
- Schedule the second follow-up six days after the first follow-up.
- Update follow-up statuses based on their scheduled dates.
- Stop or cancel pending follow-ups when an influencer replies, declines, or opts out.
- Require human review and approval before sending follow-up emails.

### 5. Gmail Reply Management
- Synchronize incoming replies using the Gmail API.
- Store incoming replies in the database.
- Classify replies using AI into categories such as Interested, Not Interested, Asking Questions, Negotiating, Opt-Out, and Other.
- Generate suggested responses.
- Save and edit reply drafts.
- Require human approval before sending replies.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript |
| Frontend Framework | TanStack Start |
| Development Server | Vite |
| Backend | Python, FastAPI |
| Database | SQLite |
| AI Integration | Google Gemini API (Gemini 2.5 Flash Lite) |
| Email Integration | Gmail API |
| Authentication | Google OAuth 2.0 |
| API Documentation | OpenAPI / Swagger UI |

## Project Structure

```text
InfluenceAI/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── ai.py
│   │   ├── database.py
│   │   └── gmail_service.py
│   ├── test_*.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── routes/
│   │   ├── lib/
│   │   └── hooks/
│   ├── public/
│   └── package.json
│
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10 or later
- Node.js and npm
- Google Gemini API key
- Google Cloud project with Gmail API enabled
- Gmail OAuth 2.0 credentials

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd InfluenceAI
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
python -m venv venv
```

Activate the virtual environment on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file inside the backend directory:

```env
GEMINI_API_KEY=your_gemini_api_key
```

#### Configure Gmail OAuth

1. Enable the Gmail API in Google Cloud Console.
2. Create OAuth 2.0 credentials for a Desktop application.
3. Place the downloaded credentials file at `backend/credentials/client_secret.json`.
4. Run the application and complete Google OAuth authorization when prompted.
5. The generated `token.json` stores the authorization token for subsequent use.

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend URL:

`http://127.0.0.1:8000`

Swagger API documentation:

`http://127.0.0.1:8000/docs`

### 3. Frontend Setup

Open another terminal and navigate to the frontend directory:

```bash
cd frontend
npm install
```

Create the frontend environment file from the example:

```powershell
Copy-Item .env.example .env
```

Configure the frontend `.env` file:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

Open the application at:

`http://localhost:8080`

## Application Workflow

```text
Influencer Research
        |
        v
Add Influencer to CRM
        |
        v
AI Profile Analysis
        |
        v
Generate Personalized Email
        |
        v
Human Review and Approval
        |
        v
Send Email through Gmail
        |
        v
Schedule Follow-ups
        |
        v
Review and Send Follow-ups
        |
        v
Synchronize Incoming Replies
        |
        v
AI Reply Classification
        |
        v
Generate Suggested Response
        |
        v
Human Review and Approval
        |
        v
Send Reply through Gmail
```

## Testing and Verification

The following workflows were tested during development:

| Test | Result |
|---|---|
| Backend startup and API access | Passed |
| Frontend production build | Passed |
| Influencer creation and retrieval | Verified |
| Duplicate username prevention | Implemented |
| AI influencer analysis | Verified |
| AI email draft generation | Verified |
| Email draft saving | Verified |
| Email approval workflow | Implemented |
| Gmail OAuth connection | Passed |
| Gmail email sending | Passed |
| Gmail reply synchronization | Passed |
| AI reply classification | Passed |
| Reply draft saving | Passed |
| Reply approval workflow | Passed |
| Approved reply sending | Passed |
| Reply status database update | Passed |
| Follow-up scheduling logic | Implemented |
| Follow-up cancellation logic | Implemented |

### Gmail Integration Test

A test email was sent through the Gmail API, and a reply was received in the same Gmail thread.

InfluenceAI successfully:

- Retrieved the incoming reply.
- Stored it in SQLite.
- Classified it as **Interested** using Gemini.
- Generated a suggested response.
- Saved the draft and recorded human approval.
- Sent the approved response through Gmail.

The final database record confirmed:

- Reply status: `Sent`
- Reply approved: `1`
- Reply sent timestamp: Recorded
- Gmail reply message ID: Recorded

## Design Decisions and Limitations

- **Instagram Research:** Influencer discovery and public profile research are performed manually. Profiles are entered into the CRM. The current implementation does not perform automated Instagram scraping or automated Instagram search.
- **Database:** SQLite is used as the CRM storage layer instead of Google Sheets.
- **AI Provider:** Google Gemini 2.5 Flash Lite is used for influencer analysis, email generation, reply classification, and suggested response generation.
- **Human-in-the-loop:** Emails and replies are not automatically sent after generation. Explicit human approval is required before sending.
- **Email Integration:** Gmail API is used with Google OAuth 2.0 authorization.
- **Follow-up Execution:** Follow-ups are scheduled and their statuses are updated through the application. Draft generation, approval, and sending are handled manually. Background scheduling and automatic email sending are not implemented.

## Security Notes

Never commit the following files or secrets to a public repository:

- Backend `.env`
- Frontend `.env`
- `token.json`
- `credentials/client_secret.json`
- SQLite database files containing personal or test data

Use environment variables and OAuth credentials locally. Sensitive files should remain excluded through `.gitignore`.

## Future Improvements

- Automated influencer discovery through authorized data providers.
- Google Sheets integration.
- Advanced influencer engagement and audience analysis.
- Email campaign analytics and reporting.
- Background follow-up scheduling and monitoring.
- More advanced AI-based campaign recommendations.

---

**InfluenceAI** — Making influencer outreach smarter with AI and automation.
