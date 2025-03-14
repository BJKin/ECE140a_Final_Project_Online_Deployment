import os
import time
import logging
import mysql.connector

from typing import Optional
from dotenv import load_dotenv
from mysql.connector import Error

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_connection(
    max_retries: int = 12,  # 12 retries = 1 minute total (12 * 5 seconds)
    retry_delay: int = 5,  # 5 seconds between retries
) -> mysql.connector.MySQLConnection:
    """Create database connection with retry mechanism"""
    
    connection: Optional[mysql.connector.MySQLConnection] = None
    attempt = 1
    last_error = None

    while attempt <= max_retries:
        try:
            connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            host=os.getenv('MYSQL_HOST'),
            port=int(os.getenv('MYSQL_PORT')),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE'),
            ssl_ca=os.getenv('MYSQL_SSL_CA'),  # Path to CA certificate file
            ssl_verify_identity=True
            )

            # Test the connection
            connection.ping(reconnect=True, attempts=1, delay=0)
            logger.info("Database connection established successfully")
            return connection

        except Error as err:
            last_error = err
            logger.warning(
                f"Connection attempt {attempt}/{max_retries} failed: {err}. "
                f"Retrying in {retry_delay} seconds..."
            )

            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

            if attempt == max_retries:
                break

            time.sleep(retry_delay)
            attempt += 1

    raise Exception(
        f"Failed to connect to database after {max_retries} attempts. "
        f"Last error: {last_error}"
    )


async def setup_database():
    """Creates user and session tables and populates initial user data if provided"""

    connection = None
    cursor = None

    # Define table schemas
    table_schemas = {
        "users": """
            CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                location VARCHAR(255),
                password VARCHAR(255) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "sessions": """
            CREATE TABLE sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                token VARCHAR(255) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """,
        "devices": """
            CREATE TABLE devices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                device_id VARCHAR(100) NOT NULL,
                mac_address VARCHAR(100) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """,
        "wardrobes": """
            CREATE TABLE wardrobes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                name VARCHAR(100) NOT NULL,
                color VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """,
        "sensordata": """
            CREATE TABLE sensordata (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                device_id VARCHAR(100) NOT NULL,
                temperature FLOAT,
                pressure FLOAT,
                temperature_unit VARCHAR(50) NOT NULL,
                pressure_unit VARCHAR(50) NOT NULL,
                timestamp DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """
    }

    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        
        logger.info("Dropping existing tables...")

        drop_order = ["sensordata", "wardrobes", "devices", "sessions", "users"]
        for table_name in drop_order:
            logger.info(f"Dropping table {table_name} if exists...")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            connection.commit()

        create_order = ["users", "sessions", "devices", "wardrobes", "sensordata"]
        for table_name in create_order:
            try:
                # Create table
                logger.info(f"Creating table {table_name}...")
                cursor.execute(table_schemas[table_name])
                connection.commit()
                logger.info(f"Table {table_name} created successfully")

            except Error as e:
                logger.error(f"Error creating table {table_name}: {e}")
                raise

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            logger.info("Database connection closed")


async def create_user(name: str, email: str, password: str, location: str) -> bool:
    """Create a new user in the database"""

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            raise ValueError(f"User with email {email} already exists")
            
        cursor.execute(
            """
            INSERT INTO users (name, email, location, password, created_at) 
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (name, email, location, password)
        )
        connection.commit()
        
        return True
    except Exception as e:
        logger.error(f"New user creation failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def get_user_by_email(email: str) -> Optional[dict]:
    """Retrieve user from database by email"""

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()
    
    except Exception as e:
        logger.error(f"Retrieving user by email failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def get_user_by_id(user_id: int) -> Optional[dict]:
    """Retrieve user from database by ID"""

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()
    
    except Exception as e:
        logger.error(f"Retrieving user by ID failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            

async def create_session(user_id: int, token: str, expires_at: str) -> bool:
    """Create a new session in the database"""

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO sessions (user_id, token, created_at, expires_at) 
            VALUES (%s, %s, NOW(), %s)
            """, 
            (user_id, token, expires_at)
        )
        connection.commit()
        return True
    except Exception as e:
        logger.error(f"Session setup failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def get_session(token: str) -> Optional[dict]:
    """Retrieve session from database"""

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM sessions
            WHERE token= %s
            """,
            (token, )
        )
        return cursor.fetchone()
    
    except Exception as e:
        logger.error(f"Retrieving session failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def delete_session(session_id: str) -> bool:
    """Delete a session from the database"""

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = %s", (session_id,))
        connection.commit()
        return True
    
    except Exception as e:
        logger.error(f"Deleting session failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def add_clothing(user_id: int, name: str, color: str) -> bool:
    """Create a new piece of clothing for a given user"""

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            """
            INSERT INTO wardrobes (user_id, name, color, created_at) 
            VALUES (%s, %s, %s, NOW())
            """,
            (user_id, name, color)
        )
        connection.commit()
        return True
    
    except Exception as e:
        logger.error(f"Clothing creation failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def remove_clothing(user_id: int, clothing_id: int) -> bool:
    """Remove a specific piece of clothing for a given user"""

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            DELETE FROM wardrobes WHERE 
            user_id = %s AND 
            id = %s
            """, 
            (user_id, clothing_id)
        )
        connection.commit()
        return True
    
    except Exception as e:
        logger.error(f"Deleting clothing failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def update_clothing(user_id: int, clothing_id: int, new_name: str, new_color: str) -> bool:
    """Update specific piece of clothing for a given user"""

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE wardrobes 
            SET name = %s, color = %s WHERE 
            user_id = %s AND 
            id = %s
            """, 
            (new_name, new_color, user_id, clothing_id)
        )
        connection.commit()
        return True
    
    except Exception as e:
        logger.error(f"Updating clothing failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def get_wardrobe(user_id: int) -> list:
    """Retrieve user wardrobe from database"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM wardrobes 
            WHERE user_id = %s
            """,
            (user_id,)
        )
        clothes = cursor.fetchall()
    
        for clothing in clothes:
            clothing['created_at'] = clothing['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return clothes 
    
    except Exception as e:
        logger.error(f"Retrieving wardrobe failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def get_clothing(user_id: int, clothing_id: int) -> Optional[dict]:
    """Retrieve specific clothing item from database"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM wardrobes 
            WHERE user_id = %s AND id = %s
            """,
            (user_id, clothing_id)
        )
        clothing = cursor.fetchone()
        
        if clothing:
            clothing['created_at'] = clothing['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return clothing 
    
    except Exception as e:
        logger.error(f"Retrieving clothing item failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def get_devices(user_id: int) -> list:
    """Retrieve user devices from database"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM devices 
            WHERE user_id = %s
            """,
            (user_id,)
        )
        devices = cursor.fetchall()
        
        for device in devices:
            device['created_at'] = device['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return devices
    except Exception as e:
        logger.error(f"Retrieving devices failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def get_device(user_id: int, device_id: str) -> Optional[dict]:
    """Retrieve specific device from database"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM devices WHERE 
            user_id = %s AND 
            device_id = %s
            """,
            (user_id, device_id)
        )
        device = cursor.fetchone()
        
        if device:
            device['created_at'] = device['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return device
    except Exception as e:
        logger.error(f"Retrieving device failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def add_device(user_id: int, device_id: str, mac_address: str) -> bool:
    """
    Create a new device for a given user
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM devices 
            WHERE mac_address = %s
            """,
            (mac_address,)
        )

        count = cursor.fetchone()[0]
        if count > 0:
            return False
        
        cursor.execute(
            """
            INSERT INTO devices (user_id, device_id, mac_address, created_at) 
            VALUES (%s, %s, %s, NOW())
            """,
            (user_id, device_id, mac_address)
        )
        connection.commit()
        return True
    
    except Exception as e:
        logger.error(f"Device creation failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def remove_device(user_id: int, device_id: str, mac_address: str) -> bool:
    """Remove a specific device for a given user"""

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            DELETE FROM devices WHERE 
            user_id = %s AND 
            device_id = %s AND
            mac_address = %s
            """, 
            (user_id, device_id, mac_address)
        )
        connection.commit()
        return True
    
    except Exception as e:
        logger.error(f"Deleting device failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def add_sensorData(user_id: int, device_id: str, temperature: float, pressure: float, temperature_unit: str, pressure_unit: str, timestamp: str) -> bool:
    """Store sensor data"""

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            """
            INSERT INTO sensordata (user_id, device_id, temperature, pressure, 
                                   temperature_unit, pressure_unit, timestamp) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, device_id, temperature, pressure, temperature_unit, pressure_unit, timestamp)
        )
        connection.commit()
        return True
    
    except Exception as e:
        logger.error(f"Sensor data creation failed: {e}")
        raise 
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def get_device_by_mac_address(mac_address: str) -> Optional[dict]:
    """Retrieve device from database by MAC address"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM devices WHERE mac_address = %s
            """,
            (mac_address,)
        )
        device = cursor.fetchone()
        
        if device:
            device['created_at'] = device['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return device
    except Exception as e:
        logger.error(f"Retrieving device by MAC address failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


async def get_sensorData(user_id: int, device_id: str, time_start: str, time_end: str) -> list:
    """Retrieve sensor data from database"""

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute(
            """
            SELECT timestamp, temperature, pressure, temperature_unit, pressure_unit
            FROM sensordata
            WHERE timestamp BETWEEN %s AND %s
            AND user_id = %s
            AND device_id = %s
            ORDER BY timestamp
            """,
            (time_start, time_end, user_id, device_id)
        )
        return cursor.fetchall()
    
    except Exception as e:
        logger.error(f"Retrieving sensor data failed: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()