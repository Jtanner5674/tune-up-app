import argparse
from servertools.py import connect_to_db, initialize_db, create_license, remove_entry, list_entries

def main():
    """
    CLI for managing licenses using the servertools script.
    """
    parser = argparse.ArgumentParser(description="Client connector for managing licenses.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Initialize database
    init_parser = subparsers.add_parser("init", help="Initialize the database")

    # Create a license
    create_parser = subparsers.add_parser("create", help="Create a new license")
    create_parser.add_argument(
        "--user-id",
        required=True,
        type=int,
        help="Provide the User ID for whom the license is created"
    )

    # Remove a license
    remove_parser = subparsers.add_parser("remove", help="Remove a license by ID")
    remove_parser.add_argument(
        "--id",
        required=True,
        type=int,
        help="ID of the license to be removed"
    )

    # List all licenses
    subparsers.add_parser("list", help="List all licenses in the database")

    args = parser.parse_args()

    # Connect to the database
    try:
        conn = connect_to_db()
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return

    # Execute the selected command
    try:
        if args.command == "init":
            initialize_db(conn)
            print("Database initialized successfully.")

        elif args.command == "create":
            create_license(conn, user_id=args.user_id)
            print(f"License created for user {args.user_id}.")

        elif args.command == "remove":
            remove_entry(conn, args.id)
            print(f"License with ID {args.id} has been removed.")

        elif args.command == "list":
            print("Listing all licenses:")
            list_entries(conn)

    except Exception as e:
        print(f"Error executing command '{args.command}': {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
