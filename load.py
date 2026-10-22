#!/usr/bin/env python3

import argparse
import re
from pathlib import Path

import duckdb


def discover_season_files(base_dir: Path) -> list[Path]:
    """Return all season TSV files under the dataset directory."""
    candidates = []

    if (base_dir / "seasons").exists():
        candidates.extend(sorted((base_dir / "seasons").glob("season*.tsv")))

    if not candidates:
        candidates.extend(sorted(base_dir.glob("**/season*.tsv")))

    if not candidates:
        raise FileNotFoundError(
            f"No season TSV files were found under '{base_dir}'. "
            "Expected files like 'season1.tsv' or a 'seasons/' folder."
        )

    return candidates


def sanitize_table_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r"[^0-9A-Za-z_]", "_", name)
    if not name:
        raise ValueError(f"Could not build a valid DuckDB table name from '{filename}'")
    return name


def load_seasons(dataset_dir: Path, db_path: Path) -> list[str]:
    season_files = discover_season_files(dataset_dir)
    table_names = []
    schema_name = "main"
    db_name = "main"

    with duckdb.connect(str(db_path)) as con:
        con.execute("USE main;")
        for season_file in season_files:
            table_name = sanitize_table_name(season_file.name)
            qualified_table = f"{db_name}.{schema_name}.{table_name}"
            table_names.append(qualified_table)

            print(f"Loading {season_file.name} into table '{qualified_table}'...")
            con.execute(f"DROP TABLE IF EXISTS {schema_name}.{table_name};")
            con.execute(
                f"""
                CREATE TABLE {schema_name}.{table_name} AS
                SELECT *
                FROM read_csv_auto(
                    '{season_file.as_posix()}',
                    delim='\t',
                    header=True,
                    all_varchar=False,
                    sample_size=-1,
                    ignore_errors=False
                );
                """
            )

    return table_names


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load each season TSV file from the Jeopardy dataset into its own DuckDB table."
    )
    parser.add_argument(
        "dataset_dir",
        nargs="?",
        default="/Users/alecpeters/Downloads/jeopardy_dataset_seasons_1-42",
        help="Path to the Jeopardy dataset root directory.",
    )
    parser.add_argument(
        "--db",
        default="/Users/alecpeters/jepopardy-game/jeopardy_seasons.duckdb",
        help="Output DuckDB database path.",
    )
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    db_path = Path(args.db)

    print(f"Dataset directory: {dataset_dir}")
    print(f"DuckDB file: {db_path}")
    print("Schema: main")
    print("Database: main")

    table_names = load_seasons(dataset_dir, db_path)
    print(f"Loaded {len(table_names)} season tables into {db_path}")
    print("Tables:", ", ".join(table_names))
