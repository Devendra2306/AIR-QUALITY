import argparse
import logging

from database_manager import (
    close_database_connection,
    collect_query_paths,
    connect_to_database,
    execute_query,
    read_query,
)


def build_presentation_views(database_path: str, presentation_query_parent_dir: str) -> None:
    query_paths = collect_query_paths(presentation_query_parent_dir)
    con = connect_to_database(database_path)

    try:
        for query_path in query_paths:
            query = read_query(query_path)
            execute_query(con, query)
            logging.info("Executed presentation query from %s", query_path)
    finally:
        close_database_connection(con)


def main():
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description="Build presentation views.")
    parser.add_argument(
        "--database-path",
        required=True,
        help="Path to the DuckDB database.",
    )
    parser.add_argument(
        "--presentation-query-parent-dir",
        required=True,
        help="Directory containing presentation SQL files.",
    )

    args = parser.parse_args()
    build_presentation_views(
        database_path=args.database_path,
        presentation_query_parent_dir=args.presentation_query_parent_dir,
    )


if __name__ == "__main__":
    main()
