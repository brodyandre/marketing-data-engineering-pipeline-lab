from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from src.config import get_settings


DEFAULT_TARGET_SCHEMA = "analytics"
SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
REQUIRED_TABLES = [
    "dim_date",
    "dim_campaign",
    "dim_customer",
    "dim_device",
    "fact_marketing_performance",
]


def _validate_tables(tables: dict[str, pd.DataFrame]) -> None:
    missing = [table_name for table_name in REQUIRED_TABLES if table_name not in tables]
    if missing:
        raise ValueError(
            "Missing transformed tables for load: " + ", ".join(missing)
        )


def _create_engine():
    settings = get_settings()
    try:
        return create_engine(
            settings.sqlalchemy_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10},
        )
    except Exception as exc:  # pragma: no cover
        raise ValueError(
            "Could not create SQLAlchemy engine from current configuration."
        ) from exc


def _execute_sql_script(engine, script_path: Path) -> None:
    if not script_path.exists():
        raise ValueError(f"Required SQL script not found: {script_path}")

    script = script_path.read_text(encoding="utf-8")
    raw_connection = engine.raw_connection()
    try:
        with raw_connection.cursor() as cursor:
            cursor.execute(script)
        raw_connection.commit()
    finally:
        raw_connection.close()


def _prepare_tables_for_load(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    prepared: dict[str, pd.DataFrame] = {}

    for table_name, dataframe in tables.items():
        prepared[table_name] = dataframe.copy()

    # Keep date values aligned with DATE column type in SQL DDL.
    prepared["dim_date"]["full_date"] = pd.to_datetime(
        prepared["dim_date"]["full_date"], errors="coerce"
    ).dt.date

    return prepared


def _truncate_target_tables(engine, schema_name: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                f"""
                TRUNCATE TABLE
                    {schema_name}.fact_marketing_performance,
                    {schema_name}.dim_customer,
                    {schema_name}.dim_campaign,
                    {schema_name}.dim_device,
                    {schema_name}.dim_date
                """
            )
        )


def _append_table(engine, schema_name: str, table_name: str, dataframe: pd.DataFrame) -> None:
    dataframe.to_sql(
        name=table_name,
        con=engine,
        schema=schema_name,
        if_exists="append",
        index=False,
        method="multi",
    )


def load_to_postgres(tables: dict[str, pd.DataFrame]) -> None:
    """
    Load transformed dimensional/fact tables into PostgreSQL schema analytics.
    """
    _validate_tables(tables)
    settings = get_settings()
    target_schema = settings.db_schema or DEFAULT_TARGET_SCHEMA
    if target_schema != DEFAULT_TARGET_SCHEMA:
        raise ValueError(
            f"Unsupported POSTGRES_SCHEMA='{target_schema}'. "
            f"This project currently loads into schema '{DEFAULT_TARGET_SCHEMA}'."
        )
    print(f"[load] Connecting to PostgreSQL at {settings.db_host}:{settings.db_port}...")

    engine = _create_engine()
    prepared_tables = _prepare_tables_for_load(tables)

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("[load] Connection established.")
    except SQLAlchemyError as exc:
        raise ValueError(
            "Could not connect to PostgreSQL. Check host, port, database, user, and password."
        ) from exc

    try:
        # Apply canonical SQL DDL before loading to preserve PK/FK constraints.
        _execute_sql_script(engine, SQL_DIR / "01_create_schema.sql")
        _execute_sql_script(engine, SQL_DIR / "02_create_tables.sql")
        print(f"[load] Ensured schema '{target_schema}' and tables exist.")

        _truncate_target_tables(engine, target_schema)
        print(f"[load] Cleared existing data from schema '{target_schema}'.")

        for table_name in REQUIRED_TABLES:
            print(f"[load] Loading table {target_schema}.{table_name}...")
            _append_table(engine, target_schema, table_name, prepared_tables[table_name])
        print("[load] Load completed successfully.")
    except SQLAlchemyError as exc:
        raise ValueError(
            f"Failed to load transformed tables into schema '{target_schema}'."
        ) from exc
    finally:
        engine.dispose()


def main() -> None:
    from src.extract import extract_data
    from src.transform import transform_data

    try:
        extracted = extract_data()
        tables = transform_data(extracted)
        load_to_postgres(tables)
    except ValueError as exc:
        print(f"[load] ERROR: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
