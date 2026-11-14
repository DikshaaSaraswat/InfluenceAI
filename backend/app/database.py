import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta


DB_PATH = Path(__file__).resolve().parent.parent / "influenceai.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_table():
    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS influencers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                profile_url TEXT,
                niche TEXT NOT NULL,
                followers INTEGER NOT NULL,
                location TEXT NOT NULL,
                email TEXT,
                relevance_score REAL,
                category TEXT,
                summary TEXT,
                reason TEXT,
                recommendation TEXT,
                status TEXT NOT NULL DEFAULT 'New Lead',
                analyzed_at TEXT,
                email_subject TEXT,
                email_draft TEXT,
                draft_generated_at TEXT,
                email_approved INTEGER NOT NULL DEFAULT 0,
                email_approved_at TEXT,
                email_sent_at TEXT,
                gmail_message_id TEXT,
                gmail_thread_id TEXT,
                followups_stopped INTEGER NOT NULL DEFAULT 0
            )
        """)

        existing_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(influencers)"
            ).fetchall()
        }

        new_columns = {
            "profile_url": "TEXT",
            "relevance_score": "REAL",
            "category": "TEXT",
            "summary": "TEXT",
            "reason": "TEXT",
            "recommendation": "TEXT",
            "status": "TEXT NOT NULL DEFAULT 'New Lead'",
            "analyzed_at": "TEXT",
            "email_subject": "TEXT",
            "email_draft": "TEXT",
            "draft_generated_at": "TEXT",
            "email_approved": "INTEGER NOT NULL DEFAULT 0",
            "email_approved_at": "TEXT",
            "email_sent_at": "TEXT",
            "gmail_message_id": "TEXT",
            "gmail_thread_id": "TEXT",
            "followups_stopped": "INTEGER NOT NULL DEFAULT 0"
        }

        for column, data_type in new_columns.items():
            if column not in existing_columns:
                connection.execute(
                    f"ALTER TABLE influencers ADD COLUMN {column} {data_type}"
                )

        connection.execute("""
            CREATE TABLE IF NOT EXISTS influencer_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                influencer_id INTEGER NOT NULL,
                gmail_message_id TEXT NOT NULL UNIQUE,
                gmail_thread_id TEXT NOT NULL,
                sender_email TEXT NOT NULL,
                subject TEXT,
                body TEXT,
                received_at TEXT,
                classification TEXT,
                summary TEXT,
                suggested_reply TEXT,
                reply_status TEXT NOT NULL DEFAULT 'New Reply',
                processed_at TEXT,
                reply_approved INTEGER NOT NULL DEFAULT 0,
                reply_approved_at TEXT,
                reply_sent_at TEXT,
                gmail_reply_message_id TEXT,
                stop_followups INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (influencer_id)
                    REFERENCES influencers(id)
                    ON DELETE CASCADE
            )
        """)

        existing_reply_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(influencer_replies)"
            ).fetchall()
        }

        if "stop_followups" not in existing_reply_columns:
            connection.execute("""
                ALTER TABLE influencer_replies
                ADD COLUMN stop_followups INTEGER NOT NULL DEFAULT 0
            """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS influencer_followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                influencer_id INTEGER NOT NULL,
                sequence_no INTEGER NOT NULL,
                scheduled_at TEXT NOT NULL,
                subject TEXT,
                body TEXT,
                status TEXT NOT NULL DEFAULT 'Scheduled',
                approved INTEGER NOT NULL DEFAULT 0,
                approved_at TEXT,
                sent_at TEXT,
                gmail_message_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(influencer_id, sequence_no),
                FOREIGN KEY (influencer_id)
                    REFERENCES influencers(id)
                    ON DELETE CASCADE
            )
        """)


def save_incoming_reply(influencer_id, reply):
    required_fields = [
        "message_id",
        "thread_id",
        "from",
        "subject",
        "body",
        "date"
    ]

    for field in required_fields:
        if not reply.get(field):
            raise ValueError(f"Incoming reply is missing: {field}")

    with get_connection() as connection:
        influencer = connection.execute(
            "SELECT id FROM influencers WHERE id = ?",
            (influencer_id,)
        ).fetchone()

        if not influencer:
            raise ValueError("Influencer not found.")

        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO influencer_replies (
                influencer_id,
                gmail_message_id,
                gmail_thread_id,
                sender_email,
                subject,
                body,
                received_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                influencer_id,
                reply["message_id"],
                reply["thread_id"],
                reply["from"],
                reply["subject"],
                reply["body"],
                reply["date"]
            )
        )

        if cursor.rowcount == 0:
            return {
                "saved": False,
                "message": "Reply already exists",
                "influencer_id": influencer_id
            }

        connection.execute(
            """
            UPDATE influencers
            SET status = 'Replied',
                followups_stopped = 1
            WHERE id = ?
            """,
            (influencer_id,)
        )

        connection.execute(
            """
            UPDATE influencer_followups
            SET status = 'Cancelled'
            WHERE influencer_id = ?
              AND status IN (
                  'Scheduled',
                  'Due',
                  'Drafted',
                  'Approved'
              )
            """,
            (influencer_id,)
        )

        return {
            "saved": True,
            "reply_id": cursor.lastrowid,
            "influencer_id": influencer_id,
            "status": "Replied",
            "followups_stopped": True
        }


def save_reply_analysis(reply_id, analysis):
    required_fields = [
        "classification",
        "summary",
        "suggested_reply",
        "stop_followups"
    ]

    for field in required_fields:
        if field not in analysis:
            raise ValueError(f"Reply analysis is missing: {field}")

    valid_categories = [
        "Interested",
        "Not Interested",
        "Asking Questions",
        "Negotiating",
        "Opt-Out",
        "Other"
    ]

    if analysis["classification"] not in valid_categories:
        raise ValueError("Invalid reply classification.")

    if not isinstance(analysis["stop_followups"], bool):
        raise ValueError("Invalid follow-up decision.")

    if not str(analysis["summary"]).strip():
        raise ValueError("Reply summary cannot be empty.")

    if not str(analysis["suggested_reply"]).strip():
        raise ValueError("Suggested reply cannot be empty.")

    expected_stop = analysis["classification"] in [
        "Not Interested",
        "Opt-Out"
    ]

    if analysis["stop_followups"] != expected_stop:
        raise ValueError("Inconsistent follow-up decision.")

    with get_connection() as connection:
        reply = connection.execute(
            """
            SELECT influencer_id
            FROM influencer_replies
            WHERE id = ?
            """,
            (reply_id,)
        ).fetchone()

        if not reply:
            raise ValueError("Reply not found.")

        connection.execute(
            """
            UPDATE influencer_replies
            SET classification = ?,
                summary = ?,
                suggested_reply = ?,
                stop_followups = ?,
                processed_at = CURRENT_TIMESTAMP,
                reply_status = 'Analyzed'
            WHERE id = ?
            """,
            (
                analysis["classification"],
                analysis["summary"],
                analysis["suggested_reply"],
                int(analysis["stop_followups"]),
                reply_id
            )
        )

        if analysis["stop_followups"]:
            connection.execute(
                """
                UPDATE influencers
                SET followups_stopped = 1,
                    status = 'Not Interested'
                WHERE id = ?
                """,
                (reply["influencer_id"],)
            )

            connection.execute(
                """
                UPDATE influencer_followups
                SET status = 'Cancelled'
                WHERE influencer_id = ?
                  AND status IN (
                      'Scheduled',
                      'Due',
                      'Drafted',
                      'Approved'
                  )
                """,
                (reply["influencer_id"],)
            )

        return {
            "saved": True,
            "reply_id": reply_id,
            "classification": analysis["classification"],
            "stop_followups": analysis["stop_followups"],
            "message": "Reply analysis saved successfully"
        }


def get_reply_details(reply_id):
    with get_connection() as connection:
        reply = connection.execute(
            """
            SELECT
                r.*,
                i.name AS influencer_name,
                i.username AS influencer_username,
                i.niche AS influencer_niche
            FROM influencer_replies r
            JOIN influencers i
                ON r.influencer_id = i.id
            WHERE r.id = ?
            """,
            (reply_id,)
        ).fetchone()

        if not reply:
            return None

        return dict(reply)


def edit_reply_draft(reply_id, suggested_reply):
    suggested_reply = suggested_reply.strip()

    if not suggested_reply:
        raise ValueError("Suggested reply cannot be empty.")

    with get_connection() as connection:
        reply = connection.execute(
            """
            SELECT id, processed_at, reply_sent_at
            FROM influencer_replies
            WHERE id = ?
            """,
            (reply_id,)
        ).fetchone()

        if not reply:
            raise ValueError("Reply not found.")

        if not reply["processed_at"]:
            raise ValueError(
                "Analyze the reply before editing its draft."
            )

        if reply["reply_sent_at"]:
            raise ValueError(
                "Cannot edit a reply that has already been sent."
            )

        connection.execute(
            """
            UPDATE influencer_replies
            SET suggested_reply = ?,
                reply_approved = 0,
                reply_approved_at = NULL,
                reply_status = 'Analyzed'
            WHERE id = ?
            """,
            (suggested_reply, reply_id)
        )

        return {
            "updated": True,
            "reply_id": reply_id,
            "reply_approved": False,
            "message": "Suggested reply updated successfully"
        }


def schedule_followups(influencer_id, initial_sent_at):
    initial_time = datetime.fromisoformat(
        initial_sent_at.replace("Z", "+00:00")
    )

    first_followup = initial_time + timedelta(days=4)
    second_followup = first_followup + timedelta(days=6)

    with get_connection() as connection:
        influencer = connection.execute(
            """
            SELECT id, followups_stopped
            FROM influencers
            WHERE id = ?
            """,
            (influencer_id,)
        ).fetchone()

        if not influencer:
            raise ValueError("Influencer not found.")

        if influencer["followups_stopped"]:
            return {
                "scheduled": False,
                "message": "Follow-ups are stopped for this influencer"
            }

        connection.execute(
            """
            INSERT OR IGNORE INTO influencer_followups
            (influencer_id, sequence_no, scheduled_at)
            VALUES (?, ?, ?)
            """,
            (
                influencer_id,
                1,
                first_followup.isoformat()
            )
        )

        connection.execute(
            """
            INSERT OR IGNORE INTO influencer_followups
            (influencer_id, sequence_no, scheduled_at)
            VALUES (?, ?, ?)
            """,
            (
                influencer_id,
                2,
                second_followup.isoformat()
            )
        )

    return {
        "scheduled": True,
        "influencer_id": influencer_id,
        "first_followup": first_followup.isoformat(),
        "second_followup": second_followup.isoformat()
    }


def get_followups(influencer_id=None):
    query = """
        SELECT
            f.*,
            i.name AS influencer_name,
            i.email AS influencer_email
        FROM influencer_followups f
        JOIN influencers i
            ON f.influencer_id = i.id
    """

    params = []

    if influencer_id is not None:
        query += " WHERE f.influencer_id = ?"
        params.append(influencer_id)

    query += " ORDER BY f.scheduled_at ASC"

    with get_connection() as connection:
        results = connection.execute(
            query,
            params
        ).fetchall()

    return [dict(row) for row in results]


def update_due_followups():
    current_time = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE influencer_followups
            SET status = 'Due'
            WHERE status = 'Scheduled'
              AND scheduled_at <= ?
              AND influencer_id IN (
                  SELECT id
                  FROM influencers
                  WHERE followups_stopped = 0
              )
            """,
            (current_time,)
        )

        connection.execute(
            """
            UPDATE influencer_followups
            SET status = 'Cancelled'
            WHERE status IN (
                'Scheduled',
                'Due',
                'Drafted',
                'Approved'
            )
              AND influencer_id IN (
                  SELECT id
                  FROM influencers
                  WHERE followups_stopped = 1
              )
            """
        )

        return connection.execute(
            """
            SELECT COUNT(*) AS due_count
            FROM influencer_followups
            WHERE status = 'Due'
            """
        ).fetchone()["due_count"]


def get_followup_details(followup_id):
    with get_connection() as connection:
        followup = connection.execute(
            """
            SELECT
                f.*,
                i.name AS influencer_name,
                i.username AS influencer_username,
                i.niche AS influencer_niche,
                i.followers AS influencer_followers,
                i.location AS influencer_location,
                i.email AS influencer_email,
                i.email_subject AS original_email_subject,
                i.email_draft AS original_email_body,
                i.email_sent_at,
                i.gmail_message_id AS original_gmail_message_id,
                i.gmail_thread_id,
                i.followups_stopped
            FROM influencer_followups f
            JOIN influencers i
                ON f.influencer_id = i.id
            WHERE f.id = ?
            """,
            (followup_id,)
        ).fetchone()

        return dict(followup) if followup else None


def save_followup_draft(followup_id, subject, body):
    subject = subject.strip()
    body = body.strip()

    if not subject or not body:
        raise ValueError("Follow-up subject and body cannot be empty.")

    with get_connection() as connection:
        followup = connection.execute(
            """
            SELECT f.status, i.followups_stopped, i.email_sent_at
            FROM influencer_followups f
            JOIN influencers i ON f.influencer_id = i.id
            WHERE f.id = ?
            """,
            (followup_id,)
        ).fetchone()

        if not followup:
            raise ValueError("Follow-up not found.")

        if followup["followups_stopped"]:
            raise ValueError("Follow-ups are stopped for this influencer.")

        if not followup["email_sent_at"]:
            raise ValueError(
                "The original outreach email has not been sent."
            )

        if followup["status"] not in ("Due", "Drafted"):
            raise ValueError(
                "Only due follow-ups can have drafts generated."
            )

        connection.execute(
            """
            UPDATE influencer_followups
            SET subject = ?,
                body = ?,
                status = 'Drafted',
                approved = 0,
                approved_at = NULL
            WHERE id = ?
            """,
            (subject, body, followup_id)
        )

        return {
            "updated": True,
            "followup_id": followup_id,
            "status": "Drafted",
            "approved": False
        }


def edit_followup_draft(followup_id, subject, body):
    return save_followup_draft(followup_id, subject, body)


def approve_followup(followup_id):
    with get_connection() as connection:
        followup = connection.execute(
            """
            SELECT f.status, f.subject, f.body, i.followups_stopped
            FROM influencer_followups f
            JOIN influencers i ON f.influencer_id = i.id
            WHERE f.id = ?
            """,
            (followup_id,)
        ).fetchone()

        if not followup:
            raise ValueError("Follow-up not found.")

        if followup["followups_stopped"]:
            raise ValueError(
                "Follow-ups are stopped for this influencer."
            )

        if followup["status"] != "Drafted":
            raise ValueError(
                "Generate a follow-up draft before approving."
            )

        if not followup["subject"] or not followup["body"]:
            raise ValueError("Follow-up draft is incomplete.")

        connection.execute(
            """
            UPDATE influencer_followups
            SET approved = 1,
                approved_at = ?,
                status = 'Approved'
            WHERE id = ?
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                followup_id
            )
        )

        return {
            "approved": True,
            "followup_id": followup_id,
            "status": "Approved"
        }


def mark_followup_sending(followup_id):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE influencer_followups
            SET status = 'Sending'
            WHERE id = ?
              AND status = 'Approved'
              AND approved = 1
              AND influencer_id IN (
                  SELECT id
                  FROM influencers
                  WHERE followups_stopped = 0
                    AND email_sent_at IS NOT NULL
              )
            """,
            (followup_id,)
        )

        return cursor.rowcount == 1


def mark_followup_sent(followup_id, gmail_message_id):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE influencer_followups
            SET status = 'Sent',
                sent_at = ?,
                gmail_message_id = ?
            WHERE id = ?
              AND status = 'Sending'
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                gmail_message_id,
                followup_id
            )
        )

        return cursor.rowcount == 1


def mark_followup_send_unconfirmed(followup_id):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE influencer_followups
            SET status = 'Send Unconfirmed'
            WHERE id = ?
              AND status = 'Sending'
            """,
            (followup_id,)
        )
