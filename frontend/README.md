# InfluenceAI Outreach CRM

Build a simple, clean and functional frontend for **InfluenceAI**, an AI-powered Instagram Influencer Research and Email Outreach CRM.

IMPORTANT:
- Build ONLY the frontend.
- Use React, TypeScript, Tailwind CSS and basic reusable components.
- Do not create a new backend, database, authentication system or AI logic.
- Keep the design minimal and lightweight to reduce generation complexity.
- Do not generate unnecessary animations, complex charts or decorative sections.
- Use the existing FastAPI backend through API calls.

**Design:**
- White/light background.
- Dark navy text with subtle purple accents.
- Simple sidebar navigation.
- Clean tables, cards, buttons and forms.
- Responsive layout.
- Professional but simple dashboard.

**Pages required:**

1. Dashboard
- Total influencers
- New leads
- Emails sent
- Follow-ups due
- Recent influencer activity

2. Influencers
- Display influencers in a table.
- Add influencer form.
- Search and filter by niche, location and followers.
- Show name, Instagram username, niche, followers, email and status.
- View influencer details.

3. AI Analysis
- Select an influencer.
- Enter brand name, niche and campaign description.
- Call POST `/influencers/{id}/analyze`.
- Display relevance score, category, summary, reason and recommendation.

4. Email Outreach
- Generate personalized email drafts.
- Allow editing subject and body.
- Add Approve and Send buttons.
- Connect to the existing email draft, approval and send APIs.
- Never send automatically.

5. Follow-ups
- Display scheduled follow-ups.
- Show influencer, sequence number, scheduled date and status.
- Allow generating, editing, approving and sending follow-up drafts.

6. Reply Management
- Display incoming replies.
- Show AI classification and suggested response.
- Allow editing, approving and sending replies.

**API integration:**
Create one centralized API utility file.
Use `VITE_API_BASE_URL` as the backend URL (defaulting to `http://127.0.0.1:8000`). Copy `.env.example` to `.env.local` for local development and restart the frontend after changing it.
Use these existing backend endpoints:

- GET `/influencers`
- POST `/influencers`
- POST `/influencers/{id}/analyze`
- PATCH `/influencers/{id}/status`
- PATCH `/influencers/{id}/email`
- PATCH `/influencers/{id}/profile-url`
- POST `/influencers/{id}/draft-email`
- GET `/influencers/{id}/draft-email`
- PATCH `/influencers/{id}/draft-email`
- PATCH `/influencers/{id}/approve-email`
- POST `/influencers/{id}/send-email`
- GET `/followups`
- POST `/followups/update-due`
- GET `/followups/{id}`
- POST `/followups/{id}/generate`
- PATCH `/followups/{id}/draft`
- PATCH `/followups/{id}/approve`
- POST `/followups/{id}/send`
- POST `/replies/sync`
- POST `/replies/{id}/analyze`
- GET `/replies/{id}`
- PATCH `/replies/{id}/draft`
- PATCH `/replies/{id}/approve`
- POST `/replies/{id}/send`

Important:
- Follow the actual API response structures.
- Do not invent endpoints.
- Do not use fake AI results or pretend Instagram discovery exists.
- Display loading states and API errors.
- If an API is unavailable, show a clear message instead of fake data.

Keep the code organized and easy to modify. Prioritize a working basic interface over visual complexity.
Start with the shared layout and the six specified pages wired to the FastAPI backend.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/688511a3-17f2-4724-b2bc-6e4206088202).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
