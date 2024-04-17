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
        DROP TABLE IF EXISTS TrafficRecords;
        DROP TABLE IF EXISTS TrafficStatistics;
        DROP TABLE IF EXISTS TrafficLights;
    """

    create_traffic_light_table = """
        CREATE TABLE IF NOT EXISTS TrafficLights (
            id SERIAL PRIMARY KEY,
            location VARCHAR(255)
        );
    """

    create_traffic_records_table = """
        CREATE TABLE IF NOT EXISTS TrafficRecords (
            id SERIAL PRIMARY KEY,
            traffic_light_id INTEGER REFERENCES TrafficLights(id),
            time TIMESTAMP,
            vehicle_count INTEGER,
            pedestrian_count INTEGER
        );
    """

    create_traffic_statistics_table = """
        CREATE TABLE IF NOT EXISTS TrafficStatistics (
            id SERIAL PRIMARY KEY,
            traffic_light_id INTEGER REFERENCES TrafficLights(id),
            peak_hours_intervals JSONB,
            normal_hours_intervals JSONB,
            light_hours_intervals JSONB,
            mean_vehicle_count FLOAT,
            mean_pedestrian_count FLOAT,
            time_min TIMESTAMP,
            time_max TIMESTAMP
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
        cursor.execute(create_traffic_records_table)
        conn.commit()
        cursor.execute(create_traffic_statistics_table)
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

sample_traffic_records = []


def generate_mockup_data():
    num_intersections = len(sample_traffic_lights)
    rows_per_intersection = 20

    current_date = datetime.today().date()

    start_time = datetime.combine(current_date, datetime.min.time())
    end_time = datetime.combine(current_date, datetime.max.time())
    time_diff_seconds = (end_time - start_time).total_seconds()

    try:
        for intersection_id in range(1, num_intersections + 1):
            for _ in range(rows_per_intersection):
                random_seconds = random.randint(0, int(time_diff_seconds))
                random_time = start_time + timedelta(seconds=random_seconds)

                vehicle_count = random.randint(5, 50)
                pedestrian_count = random.randint(1, 20)

                sample_traffic_records.append({
                    "traffic_light_id": intersection_id,
                    "time": random_time,
                    "vehicle_count": vehicle_count,
                    "pedestrian_count": pedestrian_count
                })

        print("Mockup data generation completed.")
    except Exception as e:
        print(f"Error generating mockup data: {e}")


def insert_sample_data():
    conn = get_connection_from_pool()
    cursor = conn.cursor()

    try:
        for light in sample_traffic_lights:
            cursor.execute("INSERT INTO TrafficLights (location) VALUES (%s) RETURNING id;", (light['location'],))

            traffic_light_id = cursor.fetchone()[0]

            for record in sample_traffic_records:
                if record['traffic_light_id'] == traffic_light_id:
                    cursor.execute(
                        "INSERT INTO TrafficRecords (traffic_light_id, time, vehicle_count, pedestrian_count) "
                        "VALUES (%s, %s, %s, %s);",
                        (traffic_light_id, record['time'], record['vehicle_count'], record['pedestrian_count'])
                    )

        conn.commit()

        print("Sample data inserted into the database.")
    except (Exception,) as e:
        conn.rollback()
        print(f"Error inserting sample data: {e}")
    finally:
        cursor.close()
        return_connection_to_pool(conn)
