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
            location VARCHAR(255),
            latitude FLOAT,
            longitude FLOAT,
            address VARCHAR(255)
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
    {
        "name": "Intersection 1",
        "latitude": 46.97520,
        "longitude": 28.87343,
        "address": "Str. Valea Crucii"
    },
    {
        "name": "Intersection 2",
        "latitude": 46.97867,
        "longitude": 28.86791,
        "address": "Str. Burebista"
    },
    {
        "name": "Intersection 3",
        "latitude": 37.4224514532131,
        "longitude": -122.08449885026891,
        "address": "123 Main St, Cityville"
    },
]

sample_traffic_records = [
    {"time": "2024-03-16T08:00:00", "vehicle_count": 5, "pedestrian_count": 5, "traffic_light_id": 1},
    {"time": "2024-03-16T08:10:00", "vehicle_count": 8, "pedestrian_count": 7, "traffic_light_id": 1},
    {"time": "2024-03-16T08:20:00", "vehicle_count": 10, "pedestrian_count": 4, "traffic_light_id": 1},
    {"time": "2024-03-16T08:30:00", "vehicle_count": 19, "pedestrian_count": 9, "traffic_light_id": 1},
    {"time": "2024-03-16T08:40:00", "vehicle_count": 22, "pedestrian_count": 6, "traffic_light_id": 1},
    {"time": "2024-03-16T08:50:00", "vehicle_count": 8, "pedestrian_count": 8, "traffic_light_id": 2},
    {"time": "2024-03-16T09:00:00", "vehicle_count": 6, "pedestrian_count": 10, "traffic_light_id": 2},
    {"time": "2024-03-16T09:10:00", "vehicle_count": 15, "pedestrian_count": 12, "traffic_light_id": 2},
    {"time": "2024-03-16T09:20:00", "vehicle_count": 19, "pedestrian_count": 5, "traffic_light_id": 2},
    {"time": "2024-03-16T09:30:00", "vehicle_count": 22, "pedestrian_count": 15, "traffic_light_id": 2},
    {"time": "2024-03-16T09:50:00", "vehicle_count": 15, "pedestrian_count": 8, "traffic_light_id": 3},
    {"time": "2024-03-16T10:00:00", "vehicle_count": 16, "pedestrian_count": 10, "traffic_light_id": 3},
    {"time": "2024-03-16T10:10:00", "vehicle_count": 20, "pedestrian_count": 12, "traffic_light_id": 3},
    {"time": "2024-03-16T10:20:00", "vehicle_count": 25, "pedestrian_count": 5, "traffic_light_id": 3},
    {"time": "2024-03-16T10:30:00", "vehicle_count": 27, "pedestrian_count": 15, "traffic_light_id": 3},
]


def insert_sample_data():
    conn = get_connection_from_pool()
    cursor = conn.cursor()

    try:
        for light in sample_traffic_lights:
            cursor.execute(
                "INSERT INTO TrafficLights (location, latitude, longitude, address) "
                "VALUES (%s, %s, %s, %s) RETURNING id;",
                (light['name'], light['latitude'], light['longitude'], light['address'])
            )

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
