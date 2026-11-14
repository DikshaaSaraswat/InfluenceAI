
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Literal

from app.database import (
    create_table,
    get_connection,
    save_incoming_reply,
    save_reply_analysis,
    get_reply_details,
    edit_reply_draft,
    schedule_followups,
    get_followups,
    update_due_followups,
    get_followup_details,
    save_followup_draft,
    edit_followup_draft,
    approve_followup,
    mark_followup_sending,
    mark_followup_sent,
    mark_followup_send_unconfirmed
)

from app.ai import (
    analyze_influencer,
    generate_outreach_email,
    classify_influencer_reply,
    generate_followup_email
)

from app.gmail_service import (
    send_email,
    get_incoming_replies,
    send_thread_reply
)


app = FastAPI(title="InfluenceAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

create_table()


class Influencer(BaseModel):
    name: str
    username: str
    profile_url: str | None = None
    niche: str
    followers: int
    location: str
    email: str | None = None


class Brand(BaseModel):
    name: str
    niche: str
    campaign: str


class StatusUpdate(BaseModel):
    status: Literal[
        "New Lead",
        "Email Available",
        "Email Sent",
        "Follow-up Due",
        "Replied",
        "Interested",
        "Not Interested",
        "Collaboration Confirmed"
    ]


class EmailUpdate(BaseModel):
    email: str | None


class ProfileURLUpdate(BaseModel):
    profile_url: str | None


class EmailDraftUpdate(BaseModel):
    subject: str
    body: str


class ReplyDraftUpdate(BaseModel):
    suggested_reply: str


class FollowupDraftUpdate(BaseModel):
    subject: str
    body: str


def validate_email_draft(influencer):

    if not influencer.get("email"):
        raise HTTPException(
            status_code=400,
            detail="Influencer business email is required"
        )

    if (
        not influencer.get("email_subject")
        or not influencer.get("email_draft")
    ):
        raise HTTPException(
            status_code=400,
            detail="Generate an email draft first"
        )

    body = influencer["email_draft"]

    if "[Your Name]" in body or "[Your Title]" in body:
        raise HTTPException(
            status_code=400,
            detail="Replace sender placeholders before approval or sending"
        )

    opt_out_terms = [
        "opt out",
        "unsubscribe",
        "stop receiving"
    ]

    if not any(term in body.lower() for term in opt_out_terms):
        raise HTTPException(
            status_code=400,
            detail="Email must include an opt-out instruction"
        )


@app.get("/")
def home():

    return {
        "message": "Welcome to InfluenceAI!",
        "status": "Backend is running"
    }


@app.post("/influencers")
def add_influencer(influencer: Influencer):

    try:
        profile_url = (
            influencer.profile_url.strip()
            if influencer.profile_url
            else None
        )

        if profile_url and not profile_url.startswith(
            "https://www.instagram.com/"
        ):
            raise HTTPException(
                status_code=400,
                detail="Please provide a valid Instagram profile URL"
            )

        with get_connection() as connection:

            cursor = connection.execute(
                """
                INSERT INTO influencers
                (name, username, profile_url, niche, followers, location, email)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    influencer.name,
                    influencer.username,
                    profile_url,
                    influencer.niche,
                    influencer.followers,
                    influencer.location,
                    influencer.email
                )
            )

        return {
            "message": "Influencer added successfully",
            "id": cursor.lastrowid,
            "influencer": {
                **influencer.model_dump(),
                "profile_url": profile_url
            }
        }

    except HTTPException:
        raise

    except Exception as e:

        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=409,
                detail="Influencer already exists"
            )

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/influencers")
def get_influencers(
    niche: str | None = None,
    location: str | None = None,
    min_followers: int | None = None,
    max_followers: int | None = None
):

    query = "SELECT * FROM influencers WHERE 1=1"
    params = []

    if niche:
        query += " AND LOWER(niche) LIKE LOWER(?)"
        params.append(f"%{niche}%")

    if location:
        query += " AND LOWER(location) = LOWER(?)"
        params.append(location)

    if min_followers is not None:
        query += " AND followers >= ?"
        params.append(min_followers)

    if max_followers is not None:
        query += " AND followers <= ?"
        params.append(max_followers)

    with get_connection() as connection:

        results = connection.execute(
            query, params
        ).fetchall()

    return [dict(row) for row in results]


@app.post("/influencers/{influencer_id}/analyze")
def analyze_influencer_profile(
    influencer_id: int,
    brand: Brand
):

    with get_connection() as connection:

        result = connection.execute(
            "SELECT * FROM influencers WHERE id = ?",
            (influencer_id,)
        ).fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Influencer not found"
        )

    try:
        analysis = analyze_influencer(
            dict(result),
            brand.model_dump()
        )

        with get_connection() as connection:

            connection.execute(
                """
                UPDATE influencers
                SET relevance_score = ?,
                    category = ?,
                    summary = ?,
                    reason = ?,
                    recommendation = ?,
                    analyzed_at = ?
                WHERE id = ?
                """,
                (
                    analysis["relevance_score"],
                    analysis["category"],
                    analysis["summary"],
                    analysis["reason"],
                    analysis["recommendation"],
                    datetime.now(timezone.utc).isoformat(),
                    influencer_id
                )
            )

        return {
            "message": "Influencer analyzed and saved successfully",
            "influencer_id": influencer_id,
            "analysis": analysis
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.patch("/influencers/{influencer_id}/status")
def update_influencer_status(
    influencer_id: int,
    status_update: StatusUpdate
):

    with get_connection() as connection:

        result = connection.execute(
            "SELECT id FROM influencers WHERE id = ?",
            (influencer_id,)
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Influencer not found"
            )

        connection.execute(
            """
            UPDATE influencers
            SET status = ?
            WHERE id = ?
            """,
            (status_update.status, influencer_id)
        )

    return {
        "message": "Influencer status updated successfully",
        "influencer_id": influencer_id,
        "new_status": status_update.status
    }


@app.patch("/influencers/{influencer_id}/email")
def update_influencer_email(
    influencer_id: int,
    email_update: EmailUpdate
):

    email = email_update.email

    if email is not None:

        email = email.strip()

        if (
            not email
            or "@" not in email
            or "." not in email.split("@")[-1]
        ):
            raise HTTPException(
                status_code=400,
                detail="Please provide a valid email address"
            )

    with get_connection() as connection:

        result = connection.execute(
            "SELECT * FROM influencers WHERE id = ?",
            (influencer_id,)
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Influencer not found"
            )

        if (
            result["status"] == "Email Sent"
            or result["gmail_message_id"]
        ):
            raise HTTPException(
                status_code=409,
                detail="Cannot change email after outreach has been sent"
            )

        connection.execute(
            """
            UPDATE influencers
            SET email = ?,
                status = ?,
                email_approved = 0,
                email_approved_at = NULL
            WHERE id = ?
            """,
            (
                email,
                "Email Available" if email else "New Lead",
                influencer_id
            )
        )

    return {
        "message": "Influencer email updated successfully",
        "influencer_id": influencer_id,
        "email": email,
        "status": "Email Available" if email else "New Lead",
        "approval_reset": True
    }


@app.patch("/influencers/{influencer_id}/profile-url")
def update_influencer_profile_url(
    influencer_id: int,
    profile_update: ProfileURLUpdate
):

    profile_url = profile_update.profile_url

    if profile_url is not None:

        profile_url = profile_url.strip()

        if (
            not profile_url
            or not profile_url.startswith(
                "https://www.instagram.com/"
            )
        ):
            raise HTTPException(
                status_code=400,
                detail="Please provide a valid Instagram profile URL"
            )

    with get_connection() as connection:

        result = connection.execute(
            "SELECT id FROM influencers WHERE id = ?",
            (influencer_id,)
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Influencer not found"
            )

        connection.execute(
            """
            UPDATE influencers
            SET profile_url = ?
            WHERE id = ?
            """,
            (profile_url, influencer_id)
        )

    return {
        "message": "Influencer profile URL updated successfully",
        "influencer_id": influencer_id,
        "profile_url": profile_url
    }


@app.post("/influencers/{influencer_id}/draft-email")
def create_email_draft(
    influencer_id: int,
    brand: Brand
):

    with get_connection() as connection:

        result = connection.execute(
            "SELECT * FROM influencers WHERE id = ?",
            (influencer_id,)
        ).fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Influencer not found"
        )

    try:
        email = generate_outreach_email(
            dict(result),
            brand.model_dump()
        )

        with get_connection() as connection:

            connection.execute(
                """
                UPDATE influencers
                SET email_subject = ?,
                    email_draft = ?,
                    draft_generated_at = ?,
                    email_approved = 0,
                    email_approved_at = NULL
                WHERE id = ?
                """,
                (
                    email["subject"],
                    email["body"],
                    datetime.now(timezone.utc).isoformat(),
                    influencer_id
                )
            )

        return {
            "message": "Email draft generated and saved successfully",
            "influencer_id": influencer_id,
            "email_subject": email["subject"],
            "email_draft": email["body"],
            "status": "Awaiting human review and approval"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/influencers/{influencer_id}/draft-email")
def get_email_draft(influencer_id: int):

    with get_connection() as connection:

        result = connection.execute(
            """
            SELECT id, name, username, email,
                   email_subject, email_draft,
                   draft_generated_at, email_approved,
                   email_approved_at
            FROM influencers
            WHERE id = ?
            """,
            (influencer_id,)
        ).fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Influencer not found"
        )

    if not result["email_draft"]:
        raise HTTPException(
            status_code=404,
            detail="No email draft found for this influencer"
        )

    return dict(result)


@app.patch("/influencers/{influencer_id}/draft-email")
def edit_email_draft(
    influencer_id: int,
    draft_update: EmailDraftUpdate
):

    subject = draft_update.subject.strip()
    body = draft_update.body.strip()

    if not subject or not body:
        raise HTTPException(
            status_code=400,
            detail="Email subject and body cannot be empty"
        )

    with get_connection() as connection:

        result = connection.execute(
            """
            SELECT id, status, gmail_message_id
            FROM influencers
            WHERE id = ?
            """,
            (influencer_id,)
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Influencer not found"
            )

        if (
            result["status"] == "Email Sent"
            or result["gmail_message_id"]
        ):
            raise HTTPException(
                status_code=409,
                detail="Cannot edit a draft after an email has been sent"
            )

        connection.execute(
            """
            UPDATE influencers
            SET email_subject = ?,
                email_draft = ?,
                email_approved = 0,
                email_approved_at = NULL
            WHERE id = ?
            """,
            (subject, body, influencer_id)
        )

    return {
        "message": "Email draft updated successfully",
        "influencer_id": influencer_id,
        "email_approved": False,
        "status": "Awaiting human approval"
    }


@app.patch("/influencers/{influencer_id}/approve-email")
def approve_email_draft(influencer_id: int):

    with get_connection() as connection:

        result = connection.execute(
            "SELECT * FROM influencers WHERE id = ?",
            (influencer_id,)
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Influencer not found"
            )

        influencer = dict(result)

        if influencer["email_approved"]:
            raise HTTPException(
                status_code=400,
                detail="Email draft is already approved"
            )

        validate_email_draft(influencer)

        approved_at = datetime.now(timezone.utc).isoformat()

        connection.execute(
            """
            UPDATE influencers
            SET email_approved = 1,
                email_approved_at = ?
            WHERE id = ?
            """,
            (approved_at, influencer_id)
        )

    return {
        "message": "Email draft approved successfully",
        "influencer_id": influencer_id,
        "email_approved": True,
        "approved_at": approved_at,
        "next_step": "Ready for Gmail sending"
    }


@app.post("/influencers/{influencer_id}/send-email")
def send_approved_email(influencer_id: int):

    with get_connection() as connection:

        result = connection.execute(
            "SELECT * FROM influencers WHERE id = ?",
            (influencer_id,)
        ).fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Influencer not found"
        )

    influencer = dict(result)

    if not influencer["email_approved"]:
        raise HTTPException(
            status_code=403,
            detail="Email requires human approval before sending"
        )

    if (
        influencer["status"] == "Email Sent"
        or influencer["gmail_message_id"]
    ):
        raise HTTPException(
            status_code=409,
            detail="This email has already been sent"
        )

    validate_email_draft(influencer)

    try:
        result = send_email(
            to_email=influencer["email"],
            subject=influencer["email_subject"],
            body=influencer["email_draft"]
        )

        sent_at = datetime.now(timezone.utc).isoformat()

        with get_connection() as connection:

            connection.execute(
                """
                UPDATE influencers
                SET status = 'Email Sent',
                    email_sent_at = ?,
                    gmail_message_id = ?,
                    gmail_thread_id = ?
                WHERE id = ?
                """,
                (
                    sent_at,
                    result["message_id"],
                    result["thread_id"],
                    influencer_id
                )
            )

        followup_schedule = None
        followup_schedule_error = None

        try:
            followup_schedule = schedule_followups(
                influencer_id=influencer_id,
                initial_sent_at=sent_at
            )
        except Exception as e:
            followup_schedule_error = str(e)

        return {
            "message": "Approved outreach email sent successfully",
            "influencer_id": influencer_id,
            "recipient": influencer["email"],
            "status": "Email Sent",
            "email_sent_at": sent_at,
            "gmail_message_id": result["message_id"],
            "gmail_thread_id": result["thread_id"],
            "followup_schedule": followup_schedule,
            "followup_schedule_error": followup_schedule_error
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=502,
            detail=f"Gmail sending failed: {str(e)}"
        )


@app.post("/replies/sync")
def sync_influencer_replies():

    with get_connection() as connection:

        influencers = connection.execute(
            """
            SELECT id, name, email,
                   gmail_message_id, gmail_thread_id
            FROM influencers
            WHERE email IS NOT NULL
              AND gmail_message_id IS NOT NULL
              AND gmail_thread_id IS NOT NULL
            """
        ).fetchall()

    results = []

    total_found = 0
    total_saved = 0

    for influencer in influencers:

        influencer = dict(influencer)

        try:
            replies = get_incoming_replies(
                thread_id=influencer["gmail_thread_id"],
                influencer_email=influencer["email"],
                original_message_id=influencer["gmail_message_id"]
            )

            influencer_saved = 0

            for reply in replies:

                save_result = save_incoming_reply(
                    influencer_id=influencer["id"],
                    reply=reply
                )

                total_found += 1

                if save_result["saved"]:
                    total_saved += 1
                    influencer_saved += 1

            results.append({
                "influencer_id": influencer["id"],
                "name": influencer["name"],
                "replies_found": len(replies),
                "new_replies_saved": influencer_saved,
                "status": "Success"
            })

        except Exception as e:

            results.append({
                "influencer_id": influencer["id"],
                "name": influencer["name"],
                "status": "Failed",
                "error": str(e)
            })

    return {
        "message": "Gmail reply synchronization completed",
        "influencers_checked": len(influencers),
        "replies_found": total_found,
        "new_replies_saved": total_saved,
        "results": results
    }


@app.post("/replies/{reply_id}/analyze")
def analyze_influencer_reply(reply_id: int):

    with get_connection() as connection:

        result = connection.execute(
            """
            SELECT
                r.*,
                i.name AS influencer_name,
                i.niche AS influencer_niche
            FROM influencer_replies r
            JOIN influencers i
                ON r.influencer_id = i.id
            WHERE r.id = ?
            """,
            (reply_id,)
        ).fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Incoming reply not found"
        )

    reply_data = dict(result)

    if reply_data["processed_at"]:
        raise HTTPException(
            status_code=409,
            detail="This reply has already been analyzed"
        )

    reply = {
        "subject": reply_data["subject"] or "",
        "body": reply_data["body"] or ""
    }

    influencer = {
        "name": reply_data["influencer_name"],
        "niche": reply_data["influencer_niche"]
    }

    try:
        analysis = classify_influencer_reply(
            reply,
            influencer
        )

        save_result = save_reply_analysis(
            reply_id=reply_id,
            analysis=analysis
        )

        return {
            "message": "AI reply analysis completed and saved successfully",
            "reply_id": reply_id,
            "influencer": influencer["name"],
            "analysis": analysis,
            "database": save_result,
            "next_step": "Human review and approval required before sending"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"AI reply analysis failed: {str(e)}"
        )


@app.get("/replies/{reply_id}")
def get_reply(reply_id: int):

    reply = get_reply_details(reply_id)

    if not reply:
        raise HTTPException(
            status_code=404,
            detail="Reply not found"
        )

    return {
        "message": "Reply details retrieved successfully",
        "reply": reply
    }


@app.patch("/replies/{reply_id}/draft")
def update_reply_draft(
    reply_id: int,
    draft_update: ReplyDraftUpdate
):

    suggested_reply = draft_update.suggested_reply.strip()

    if not suggested_reply:
        raise HTTPException(
            status_code=400,
            detail="Suggested reply cannot be empty"
        )

    try:
        result = edit_reply_draft(
            reply_id=reply_id,
            suggested_reply=suggested_reply
        )

        return {
            "message": "AI reply draft updated successfully",
            "reply_id": reply_id,
            "reply_approved": False,
            "status": "Awaiting human approval",
            "database": result
        }

    except ValueError as e:

        error_message = str(e)

        if error_message == "Reply not found.":
            status_code = 404

        elif "already been sent" in error_message:
            status_code = 409

        else:
            status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )


@app.patch("/replies/{reply_id}/approve")
def approve_reply_draft(reply_id: int):

    with get_connection() as connection:

        result = connection.execute(
            """
            SELECT *
            FROM influencer_replies
            WHERE id = ?
            """,
            (reply_id,)
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Reply not found"
            )

        reply = dict(result)

        if not reply["processed_at"]:
            raise HTTPException(
                status_code=400,
                detail="Analyze the reply before approving its draft"
            )

        if reply["reply_sent_at"]:
            raise HTTPException(
                status_code=409,
                detail="This reply has already been sent"
            )

        if reply["reply_approved"]:
            raise HTTPException(
                status_code=409,
                detail="Reply draft is already approved"
            )

        if not reply["suggested_reply"] or not reply["suggested_reply"].strip():
            raise HTTPException(
                status_code=400,
                detail="No reply draft available for approval"
            )

        approved_at = datetime.now(timezone.utc).isoformat()

        connection.execute(
            """
            UPDATE influencer_replies
            SET reply_approved = 1,
                reply_approved_at = ?,
                reply_status = 'Approved'
            WHERE id = ?
            """,
            (approved_at, reply_id)
        )

    return {
        "message": "AI reply draft approved successfully",
        "reply_id": reply_id,
        "reply_approved": True,
        "approved_at": approved_at,
        "status": "Approved",
        "next_step": "Ready for human-authorized Gmail sending"
    }


@app.post("/replies/{reply_id}/send")
def send_approved_reply(reply_id: int):

    with get_connection() as connection:

        result = connection.execute(
            """
            SELECT
                r.*,
                i.name AS influencer_name,
                i.email AS influencer_email
            FROM influencer_replies r
            JOIN influencers i
                ON r.influencer_id = i.id
            WHERE r.id = ?
            """,
            (reply_id,)
        ).fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Reply not found"
        )

    reply = dict(result)

    if not reply["processed_at"]:
        raise HTTPException(
            status_code=400,
            detail="Analyze the reply before sending"
        )

    if not reply["reply_approved"]:
        raise HTTPException(
            status_code=403,
            detail="Human approval is required before sending"
        )

    if reply["reply_sent_at"]:
        raise HTTPException(
            status_code=409,
            detail="This reply has already been sent"
        )

    if reply["reply_status"] != "Approved":
        raise HTTPException(
            status_code=409,
            detail=f"Reply cannot be sent from status: {reply['reply_status']}"
        )

    if not reply["suggested_reply"] or not reply["suggested_reply"].strip():
        raise HTTPException(
            status_code=400,
            detail="No approved reply draft available"
        )

    if not reply["gmail_thread_id"] or not reply["gmail_message_id"]:
        raise HTTPException(
            status_code=400,
            detail="Gmail thread or incoming message ID is missing"
        )

    if not reply["influencer_email"]:
        raise HTTPException(
            status_code=400,
            detail="Influencer email is missing"
        )

    if (
        reply["sender_email"].strip().lower()
        != reply["influencer_email"].strip().lower()
    ):
        raise HTTPException(
            status_code=400,
            detail="Incoming reply sender does not match influencer email"
        )

    with get_connection() as connection:

        reservation = connection.execute(
            """
            UPDATE influencer_replies
            SET reply_status = 'Sending'
            WHERE id = ?
              AND reply_status = 'Approved'
              AND reply_approved = 1
              AND reply_sent_at IS NULL
            """,
            (reply_id,)
        )

        if reservation.rowcount != 1:
            raise HTTPException(
                status_code=409,
                detail="Reply is already being processed or is no longer approved"
            )

    try:

        gmail_result = send_thread_reply(
            thread_id=reply["gmail_thread_id"],
            to_email=reply["influencer_email"],
            subject=reply["subject"] or "Re:",
            body=reply["suggested_reply"],
            reply_to_message_id=reply["gmail_message_id"]
        )

        sent_at = datetime.now(timezone.utc).isoformat()

        classification = reply["classification"]

        if classification == "Interested":
            influencer_status = "Interested"

        elif classification in ["Not Interested", "Opt-Out"]:
            influencer_status = "Not Interested"

        else:
            influencer_status = "Replied"

        with get_connection() as connection:

            update_result = connection.execute(
                """
                UPDATE influencer_replies
                SET reply_status = 'Sent',
                    reply_sent_at = ?,
                    gmail_reply_message_id = ?
                WHERE id = ?
                  AND reply_status = 'Sending'
                """,
                (
                    sent_at,
                    gmail_result["message_id"],
                    reply_id
                )
            )

            if update_result.rowcount != 1:
                raise RuntimeError(
                    "Gmail accepted the reply, but the database status could not be confirmed. "
                    "Check the Gmail thread before taking further action."
                )

            connection.execute(
                """
                UPDATE influencers
                SET status = ?,
                    followups_stopped = 1
                WHERE id = ?
                """,
                (
                    influencer_status,
                    reply["influencer_id"]
                )
            )

        return {
            "message": "Approved Gmail reply sent successfully",
            "reply_id": reply_id,
            "influencer": reply["influencer_name"],
            "recipient": reply["influencer_email"],
            "classification": classification,
            "status": "Sent",
            "influencer_status": influencer_status,
            "followups_stopped": True,
            "sent_at": sent_at,
            "gmail_message_id": gmail_result["message_id"],
            "gmail_thread_id": gmail_result["thread_id"]
        }

    except Exception as e:

        try:
            with get_connection() as connection:

                connection.execute(
                    """
                    UPDATE influencer_replies
                    SET reply_status = 'Send Unconfirmed'
                    WHERE id = ?
                      AND reply_status = 'Sending'
                    """,
                    (reply_id,)
                )

        except Exception:
            pass

        raise HTTPException(
            status_code=502,
            detail=(
                "Gmail sending could not be confirmed. "
                "Check the Gmail thread before attempting another send. "
                f"Details: {str(e)}"
            )
        )


@app.get("/followups")
def list_followups(influencer_id: int | None = None):

    try:
        followups = get_followups(influencer_id)

        return {
            "message": "Follow-ups retrieved successfully",
            "total": len(followups),
            "followups": followups
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve follow-ups: {str(e)}"
        )


@app.post("/followups/update-due")
def refresh_due_followups():

    try:
        due_count = update_due_followups()

        return {
            "message": "Follow-up statuses updated successfully",
            "due_followups": due_count
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not update follow-ups: {str(e)}"
        )


@app.get("/followups/{followup_id}")
def get_followup(followup_id: int):

    followup = get_followup_details(followup_id)

    if not followup:
        raise HTTPException(
            status_code=404,
            detail="Follow-up not found"
        )

    return {
        "message": "Follow-up details retrieved successfully",
        "followup": followup
    }


@app.post("/followups/{followup_id}/generate")
def generate_followup_draft(
    followup_id: int,
    brand: Brand
):

    try:
        update_due_followups()

        followup = get_followup_details(followup_id)

        if not followup:
            raise HTTPException(
                status_code=404,
                detail="Follow-up not found"
            )

        if followup["followups_stopped"]:
            raise HTTPException(
                status_code=409,
                detail="Follow-ups have been stopped for this influencer"
            )

        if followup["status"] not in ["Due", "Drafted"]:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot generate a draft for follow-up status: {followup['status']}"
            )

        if not followup["influencer_email"]:
            raise HTTPException(
                status_code=400,
                detail="Influencer business email is missing"
            )

        if not followup["email_sent_at"]:
            raise HTTPException(
                status_code=400,
                detail="Original outreach email has not been sent"
            )

        if not followup["original_email_subject"] or not followup["original_email_body"]:
            raise HTTPException(
                status_code=400,
                detail="Original outreach email details are missing"
            )

        if followup["sequence_no"] not in [1, 2]:
            raise HTTPException(
                status_code=400,
                detail="Unsupported follow-up sequence number"
            )

        generated_email = generate_followup_email(
            influencer={
                "name": followup["influencer_name"],
                "username": followup["influencer_username"],
                "niche": followup["influencer_niche"],
                "followers": followup["influencer_followers"],
                "location": followup["influencer_location"],
                "email": followup["influencer_email"]
            },
            brand=brand.model_dump(),
            followup_number=followup["sequence_no"],
            previous_email_subject=followup["original_email_subject"],
            previous_email_body=followup["original_email_body"]
        )

        save_result = save_followup_draft(
            followup_id=followup_id,
            subject=generated_email["subject"],
            body=generated_email["body"]
        )

        return {
            "message": "AI follow-up draft generated successfully",
            "followup_id": followup_id,
            "sequence_no": followup["sequence_no"],
            "subject": generated_email["subject"],
            "body": generated_email["body"],
            "status": "Drafted",
            "human_approval_required": True,
            "database": save_result
        }

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Follow-up generation failed: {str(e)}"
        )


@app.patch("/followups/{followup_id}/draft")
def update_followup_draft(
    followup_id: int,
    draft_update: FollowupDraftUpdate
):

    subject = draft_update.subject.strip()
    body = draft_update.body.strip()

    if not subject or not body:
        raise HTTPException(
            status_code=400,
            detail="Follow-up subject and body cannot be empty"
        )

    try:
        result = edit_followup_draft(
            followup_id=followup_id,
            subject=subject,
            body=body
        )

        return {
            "message": "Follow-up draft updated successfully",
            "followup_id": followup_id,
            "status": "Drafted",
            "approved": False,
            "human_approval_required": True,
            "database": result
        }

    except ValueError as e:

        error_message = str(e)

        if "not found" in error_message.lower():
            status_code = 404

        elif "stopped" in error_message.lower():
            status_code = 409

        else:
            status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not update follow-up draft: {str(e)}"
        )


@app.patch("/followups/{followup_id}/approve")
def approve_followup_draft(followup_id: int):

    try:
        result = approve_followup(followup_id)

        return {
            "message": "Follow-up draft approved successfully",
            "followup_id": followup_id,
            "status": "Approved",
            "human_approved": True,
            "next_step": "Ready for Gmail sending",
            "database": result
        }

    except ValueError as e:

        error_message = str(e)

        if "not found" in error_message.lower():
            status_code = 404

        elif "stopped" in error_message.lower():
            status_code = 409

        else:
            status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not approve follow-up: {str(e)}"
        )


@app.post("/followups/{followup_id}/send")
def send_approved_followup(followup_id: int):

    followup = get_followup_details(followup_id)

    if not followup:
        raise HTTPException(
            status_code=404,
            detail="Follow-up not found"
        )

    if followup["followups_stopped"]:
        raise HTTPException(
            status_code=409,
            detail="Follow-ups have been stopped for this influencer"
        )

    if followup["status"] != "Approved" or not followup["approved"]:
        raise HTTPException(
            status_code=403,
            detail="Human approval is required before sending this follow-up"
        )

    if not followup["subject"] or not followup["body"]:
        raise HTTPException(
            status_code=400,
            detail="Approved follow-up subject or body is missing"
        )

    if not followup["influencer_email"]:
        raise HTTPException(
            status_code=400,
            detail="Influencer email is missing"
        )

    if not followup["gmail_thread_id"] or not followup["original_gmail_message_id"]:
        raise HTTPException(
            status_code=400,
            detail="Original Gmail thread or message ID is missing"
        )

    try:
        reserved = mark_followup_sending(followup_id)

        if not reserved:
            raise HTTPException(
                status_code=409,
                detail="Follow-up is already being processed or is no longer approved"
            )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not reserve follow-up for sending: {str(e)}"
        )

    try:
        gmail_result = send_thread_reply(
            thread_id=followup["gmail_thread_id"],
            to_email=followup["influencer_email"],
            subject=followup["subject"],
            body=followup["body"],
            reply_to_message_id=followup["original_gmail_message_id"]
        )

        sent_at = datetime.now(timezone.utc).isoformat()

        updated = mark_followup_sent(
            followup_id=followup_id,
            gmail_message_id=gmail_result["message_id"]
        )

        if not updated:
            raise RuntimeError(
                "Gmail accepted the email, but the database could not confirm its sent status. Check the Gmail thread before retrying."
            )

        return {
            "message": "Approved follow-up email sent successfully",
            "followup_id": followup_id,
            "influencer": followup["influencer_name"],
            "recipient": followup["influencer_email"],
            "sequence_no": followup["sequence_no"],
            "status": "Sent",
            "sent_at": sent_at,
            "gmail_message_id": gmail_result["message_id"],
            "gmail_thread_id": gmail_result["thread_id"]
        }

    except Exception as e:

        try:
            mark_followup_send_unconfirmed(followup_id)
        except Exception:
            pass

        raise HTTPException(
            status_code=502,
            detail=(
                "Gmail sending could not be confirmed. "
                "Check the Gmail thread before attempting another send. "
                f"Details: {str(e)}"
            )
        )
