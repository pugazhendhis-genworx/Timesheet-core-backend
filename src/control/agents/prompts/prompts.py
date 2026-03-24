from dotenv import load_dotenv
from langfuse import get_client

load_dotenv()

langfuse = get_client()


def build_extract_attachments_prompt():
    prompt = langfuse.get_prompt(
        "time_guard/extract_attachment_prompt", label="production"
    )
    compiled_prompt = prompt.compile()
    return compiled_prompt


def build_timesheet_classification_prompt(email_body, email_subject, attachment_text):
    prompt = langfuse.get_prompt(
        "time_guard/timesheet_classification_prompt", label="production"
    )
    compiled_prompt = prompt.compile(
        email_body=email_body,
        email_subject=email_subject,
        attachment_text=attachment_text,
    )
    return compiled_prompt


def build_extract_timesheet_structure(email_body, email_subject, attachment_text):
    prompt = langfuse.get_prompt(
        "time_guard/extract_timesheet_structure", label="production"
    )
    compiled_prompt = prompt.compile(
        email_body=email_body,
        email_subject=email_subject,
        attachment_text=attachment_text,
    )
    return compiled_prompt
