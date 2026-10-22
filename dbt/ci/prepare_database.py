"""Seed production snapshot history from main when production is first built."""
import os
from pathlib import Path

import duckdb


def prepare_database(db_path: Path) -> None:
    if not db_path.is_file():
        raise FileNotFoundError(f"Expected the existing season database at {db_path}")

    with duckdb.connect(str(db_path)) as con:
        history_schemas = {
            row[0]
            for row in con.execute(
                """
                select table_schema
                from information_schema.tables
                where table_catalog = current_database()
                  and table_name = 'jeopardy_episodes_history'
                """
            ).fetchall()
        }
        if "prod" in history_schemas:
            print("Production history already exists; preserving it.")
            return
        if "main" not in history_schemas:
            raise ValueError("Cannot initialize prod: main.jeopardy_episodes_history is missing.")

        con.execute("create schema if not exists prod")
        con.execute(
            """
            create table prod.jeopardy_episodes_history as
            select * from main.jeopardy_episodes_history
            """
        )
        print("Initialized prod.jeopardy_episodes_history from main history.")


if __name__ == "__main__":
    prepare_database(Path(os.environ["DBT_DUCKDB_PATH"]))
