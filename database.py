import sqlite3
import polars as pl
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import psycopg2
from typing import List
from urllib.parse import urlparse


load_dotenv()

DB_PATH = os.getenv("DB_PATH")
PRODUCTS_TABLE = os.getenv("PRODUCTS_TABLE")

MASTERDB_USER = os.getenv("MASTERDB_USER")
MASTERDB_PASSWORD = os.getenv("MASTERDB_PASSWORD")
MASTERDB_HOST = os.getenv("MASTERDB_HOST")
MASTERDB_PORT = os.getenv("MASTERDB_PORT")
MASTERDB_NAME = os.getenv("MASTERDB_NAME")
SEARCH_HISTORY_TABLE = "search_history"

MASTER_DATABASE_URL = f"postgresql://{MASTERDB_USER}:{MASTERDB_PASSWORD}@{MASTERDB_HOST}:{MASTERDB_PORT}/{MASTERDB_NAME}"
LOCAL_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine_master_db = create_engine(MASTER_DATABASE_URL)
SessionLocal_master_db = sessionmaker(autocommit=False, autoflush=False, bind=engine_master_db)

engine_local_db = create_engine(LOCAL_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal_local_db = sessionmaker(autocommit=False, autoflush=False, bind=engine_local_db)

def get_local_master():
    db = SessionLocal_master_db()
    try:
        yield db
    finally:
        db.close()

def get_local_db():
    """
    Dependency function to create and manage database sessions.
    """
    db = SessionLocal_local_db()
    try:
        yield db
    finally:
        db.close()


def download_master_table(db_uri=MASTER_DATABASE_URL) -> pl.DataFrame:
    q = f"SELECT barcode, name, price, unit FROM {PRODUCTS_TABLE}"
    data = pl.read_database_uri(query=q, uri=db_uri, engine="adbc")
    print(data.head())

    # Convert all date/datetime cols to string or the columns will have wrong string format in SQLITE
    # data = data.with_columns(
        # [
            # pl.col(x).dt.strftime("%Y-%m-%d %H:%M:%S").alias(x)
            # for x in ["create_time", "update_time"]
        # ]
    # ).with_columns(
        # [pl.col(x).dt.strftime("%Y-%m-%d").alias(x) for x in ["expiry_date"]]
    # )

    sqlite_conn = sqlite3.connect(DB_PATH)
    data.to_pandas().to_sql(
        PRODUCTS_TABLE, sqlite_conn, if_exists="replace", index=False
    )

    sqlite_conn.commit()
    sqlite_conn.close()
    return

def is_table_exists():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (PRODUCTS_TABLE,)
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None  # Returns True if a row was found, False otherwise
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False  # Handle potential errors

def log_search(search_txt: str, is_found: bool):
    conn = None
    try:
        
        parsed_uri = urlparse(MASTER_DATABASE_URL)
        
        conn = psycopg2.connect(
            dbname=parsed_uri.path[1:],  # Remove leading slash
            user=parsed_uri.username,
            password=parsed_uri.password,
            host=parsed_uri.hostname,
            port=parsed_uri.port
        )
        
        with conn:
            with conn.cursor() as cursor:
                # time column is in UTC
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {SEARCH_HISTORY_TABLE} (
                        search_id SERIAL PRIMARY KEY,
                        search_text TEXT NOT NULL,
                        is_found  BOOLEAN NOT NULL,
                        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()

                cursor.execute(f'''
                    INSERT INTO {SEARCH_HISTORY_TABLE} (search_text, is_found)
                    VALUES (%s, %s)
                ''', (search_txt, is_found))
                conn.commit()
                
        print("Barcode logged successfully")

    except psycopg2.OperationalError as e:
        print(f"Connection failed: {str(e)}")
    except psycopg2.Error as e:
        print(f"Database error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    finally:
        if conn is not None:
            conn.close()