from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
)
from src.api.middleware.request_context import RequestContextMiddleware
from src.api.rest.routes.approval_routes import approval_router
from src.api.rest.routes.assignment_routes import assignment_router
from src.api.rest.routes.attachment_routes import attachment_router
from src.api.rest.routes.audit_log_routes import audit_log_router
from src.api.rest.routes.client_routes import client_router
from src.api.rest.routes.client_rules_routes import rule_router
from src.api.rest.routes.email_processing_routes import email_process_router
from src.api.rest.routes.email_routes import email_router
from src.api.rest.routes.email_whitelist_routes import whitelist_router
from src.api.rest.routes.employee_routes import employee_router
from src.api.rest.routes.health_routes import health_router
from src.api.rest.routes.holiday_routes import holiday_router
from src.api.rest.routes.manual_review_routes import review_router
from src.api.rest.routes.paycode_routes import paycode_router
from src.api.rest.routes.payroll_payslip_routes import payroll_payslip_router
from src.api.rest.routes.payroll_routes import payroll_router
from src.api.rest.routes.rule_violation_routes import rule_violation_router
from src.api.rest.routes.timesheet_routes import timesheet_router
from src.config.settings import settings
from src.data.models.postgres.assignment_model import Assignment  # noqa
from src.data.models.postgres.audit_log_model import AuditLog  # noqa
from src.data.models.postgres.client_model import Client  # noqa
from src.data.models.postgres.client_rule_model import ClientRule, RuleViolation  # noqa
from src.data.models.postgres.email_model import (  # noqa
    EmailAttachment,
    EmailMessage,
    EmailThread,
    EmailWhitelist,
)
from src.data.models.postgres.employee_model import Employee  # noqa
from src.data.models.postgres.paycode_model import Paycode  # noqa
from src.data.models.postgres.payroll_model import (  # noqa
    PayrollExport,
    PayrollReadyEntry,
)
from src.data.models.postgres.review_model import Approval, ManualReview  # noqa
from src.data.models.postgres.timesheet_model import TimeEntryRaw, Timesheet  # noqa


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(health_router)
    app.include_router(email_router)
    app.include_router(client_router)
    app.include_router(whitelist_router)
    app.include_router(employee_router)
    app.include_router(email_process_router)
    app.include_router(assignment_router)
    app.include_router(paycode_router)
    app.include_router(timesheet_router)
    app.include_router(review_router)
    app.include_router(approval_router)
    app.include_router(audit_log_router)
    app.include_router(attachment_router)
    app.include_router(payroll_router)
    app.include_router(payroll_payslip_router)
    app.include_router(holiday_router)
    app.include_router(rule_router)
    app.include_router(rule_violation_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL, settings.AUTHBACKEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    return app
