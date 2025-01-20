import pymysql
import uuid

def connect_to_db():
    """
    Connect to the MariaDB database using connection parameters.
    """
    conn = pymysql.connect(
        database='licenses',         
        user='root',              
        password='NTi',          
        host='192.168.4.114',
        port=3306                       
    )
    return conn

def initialize_db(conn):
    """
    Initialize the database. Creates a table named 'licenses' if it doesn't exist.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM licenses LIMIT 1")
            print("Table already exists.")
    except pymysql.MySQLError:
        conn.rollback()
        print("Creating new table.")
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS licenses (
                    id VARCHAR(255) PRIMARY KEY,  -- Use VARCHAR to allow strings as user IDs
                    hash TEXT NOT NULL UNIQUE,
                    activation_key TEXT NOT NULL UNIQUE,
                    activated_on DATETIME
                )
            """)
        conn.commit()

def create_license(conn, user_id=None):
    """
    Automates license creation for a user. User ID can be a string or None.
    """
    # Generate unique license values
    license_hash = str(uuid.uuid4())
    activation_key = str(uuid.uuid4())

    # Prepare entry
    entry = {
        'id': user_id,
        'hash': license_hash,
        'activation_key': activation_key,
        'activated_on': None,
    }

    # Insert the new license into the database
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO licenses (id, hash, activation_key, activated_on)
            VALUES (%s, %s, %s, %s)
        """, (entry['id'], entry['hash'], entry['activation_key'], entry['activated_on']))
    conn.commit()

    print(f"License created for user {user_id}.")
    print(f"  Activation key: {activation_key}")


def remove_entry(conn, entry_id):
    """
    Remove an entry from the database by ID.
    """
    with conn.cursor() as cur:
        cur.execute("DELETE FROM licenses WHERE id = %s", (entry_id,))
    conn.commit()

def list_entries(conn):
    """
    List all licenses in the database.
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT * FROM licenses")
        entries = cur.fetchall()
    for entry in entries:
        print(f"""
              ID: {entry['id']},
              Hash: {entry['hash']},
              Activation key: {entry['activation_key']},
              Activated on: {entry['activated_on']}""")

def main():
    """
    Parse command line arguments and call the appropriate function.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Manage database entries.')
    parser.add_argument('--init', action='store_true', help='Initialize the database')
    parser.add_argument('--create', metavar='USER_ID', type=str, help='Create a perpetual license for a user')
    parser.add_argument('--remove', metavar='ID', type=int, help='Remove an entry from the database by ID')
    parser.add_argument('--list', action='store_true', help='List all licenses')

    args = parser.parse_args()

    conn = connect_to_db()

    if args.init:
        initialize_db(conn)
    elif args.create:
        create_license(conn, args.create)
    elif args.remove:
        remove_entry(conn, args.remove)
    elif args.list:
        list_entries(conn)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
