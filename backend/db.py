import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error, pooling
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'admin'),
    'database': os.getenv('DB_NAME', 'smart_gardening')
}

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name='agriculture_pool',
            pool_size=5,
            **DB_CONFIG
        )
    return _pool

def get_db_connection(user_db=None):
    """Return a connection from the pool. Switch DB to user_db or default global DB."""
    try:
        conn = get_pool().get_connection()
        target_db = user_db if user_db else DB_CONFIG['database']
        cursor = conn.cursor()
        cursor.execute(f"USE `{target_db}`")
        cursor.close()
        return conn
    except Error as e:
        print(f"DB connection error: {e}")
        return None

def create_tables():
    connection = get_db_connection()
    if connection is None:
        return False
    try:
        cursor = connection.cursor()

        # Global users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                farm_size VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Global crops table
        cursor.execute("DROP TABLE IF EXISTS crops")
        cursor.execute("""
            CREATE TABLE crops (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                season VARCHAR(50),
                water_needs VARCHAR(50),
                soil_type VARCHAR(100),
                fertilizer VARCHAR(100),
                sunlight VARCHAR(50),
                detailed_plan JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Global diseases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diseases (
                id INT AUTO_INCREMENT PRIMARY KEY,
                crop_name VARCHAR(100) NOT NULL,
                disease_name VARCHAR(100) NOT NULL,
                symptoms TEXT,
                treatment TEXT,
                prevention TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Global market prices
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_prices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                crop_name VARCHAR(100) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                unit VARCHAR(20) DEFAULT 'per kg',
                location VARCHAR(100),
                date_recorded DATE DEFAULT (CURRENT_DATE),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Global crop finance data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crop_finance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                crop_name VARCHAR(100) UNIQUE NOT NULL,
                seed_cost_multiplier DECIMAL(5,2) DEFAULT 1.0,
                yield_per_sqm DECIMAL(8,2) DEFAULT 3.0,
                market_price_per_kg DECIMAL(8,2) DEFAULT 2.0,
                growing_period_months INT DEFAULT 4,
                labor_multiplier DECIMAL(5,2) DEFAULT 1.0
            )
        """)

        # Global crop irrigation data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crop_irrigation (
                id INT AUTO_INCREMENT PRIMARY KEY,
                crop_name VARCHAR(100) UNIQUE NOT NULL,
                base_level VARCHAR(20) DEFAULT 'Moderate',
                drip_duration_mins INT DEFAULT 30,
                sprinkler_duration_mins INT DEFAULT 20,
                growth_stage_modifiers JSON
            )
        """)

        connection.commit()
        print("Global tables created successfully!")
        return True
    except Error as e:
        print(f"Error creating global tables: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def setup_user_database(username):
    """Creates a dedicated database for a specific user to store their personal records."""
    db_name = f"user_{username}"
    # Temporarily connect to global DB just to execute CREATE DATABASE
    connection = get_db_connection()
    if not connection: return False
    
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        cursor.execute(f"USE `{db_name}`")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS soil_tests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ph_level DECIMAL(3,1),
                soil_type VARCHAR(50),
                color VARCHAR(50),
                moisture VARCHAR(50),
                nutrients TEXT,
                recommendations TEXT,
                test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS finance_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                crop_name VARCHAR(100),
                area_sqm DECIMAL(10,2),
                mode VARCHAR(50),
                total_cost DECIMAL(10,2),
                breakdown TEXT,
                estimated_yield DECIMAL(10,2),
                record_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS advisory_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                query TEXT NOT NULL,
                response_summary TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id INT,
                activity_type VARCHAR(50) NOT NULL,
                summary TEXT NOT NULL,
                details JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES user_sessions(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS irrigation_settings (
                id INT PRIMARY KEY DEFAULT 1,
                pump_state BOOLEAN DEFAULT 0,
                auto_mode BOOLEAN DEFAULT 0,
                target_moisture DECIMAL(5,2) DEFAULT 50.0,
                current_moisture DECIMAL(5,2) DEFAULT 45.0,
                water_consumed_today DECIMAL(10,2) DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CHECK (id = 1)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS irrigation_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                action VARCHAR(50),
                source VARCHAR(20) DEFAULT 'manual',
                water_used_liters DECIMAL(10,2),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Initialize settings if not exists
        cursor.execute("INSERT IGNORE INTO irrigation_settings (id, pump_state, auto_mode) VALUES (1, 0, 0)")
        
        # MIGRATION: Ensure session_id column exists if table was created older
        cursor.execute("SHOW COLUMNS FROM activity_log LIKE 'session_id'")
        if not cursor.fetchone():
            print(f"Migrating activity_log for {username}...")
            cursor.execute("ALTER TABLE activity_log ADD COLUMN session_id INT AFTER id")
            cursor.execute("ALTER TABLE activity_log ADD FOREIGN KEY (session_id) REFERENCES user_sessions(id) ON DELETE CASCADE")
            
        connection.commit()
        print(f"User database `{db_name}` initialized!")
        return True
    except Error as e:
        print(f"Error creating user DB {db_name}: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


import json

def insert_sample_data():
    connection = get_db_connection()
    if connection is None:
        return False
    try:
        cursor = connection.cursor()

        hashed_pw = generate_password_hash('password')
        cursor.execute(
            "INSERT IGNORE INTO users (name, username, password, email, farm_size) VALUES (%s, %s, %s, %s, %s)",
            ('Administrator', 'admin', hashed_pw, 'admin@example.com', 'N/A')
        )
        connection.commit()
        setup_user_database('admin')

        # Load generated 1000 crops base data and harvest plans
        try:
            with open('backend/data/db_seed.json', 'r') as f:
                seed_data = json.load(f)
            crops_data = seed_data.get("crops", [])
            prices_data = seed_data.get("prices", [])
            
            with open('backend/data/harvest_plans.json', 'r') as f:
                harvest_plans = json.load(f)
        except Exception:
            crops_data = []
            prices_data = []
            harvest_plans = {}
            
        if crops_data:
            enriched_crops = []
            for crop in crops_data:
                crop_name = crop[0]
                c_key = crop_name.lower().strip()
                # Get JSON structure, or empty dict if missing
                detailed_plan_json = json.dumps(harvest_plans.get(c_key, {}))
                
                enriched_crops.append((
                    crop[0], crop[1], crop[2], crop[3], crop[4], crop[5], detailed_plan_json
                ))
                
            cursor.executemany(
                "INSERT INTO crops (name, season, water_needs, soil_type, fertilizer, sunlight, detailed_plan) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                enriched_crops
            )

        if prices_data:
            cursor.executemany(
                "INSERT IGNORE INTO market_prices (crop_name, price, unit, location) VALUES (%s,%s,%s,%s)",
                prices_data
            )
            
        # Optional: Load diseases
        try:
            with open('backend/data/disease_data.json', 'r') as f:
                disease_dict = json.load(f)
            diseases_data = []
            for c_key, disease_list in disease_dict.items():
                # c_key is lowercase, but we don't have exact case mapping easily here. 
                # Storing it lowercase is fine for mocking.
                for d in disease_list:
                    diseases_data.append((
                        c_key.title(),
                        d['disease'],
                        "Various symptoms",
                        d['treatment'],
                        "Regular monitoring"
                    ))
            if diseases_data:
                cursor.executemany(
                    "INSERT IGNORE INTO diseases (crop_name, disease_name, symptoms, treatment, prevention) VALUES (%s,%s,%s,%s,%s)",
                    diseases_data
                )
        except Exception:
            pass

        connection.commit()
        print(f"Sample data ({len(crops_data)} crops) inserted successfully!")
        return True
    except Error as e:
        print(f"Error inserting sample data: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def create_user(name, username, password, farm_size):
    """Register a new user and initialize their personal database."""
    connection = get_db_connection()
    if connection is None:
        return False, "Database connection failed"
    try:
        cursor = connection.cursor()
        
        # Check if exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return False, "Username already exists"
            
        hashed_pw = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (name, username, password, farm_size) VALUES (%s, %s, %s, %s)",
            (name, username, hashed_pw, farm_size)
        )
        connection.commit()
        
        # After inserting, create their personal database
        success = setup_user_database(username)
        if not success:
            return False, "User created but database initialization failed"
            
        return True, "User created successfully"
    except Error as e:
        print(f"Error creating user: {e}")
        return False, str(e)
    finally:
        cursor.close()
        connection.close()


def get_user_by_username(username):
    connection = get_db_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error retrieving user: {e}")
        return None
    finally:
        cursor.close()
        connection.close()


def get_crops():
    connection = get_db_connection()
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM crops")
        return cursor.fetchall()
    except Error as e:
        print(f"Error retrieving crops: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_diseases_by_crop(crop_name):
    connection = get_db_connection()
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM diseases WHERE crop_name = %s", (crop_name,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error retrieving diseases: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_market_prices():
    connection = get_db_connection()
    if connection is None:
        return {}
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT crop_name, price FROM market_prices
            WHERE (crop_name, date_recorded) IN (
                SELECT crop_name, MAX(date_recorded) FROM market_prices GROUP BY crop_name
            )
        """)
        prices = cursor.fetchall()
        return {p['crop_name']: float(p['price']) for p in prices}
    except Error as e:
        print(f"Error retrieving prices: {e}")
        return {}
    finally:
        cursor.close()
        connection.close()


def save_soil_test(username, ph_level, soil_type, color, moisture, nutrients, recommendations):
    connection = get_db_connection(f"user_{username}")
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO soil_tests (ph_level, soil_type, color, moisture, nutrients, recommendations)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (ph_level, soil_type, color, moisture, nutrients, recommendations))
        connection.commit()
        return True
    except Error as e:
        print(f"Error saving soil test: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def save_finance_record(username, crop_name, area_sqm, mode, total_cost, breakdown, estimated_yield):
    connection = get_db_connection(f"user_{username}")
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO finance_records (crop_name, area_sqm, mode, total_cost, breakdown, estimated_yield)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (crop_name, area_sqm, mode, total_cost, breakdown, estimated_yield))
        connection.commit()
        return True
    except Error as e:
        print(f"Error saving finance record: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def save_advisory_history(username, query, response_summary):
    connection = get_db_connection(f"user_{username}")
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO advisory_history (query, response_summary)
            VALUES (%s, %s)
        """, (query, response_summary))
        connection.commit()
        return True
    except Error as e:
        print(f"Error saving advisory history: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_advisory_history(username):
    connection = get_db_connection(f"user_{username}")
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM advisory_history ORDER BY timestamp DESC LIMIT 20")
        return cursor.fetchall()
    except Error as e:
        print(f"Error retrieving advisory history: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def create_session(username):
    """Create a new login session for the user and return its ID."""
    connection = get_db_connection(f"user_{username}")
    if connection is None:
        return None
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO user_sessions (status) VALUES ('active')")
        session_id = cursor.lastrowid
        connection.commit()
        return session_id
    except Error as e:
        print(f"Error creating session: {e}")
        return None
    finally:
        cursor.close()
        connection.close()


def save_activity(username, activity_type, summary, details=None, session_id=None):
    """Log a user activity to the user-specific database."""
    # Exclude dashboard overviews as requested: Dashboard/Market/Weather are now filtered in app.py
    connection = get_db_connection(f"user_{username}")
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO activity_log (session_id, activity_type, summary, details)
            VALUES (%s, %s, %s, %s)
        """, (session_id, activity_type, summary, json.dumps(details) if details else None))
        connection.commit()
        return True
    except Error as e:
        print(f"Error saving activity: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


def get_activity_history(username, limit_sessions=10):
    """Retrieve recent login sessions and their associated activity logs."""
    connection = get_db_connection(f"user_{username}")
    if connection is None:
        return []
    try:
        cursor = connection.cursor(dictionary=True)
        # Fetch the most recent sessions
        cursor.execute(
            "SELECT id, login_time, status FROM user_sessions ORDER BY login_time DESC LIMIT %s",
            (limit_sessions,)
        )
        sessions = cursor.fetchall()
        
        for sess in sessions:
            # Format login time
            if sess.get('login_time'):
                sess['login_time'] = sess['login_time'].strftime('%Y-%m-%d %H:%M:%S')
            
            # Fetch actions for this session
            cursor.execute(
                "SELECT id, activity_type, summary, details, created_at FROM activity_log WHERE session_id = %s ORDER BY created_at ASC",
                (sess['id'],)
            )
            logs = cursor.fetchall()
            for log in logs:
                if log.get('created_at'):
                    log['created_at'] = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                if log.get('details') and isinstance(log['details'], str):
                    try:
                        log['details'] = json.loads(log['details'])
                    except Exception:
                        pass
            sess['activities'] = logs
            
        return sessions
    except Error as e:
        print(f"Error retrieving session history: {e}")
        return []
    finally:
        cursor.close()
        connection.close()

# Keep alias for compatibility in app.py if needed
def get_activity_log(username, limit=30):
    return get_activity_history(username, limit_sessions=limit)

def get_irrigation_status(username):
    connection = get_db_connection(f"user_{username}")
    if connection is None:
        return None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM irrigation_settings WHERE id = 1")
        settings = cursor.fetchone()
        
        cursor.execute("SELECT * FROM irrigation_logs ORDER BY timestamp DESC LIMIT 10")
        logs = cursor.fetchall()
        for log in logs:
            if log.get('timestamp'):
                log['timestamp'] = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'settings': settings,
            'recent_logs': logs
        }
    except Error as e:
        print(f"Error retrieving irrigation status: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def update_irrigation_status(username, pump_state=None, auto_mode=None, target_moisture=None, current_moisture=None, add_water=0):
    connection = get_db_connection(f"user_{username}")
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        updates = []
        params = []
        
        if pump_state is not None:
            updates.append("pump_state = %s")
            params.append(pump_state)
        if auto_mode is not None:
            updates.append("auto_mode = %s")
            params.append(auto_mode)
        if target_moisture is not None:
            updates.append("target_moisture = %s")
            params.append(target_moisture)
        if current_moisture is not None:
            updates.append("current_moisture = %s")
            params.append(current_moisture)
        if add_water > 0:
            updates.append("water_consumed_today = water_consumed_today + %s")
            params.append(add_water)
            
        if updates:
            sql = f"UPDATE irrigation_settings SET {', '.join(updates)} WHERE id = 1"
            cursor.execute(sql, tuple(params))
            connection.commit()
        return True
    except Error as e:
        print(f"Error updating irrigation status: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def log_irrigation_event(username, action, source='manual', water_used=0):
    connection = get_db_connection(f"user_{username}")
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO irrigation_logs (action, source, water_used_liters)
            VALUES (%s, %s, %s)
        """, (action, source, water_used))
        connection.commit()
        return True
    except Error as e:
        print(f"Error logging irrigation event: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    print("Setting up database...")
    if create_tables():
        print("Inserting sample data...")
        insert_sample_data()
    print("Database setup complete!")
