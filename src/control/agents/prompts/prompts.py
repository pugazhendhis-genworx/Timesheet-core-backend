from dotenv import load_dotenv
from langfuse import get_client

load_dotenv()

langfuse = get_client()


def build_extract_attachments_prompt() -> str:
    prompt = langfuse.get_prompt(
        "time_guard/extract_attachment_prompt", label="production"
    )
    compiled_prompt = prompt.compile()
    return compiled_prompt


def build_timesheet_classification_prompt(
    email_body: str | None,
    email_subject: str | None,
    attachment_text: str | None,
) -> str:
    prompt = langfuse.get_prompt(
        "time_guard/timesheet_classification_prompt", label="production"
    )
    compiled_prompt = prompt.compile(
        email_body=email_body,
        email_subject=email_subject,
        attachment_text=attachment_text,
    )
    return compiled_prompt


def build_extract_timesheet_structure(
    email_body: str | None,
    email_subject: str | None,
    attachment_text: str | None,
) -> str:
    prompt = langfuse.get_prompt(
        "time_guard/extract_timesheet_structure", label="production"
    )
    expected_json = {
        "week_ending": "",
        "multiple_employees": False,
        "conflict": False,
        "detected_employee_names": [],
        "entries": [
            {
                "employee_name": "",
                "employee_email": "",
                "date": "",
                "start_time": "",
                "end_time": "",
                "total_hours": 0,
                "paycode": "",
            }
        ],
    }
    compiled_prompt = prompt.compile(
        email_body=email_body,
        email_subject=email_subject,
        attachment_text=attachment_text,
        expected_json=expected_json,
    )
    return compiled_prompt
