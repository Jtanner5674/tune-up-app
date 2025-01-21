import logging
from flask import Flask, request
from waitress import serve
from server_tools import initialize_db, connect_to_db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
_conn = None

def get_connection():
    global _conn
    if _conn is None:
        try:
            logger.info("Connecting to the database...")
            _conn = connect_to_db()
            logger.info("Database connection established.")
        except Exception as e:
            logger.error(f"Failed to connect to the database: {e}", exc_info=True)
            raise
    return _conn

@app.route('/check_license', methods=['GET'])
def handle_check_license():
    """ Check license and update hash after first use. """
    activation_key = request.args.get('key')  # Get the activation key from the request
    client_hash = request.args.get('hash')  # Get the hash from the client request

    if not activation_key or not client_hash:
        logger.error("Activation key or hash missing in the request.")
        return {"valid": False, "message": "Activation key or hash missing"}, 400

    logger.info(f"Checking license for key: {activation_key} with hash: {client_hash}")
    cur = get_connection().cursor()
    try:
        cur.execute("SELECT * FROM licenses WHERE activation_key = %s", (activation_key,))
        result = cur.fetchone()
        logger.debug(f"Query result: {result}")
    except Exception as e:
        logger.error(f"Error during database query: {e}", exc_info=True)
        return {"valid": False, "message": "Internal server error"}, 500

    if result is None:
        logger.warning(f"License with key {activation_key} not found.")
        return {"valid": False, "message": "License does not exist"}, 404

    # Check and update the hash
    license_hash = result.get('hash')  # No error here because result is a dictionary
    if license_hash == "default_hash_value":
        try:
            logger.info(f"Default hash detected for license {activation_key}. Updating hash.")
            cur.execute(
                "UPDATE licenses SET activated_on = NOW(), hash = %s WHERE activation_key = %s",
                (client_hash, activation_key)
            )
            get_connection().commit()
            logger.info(f"License {activation_key} activated and hash updated.")
            return {"valid": True, "message": "License successfully activated and hash updated"}, 200
        except Exception as e:
            logger.error(f"Error updating hash for license {activation_key}: {e}", exc_info=True)
            return {"valid": False, "message": "Internal server error during hash update"}, 500

    # Validate the hash for subsequent uses
    if license_hash == client_hash:
        logger.info(f"License {activation_key} validated successfully.")
        return {"valid": True, "message": "License validated"}, 200
    else:
        logger.error(f"Hash mismatch for license {activation_key}.")
        return {"valid": False, "message": "Hash mismatch, license invalid"}, 403


if __name__ == '__main__':
    try:
        logger.info("Initializing database...")
        initialize_db(get_connection())
        logger.info("Database initialized.")
        print("Running in production mode.")
        serve(app, host="0.0.0.0", port=5000, threads=4)
    except Exception as e:
        logger.error(f"Error during server initialization: {e}", exc_info=True)
        print(f"Error starting the server: {e}")
