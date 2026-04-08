from typing import Any, TypedDict

from sqlalchemy.ext.asyncio import AsyncSession


class EmailProcessingState(TypedDict, total=False):
    email_id: str
    email_body: str
    email_subject: str
    db: AsyncSession

    client_id: str | None

    attachments: list[dict[str, Any]]
    attachment_text: str
    attachment_types: list[str]

    extracted_text: str

    classification: str

    timesheet_data: dict[str, Any] | None

    error: str | None
