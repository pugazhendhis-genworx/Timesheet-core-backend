from uuid import UUID

from src.core.services.employee_matching_service import (
    match_employees_for_timesheet,
    validate_client_for_timesheet,
)
from src.core.services.timesheet_service import (
    create_timesheet_from_extraction,
)
from src.data.repositories.email_repository import get_email_client_id_by_thread_id


async def process_timesheet(email, output, db):
    email.processed_status = "EXTRACTING"
    await db.flush()

    timesheet_data = output.get("timesheet_data")
    if not timesheet_data:
        raise RuntimeError("LangGraph returned TIMESHEET but no extraction data")

    # Resolve client_id from the LangGraph output or email thread
    client_id = output.get("client_id")
    if not client_id and email.thread_id:
        thread_client_id = await get_email_client_id_by_thread_id(email.thread_id, db)
        if thread_client_id:
            client_id = str(thread_client_id)

    if not client_id:
        raise RuntimeError("Could not resolve client_id for timesheet")

    timesheet = await create_timesheet_from_extraction(
        db=db,
        email_message_id=email.email_message_id,
        client_id=UUID(client_id),
        timesheet_data=timesheet_data,
    )

    await match_employees_for_timesheet(
        db=db,
        timesheet_id=timesheet.timesheet_id,
        raw_extraction=timesheet_data,
    )

    await validate_client_for_timesheet(
        db=db,
        timesheet_id=timesheet.timesheet_id,
        raw_extraction=timesheet_data,
    )

    email.processed_status = "COMPLETED"
    await db.flush()
