from datetime import datetime, timedelta
import random
import psycopg2
import psycopg2.pool

from app.database.config import Config

db_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    **Config.DATABASE
)


def get_connection_from_pool():
    return db_pool.getconn()


def return_connection_to_pool(conn):
    db_pool.putconn(conn)


def setup_database():
    drop_tables = """
        DROP TABLE IF EXISTS TrafficLights;
    """

    create_traffic_light_table = """
        CREATE TABLE IF NOT EXISTS TrafficLights (
            id SERIAL PRIMARY KEY,
            location VARCHAR(255)
        );
    """

    try:
        conn = psycopg2.connect(
            **Config.DATABASE
        )
        cursor = conn.cursor()
        cursor.execute(drop_tables)
        conn.commit()
        cursor.execute(create_traffic_light_table)
        conn.commit()
        cursor.close()
        conn.close()
        print("Database setup completed.")
    except psycopg2.Error as e:
        print(f"Error setting up database: {e}")


sample_traffic_lights = [
    {"location": "Intersection 1"},
    {"location": "Intersection 2"}
]


def insert_sample_data():
    conn = get_connection_from_pool()
    cursor = conn.cursor()

    try:
        for light in sample_traffic_lights:
            cursor.execute("INSERT INTO TrafficLights (location) VALUES (%s) RETURNING id;", (light['location'],))

        conn.commit()

        print("Sample data inserted into the database.")
    except (Exception,) as e:
        conn.rollback()
        print(f"Error inserting sample data: {e}")
    finally:
        cursor.close()
        return_connection_to_pool(conn)
