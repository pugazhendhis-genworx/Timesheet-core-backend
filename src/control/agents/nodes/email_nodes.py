import json
import logging

from dotenv import load_dotenv
from google import genai
from google.genai import types
from groq import Groq
from langfuse import observe
from sqlalchemy import select

from src.config.settings import settings
from src.control.agents.prompts.prompts import (
    build_extract_attachments_prompt,
    build_extract_timesheet_structure,
    build_timesheet_classification_prompt,
)
from src.control.agents.utils.attachment_utils import (
    detect_attachment_type,
    parse_excel_timesheet,
)
from src.core.services.gcs_service import download_from_gcs
from src.data.models.postgres.email_model import EmailThread
from src.data.repositories.email_repository import get_attachments, get_email_by_id

logger = logging.getLogger(__name__)
load_dotenv()


gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)


groq_client = Groq(api_key=settings.GROQ_API_KEY)

MAX_GEMINI_RETRIES = 3
GEMINI_RETRY_DELAY = 2  # seconds, doubles each retry


def _strip_json(text: str) -> str:
    """Strip markdown code fences and whitespace from LLM JSON output."""
    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence (```json or ```)
        text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


# =====================================================
# NODE 1 — LOAD EMAIL
# =====================================================


@observe()
async def load_email(state):

    try:
        db = state["db"]

        email = await get_email_by_id(state["email_id"], db)
        attachments = await get_attachments(state["email_id"], db)

        # Resolve client_id from the email's thread via FK query
        client_id = None
        if email.thread_id:
            result = await db.execute(
                select(EmailThread.client_id).where(
                    EmailThread.thread_id == email.thread_id
                )
            )
            thread_client_id = result.scalar_one_or_none()
            if thread_client_id:
                client_id = str(thread_client_id)

        return {
            "email_subject": email.subject,
            "email_body": email.body,
            "attachments": attachments,
            "client_id": client_id,
        }

    except Exception as e:
        logger.exception("Failed loading email")
        return {"error": str(e)}


# =====================================================
# NODE 2 — EXTRACT ATTACHMENT TEXT
# =====================================================


@observe()
async def extract_attachment_text(state):

    texts = []

    try:
        for att in state.get("attachments", []):
            file_type = detect_attachment_type(att.file_type)

            # Download file bytes from GCS
            file_bytes = download_from_gcs(att.file_path)

            # ------------------------
            # EXCEL
            # ------------------------

            if file_type == "excel":
                texts.append(parse_excel_timesheet(file_bytes))

            # ------------------------
            # IMAGE / PDF → GEMINI
            # ------------------------

            elif file_type in ["pdf", "image"]:
                prompt = build_extract_attachments_prompt()

                # Use the actual MIME type stored in DB
                mime = att.file_type or (
                    "application/pdf" if file_type == "pdf" else "image/jpeg"
                )

                response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        prompt,
                        types.Part.from_bytes(
                            data=file_bytes,
                            mime_type=mime,
                        ),
                    ],
                )

                if response.text:
                    texts.append(response.text)
                else:
                    logger.error("Gemini returned empty response for %s", att.file_name)

        return {"attachment_text": "\n".join(texts)}

    except Exception as e:
        logger.exception("Attachment extraction failed")
        return {"error": str(e)}


# =====================================================
# NODE 3 — EMAIL CLASSIFICATION
# =====================================================


@observe()
async def classify_email(state):

    try:
        prompt = build_timesheet_classification_prompt(
            state.get("email_body"),
            state.get("email_subject"),
            state.get("attachment_text"),
        )

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        result = response.choices[0].message.content

        if not result or not result.strip():
            return {"error": "Classification returned empty response"}

        cleaned = _strip_json(result)
        data = json.loads(cleaned)

        if data.get("is_timesheet"):
            return {"classification": "TIMESHEET"}

        return {"classification": "OTHER"}

    except json.JSONDecodeError as e:
        logger.exception("Classification JSON parse failed")
        return {"error": f"Classification JSON parse failed: {e}"}
    except Exception as e:
        logger.exception("Classification failed")
        return {"error": str(e)}


# =====================================================
# NODE 4 — TIMESHEET EXTRACTION (GROQ)
# =====================================================


@observe()
async def extract_timesheet(state):

    try:
        prompt = build_extract_timesheet_structure(
            state.get("email_body"),
            state.get("email_subject"),
            state.get("attachment_text"),
        )
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            return {"error": "Extraction returned empty response"}

        cleaned = _strip_json(content)
        data = json.loads(cleaned)

        return {"timesheet_data": data}

    except json.JSONDecodeError as e:
        logger.exception("Extraction JSON parse failed")
        return {"error": f"Extraction JSON parse failed: {e}"}
    except Exception as e:
        logger.exception("Extraction failed")
        return {"error": str(e)}
