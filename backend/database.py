import sqlite3
import os

DB_DIR = os.environ.get("DB_DIR", os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(DB_DIR, "trazabilidad.db")

def get_db_connection():
    # Helper for db connection
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Initializes the telemetry table (drops existing to sync with in-memory blockchain)
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS telemetria')
    c.execute('''
        CREATE TABLE IF NOT EXISTS telemetria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_viaje TEXT NOT NULL,
            id_lote TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            temperatura REAL NOT NULL,
            timestamp REAL NOT NULL,
            block_hash TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_telemetria(numero_viaje, id_lote, lat, lon, temperatura, timestamp):
    """
    Inserts raw telemetry off-chain data and returns the primary key ID.
    The block_hash is updated later when the block is mined/created.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO telemetria (numero_viaje, id_lote, lat, lon, temperatura, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (numero_viaje, id_lote, lat, lon, temperatura, timestamp))
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    return row_id

def update_block_hash(row_id, block_hash):
    """
    Updates the registry with its cryptographic proof (the blockchain hash).
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE telemetria SET block_hash = ? WHERE id = ?
    ''', (block_hash, row_id))
    conn.commit()
    conn.close()

def get_all_telemetria():
    """
    Retrieves all records for the frontend or for auditing comparisons.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM telemetria ORDER BY id ASC')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]
