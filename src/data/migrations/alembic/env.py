import asyncio
from configparser import ConfigParser
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from src.config.settings import settings
from src.data.clients.database import Base
from src.data.models.postgres.assignment_model import Assignment  # noqa
from src.data.models.postgres.audit_log_model import AuditLog  # noqa
from src.data.models.postgres.client_model import Client  # noqa
from src.data.models.postgres.client_rule_model import ClientRule, RuleViolation  # noqa
from src.data.models.postgres.email_model import (  # noqa
    EmailAttachment,
    EmailClassification,
    EmailMessage,
    EmailThread,
    EmailWhitelist,
)
from src.data.models.postgres.employee_model import Employee  # noqa
from src.data.models.postgres.holiday_model import Holiday  # noqa
from src.data.models.postgres.paycode_model import Paycode  # noqa
from src.data.models.postgres.payroll_model import (  # noqa
    PayrollExport,
    PayrollReadyEntry,
)
from src.data.models.postgres.review_model import ManualReview  # noqa
from src.data.models.postgres.timesheet_model import TimeEntryRaw, Timesheet  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.file_config = ConfigParser(interpolation=None)

DATABASE_URL = settings.POSTGRES_DB_URL
config.set_main_option("sqlalchemy.url", DATABASE_URL)
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        return name in target_metadata.tables
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
        version_table="core_alembic_version",
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=include_object,
        version_table="core_alembic_version",
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
