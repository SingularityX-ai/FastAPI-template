from typing import Optional

import pytest

from fastapi_template.cli import db_menu, orm_menu
from fastapi_template.input_model import BuilderContext
from fastapi_template.tests.utils import model_dump_compat, run_default_check


def init_context(
    context: BuilderContext,
    db: str,
    orm: Optional[str],
    api: Optional[str] = None,
) -> BuilderContext:
    """
    Initialize the context with the provided parameters.

    Args:
    - context (BuilderContext): The context to be initialized.
    - db (str): The database identifier.
    - orm (Optional[str]): The ORM identifier.
    - api (Optional[str], optional): The API type. Defaults to None.

    Returns:
    - BuilderContext: The initialized context.

    Raises:
    - ValueError: If the provided database identifier is unknown.
    """

    db_info = None
    for entry in db_menu.entries:
        if entry.code == db:
            db_info = model_dump_compat(entry.additional_info)
            if entry.pydantic_v1:
                context.pydanticv1 = True
    if db_info is None:
        raise ValueError(f"Unknown database: {db}")

    context.db = db
    context.db_info = db_info
    context.orm = orm
    for entry in orm_menu.entries:
        if entry.code == orm:
            if entry.pydantic_v1:
                context.pydanticv1 = True

    if api is not None:
        context.api_type = api
        if api == "graphql":
            context.pydanticv1 = True

    context.enable_migrations = db != "none"
    context.add_dummy = db != "none"

    return context


def test_default_without_db(default_context: BuilderContext):
    """
    Test the default behavior without using a database.

    Args:
    default_context (BuilderContext): The default context for testing.

    Raises:
    No specific exceptions are raised.
    """

    run_default_check(init_context(default_context, "none", None))


@pytest.mark.parametrize(
    "db",
    [
        "postgresql",
        "sqlite",
        "mysql",
    ],
)
@pytest.mark.parametrize(
    "orm",
    [
        "sqlalchemy",
        "tortoise",
        "ormar",
        "piccolo",
    ],
)
def test_default_with_db(default_context: BuilderContext, db: str, orm: str):
    """
    Test the default with database.

    Args:
        default_context (BuilderContext): The default context.
        db (str): The database type.
        orm (str): The ORM type.

    Raises:
        (Add information about any exceptions that may be raised)

    Returns:
        None
    """

    if orm == "piccolo" and db == "mysql":
        return
    run_default_check(init_context(default_context, db, orm))


@pytest.mark.parametrize("api", ["rest", "graphql"])
@pytest.mark.parametrize(
    "orm",
    [
        "sqlalchemy",
        "tortoise",
        "ormar",
        "piccolo",
    ],
)
def test_default_for_apis(default_context: BuilderContext, orm: str, api: str):
    """
    Test the default settings for APIs.

    Args:
        default_context (BuilderContext): The default context for the APIs.
        orm (str): The Object-Relational Mapping (ORM) type.
        api (str): The API type.

    Raises:
        <Exception Type>: <Description of the exception raised>

    Returns:
        None
    """

    run_default_check(init_context(default_context, "postgresql", orm, api))


@pytest.mark.parametrize(
    "orm",
    [
        "psycopg",
    ],
)
def test_pg_drivers(default_context: BuilderContext, orm: str):
    """
    Test PostgreSQL drivers.

    Args:
    default_context (BuilderContext): The default context.
    orm (str): The Object-Relational Mapping (ORM) to be used.

    Raises:
    <Exception Type>: <Description of the exception raised>

    Returns:
    None
    """

    run_default_check(init_context(default_context, "postgresql", orm))


@pytest.mark.parametrize(
    "orm",
    [
        "sqlalchemy",
        "tortoise",
        "ormar",
        "psycopg",
        "piccolo",
    ],
)
def test_without_routers(default_context: BuilderContext, orm: str):
    """
    Test the functionality without using routers.

    Args:
    default_context (BuilderContext): The default context for the test.
    orm (str): The object-relational mapping type.

    Raises:
    <Exception Type>: <Description of the exception raised>

    Returns:
    None
    """

    context = init_context(default_context, "postgresql", orm)
    context.enable_routers = False
    run_default_check(context)


@pytest.mark.parametrize(
    "orm",
    [
        "sqlalchemy",
        "tortoise",
        "ormar",
        "piccolo",
    ],
)
def test_without_migrations(default_context: BuilderContext, orm: str):
    """
    Test the functionality without migrations.

    Args:
    default_context (BuilderContext): The default context for the test.
    orm (str): The object-relational mapping (ORM) to be used.

    Raises:
    No specific exceptions are raised.

    Returns:
    None
    """

    context = init_context(default_context, "postgresql", orm)
    context.enable_migrations = False
    run_default_check(context)


def test_with_selfhosted_swagger(default_context: BuilderContext):
    """
    Test with self-hosted swagger.

    Args:
        default_context (BuilderContext): The default context with self-hosted swagger enabled.

    Raises:
        Any exceptions raised by the run_default_check function.

    Returns:
        None
    """

    default_context.self_hosted_swagger = True
    run_default_check(default_context)


@pytest.mark.parametrize(
    "orm",
    [
        "sqlalchemy",
        "tortoise",
        "ormar",
        "psycopg",
        "piccolo",
    ],
)
def test_without_dummy(default_context: BuilderContext, orm: str):
    """
    Perform a test without using a dummy value.

    Args:
    default_context (BuilderContext): The default context to be used.
    orm (str): The object-relational mapping to be used.

    Raises:
    Any exceptions that might be raised during the execution of the function.

    Returns:
    None
    """

    context = init_context(default_context, "postgresql", orm)
    context.add_dummy = False
    run_default_check(context)


@pytest.mark.parametrize(
    "api",
    [
        "rest",
        "graphql",
    ],
)
def test_redis(default_context: BuilderContext, api: str):
    """
    Enable Redis and Taskiq in the default context and set the API type.

    Args:
        default_context (BuilderContext): The default context to modify.
        api (str): The type of API to set in the default context.

    Raises:
        <ExceptionType>: <Description of the exception raised>

    Returns:
        None
    """

    default_context.enable_redis = True
    default_context.enable_taskiq = True
    default_context.api_type = api
    if api == "graphql":
        default_context.pydanticv1 = True
    run_default_check(default_context)


@pytest.mark.parametrize(
    "api",
    [
        "rest",
        "graphql",
    ],
)
def test_rmq(default_context: BuilderContext, api: str):
    """
    Enable RMQ and TaskIQ in the default context and set the API type.

    Args:
        default_context (BuilderContext): The default context to modify.
        api (str): The type of API to set in the default context.

    Raises:
        Any exceptions that may be raised during the execution of the function.

    Returns:
        None
    """

    default_context.enable_rmq = True
    default_context.enable_taskiq = True
    default_context.api_type = api
    if api == "graphql":
        default_context.pydanticv1 = True
    run_default_check(default_context)


def test_telemetry_pre_commit(default_context: BuilderContext):
    """
    Test telemetry pre-commit.

    Args:
        default_context (BuilderContext): The default context.

    Raises:
        Any exceptions raised during the execution of the function.

    Returns:
        None
    """

    default_context.enable_rmq = True
    default_context.enable_redis = True
    default_context.prometheus_enabled = True
    default_context.otlp_enabled = True
    default_context.sentry_enabled = True
    default_context.enable_loguru = True
    run_default_check(default_context, without_pytest=True)


def test_gunicorn(default_context: BuilderContext):
    """
    Test gunicorn.

    Args:
    default_context (BuilderContext): The default context.

    Raises:
    None

    Returns:
    None
    """

    default_context.gunicorn = True
    run_default_check(default_context, without_pytest=True)


# @pytest.mark.parametrize("api", ["rest", "graphql"])
# def test_kafka(default_context: BuilderContext, api: str):
#     default_context.enable_kafka = True
#     default_context.api_type = api
#     run_default_check(default_context)
