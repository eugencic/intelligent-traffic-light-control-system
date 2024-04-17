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


def insert_sample_data():
    conn = get_connection_from_pool()
    cursor = conn.cursor()

    sample_traffic_lights = [
        {"location": "Intersection 1"},
        {"location": "Intersection 2"}
    ]

    sample_traffic_records = [
        {"time": "2024-03-16T08:00:00", "vehicle_count": 10, "pedestrian_count": 5, "traffic_light_id": 1},
        {"time": "2024-03-16T08:10:00", "vehicle_count": 15, "pedestrian_count": 7, "traffic_light_id": 1},
        {"time": "2024-03-16T08:20:00", "vehicle_count": 12, "pedestrian_count": 4, "traffic_light_id": 1},
        {"time": "2024-03-16T08:30:00", "vehicle_count": 18, "pedestrian_count": 9, "traffic_light_id": 1},
        {"time": "2024-03-16T08:40:00", "vehicle_count": 20, "pedestrian_count": 6, "traffic_light_id": 1},
        {"time": "2024-03-16T08:50:00", "vehicle_count": 22, "pedestrian_count": 8, "traffic_light_id": 2},
        {"time": "2024-03-16T09:00:00", "vehicle_count": 30, "pedestrian_count": 10, "traffic_light_id": 2},
        {"time": "2024-03-16T09:10:00", "vehicle_count": 35, "pedestrian_count": 12, "traffic_light_id": 2},
        {"time": "2024-03-16T09:20:00", "vehicle_count": 25, "pedestrian_count": 5, "traffic_light_id": 2},
        {"time": "2024-03-16T09:30:00", "vehicle_count": 40, "pedestrian_count": 15, "traffic_light_id": 2},
    ]

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
