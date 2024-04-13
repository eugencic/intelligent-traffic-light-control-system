import json
import threading
import psycopg2.pool
from flask import Flask, jsonify, request
import pandas as pd
from datetime import datetime

app = Flask(__name__)
lock = threading.Lock()

traffic_records_cache = []
traffic_statistics_cache = {}

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
        dbname='traffic-analytics',
        user='postgres',
        password='111111',
        # host='traffic-analytics',
        host='localhost',
        port='5433'
    )
    print("Connected to traffic analytics database.")
    cursor = conn.cursor()
    cursor.execute(drop_tables)
    conn.commit()
    cursor.execute(create_traffic_light_table)
    conn.commit()
    cursor.execute(create_traffic_records_table)
    conn.commit()
    cursor.execute(create_traffic_statistics_table)
    conn.commit()
    print("Tables created.")
    cursor.close()
    conn.close()
except (Exception,) as e:
    print(f"Error connecting to the traffic analytics database.")

db_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dbname='traffic-analytics',
    user='postgres',
    password='111111',
    # host='traffic-analytics',
    host='localhost',
    port='5433'
)


def get_connection_from_pool():
    return db_pool.getconn()


def return_connection_to_pool(conn):
    db_pool.putconn(conn)


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
    cursor.close()
    return_connection_to_pool(conn)


insert_sample_data()


def update_cache():
    global traffic_records_cache
    conn = get_connection_from_pool()
    cursor = conn.cursor()

    try:
        # Fetch traffic records from the database
        cursor.execute("SELECT time, vehicle_count, pedestrian_count, traffic_light_id FROM TrafficRecords;")
        records = cursor.fetchall()

        # Clear existing cache
        traffic_records_cache.clear()

        # Iterate over fetched records and format them as dictionaries
        for record in records:
            time_str = record[0].isoformat()  # Convert timestamp to ISO format string
            vehicle_count = record[1]
            pedestrian_count = record[2]
            traffic_light_id = record[3]

            # Create a dictionary representing the traffic record
            traffic_record = {
                "time": time_str,
                "vehicle_count": vehicle_count,
                "pedestrian_count": pedestrian_count,
                "traffic_light_id": traffic_light_id
            }

            # Append the formatted record to the cache list
            traffic_records_cache.append(traffic_record)

    except psycopg2.Error as e:
        print(f"Error fetching traffic records: {e}")

    finally:
        cursor.close()
        return_connection_to_pool(conn)


update_cache()

print("Initial cache ", traffic_records_cache)
# Convert to DataFrame
df = pd.DataFrame(traffic_records_cache)
print(df)


def calculate_statistics(traffic_light_data):

    # Define thresholds for peak, light, and normal hours
    global vehicle_count, pedestrian_count
    peak_vehicle_threshold = 30
    peak_pedestrian_threshold = 10
    normal_vehicle_threshold = 20
    normal_pedestrian_threshold = 5

    # Initialize lists to store time intervals for peak, light, and normal hours
    peak_hours_intervals = []
    light_hours_intervals = []
    normal_hours_intervals = []

    # Initialize accumulators for vehicle and pedestrian counts
    total_vehicle_count = 0
    total_pedestrian_count = 0

    # Initialize variables to track the start and end times of each interval
    current_interval_start = None
    current_interval_end = None

    # Iterate over each record to calculate statistics
    for index, row in traffic_light_data.iterrows():
        vehicle_count = row['vehicle_count']
        pedestrian_count = row['pedestrian_count']
        current_time = datetime.strptime(row['time'], '%Y-%m-%dT%H:%M:%S')

        # Update total counts
        total_vehicle_count += vehicle_count
        total_pedestrian_count += pedestrian_count

        # Check if the current interval is peak, light, or normal hours
        if vehicle_count >= peak_vehicle_threshold or pedestrian_count >= peak_pedestrian_threshold:
            if current_interval_start is None:
                current_interval_start = current_time
            current_interval_end = current_time
        elif vehicle_count >= normal_vehicle_threshold or pedestrian_count >= normal_pedestrian_threshold:
            if current_interval_start is None:
                current_interval_start = current_time
            current_interval_end = current_time
        else:
            if current_interval_start is not None:
                # Store the current interval and reset the interval variables
                interval_range = (current_interval_start, current_interval_end)
                if vehicle_count >= peak_vehicle_threshold or pedestrian_count >= peak_pedestrian_threshold:
                    peak_hours_intervals.append(interval_range)
                elif vehicle_count >= normal_vehicle_threshold or pedestrian_count >= normal_pedestrian_threshold:
                    normal_hours_intervals.append(interval_range)
                else:
                    light_hours_intervals.append(interval_range)
                current_interval_start = None
                current_interval_end = None

    # Handle the case where there's only one record
    if current_interval_start is not None:
        interval_range = (current_interval_start, current_interval_end)
        if vehicle_count >= peak_vehicle_threshold or pedestrian_count >= peak_pedestrian_threshold:
            peak_hours_intervals.append(interval_range)
        elif vehicle_count >= normal_vehicle_threshold or pedestrian_count >= normal_pedestrian_threshold:
            normal_hours_intervals.append(interval_range)
        else:
            light_hours_intervals.append(interval_range)

    # Calculate mean vehicle and pedestrian counts
    mean_vehicle_count = total_vehicle_count / len(traffic_light_data)
    mean_pedestrian_count = total_pedestrian_count / len(traffic_light_data)

    # Get minimum and maximum times
    min_time = traffic_light_data['time'].min()
    max_time = traffic_light_data['time'].max()

    return {
        'peak_hours_intervals': [(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')) for start, end
                                 in peak_hours_intervals],
        'normal_hours_intervals': [(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')) for
                                   start, end in normal_hours_intervals],
        'light_hours_intervals': [(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')) for
                                  start, end in light_hours_intervals],
        'mean_vehicle_count': mean_vehicle_count,
        'mean_pedestrian_count': mean_pedestrian_count,
        'time_min': min_time,
        'time_max': max_time
    }


def update_statistics():
    global df, traffic_statistics_cache

    threading.Timer(10, update_statistics).start()

    with lock:
        # Group traffic records by traffic_light_id and calculate statistics
        stats = df.groupby('traffic_light_id').apply(calculate_statistics)

        # Update traffic_statistics_cache with the calculated statistics
        traffic_statistics_cache.update(stats)
        print(traffic_statistics_cache)
        # Update TrafficStatistics table in the database with the new statistics
        conn = get_connection_from_pool()
        cursor = conn.cursor()

        try:
            for traffic_light_id, stat in stats.items():
                # Retrieve existing statistics for the traffic light (if any)
                cursor.execute(
                    "SELECT id FROM TrafficStatistics WHERE traffic_light_id = %s;", (traffic_light_id,)
                )
                result = cursor.fetchone()

                if result:
                    # Update existing statistics
                    cursor.execute(
                        "UPDATE TrafficStatistics SET peak_hours_intervals = %s, normal_hours_intervals = %s, "
                        "light_hours_intervals = %s, mean_vehicle_count = %s, mean_pedestrian_count = %s, "
                        "time_min = %s, time_max = %s WHERE id = %s;",
                        (
                            json.dumps(stat['peak_hours_intervals']),
                            json.dumps(stat['normal_hours_intervals']),
                            json.dumps(stat['light_hours_intervals']),
                            stat['mean_vehicle_count'],
                            stat['mean_pedestrian_count'],
                            stat['time_min'],
                            stat['time_max'],
                            result[0]  # Use the ID of the existing statistics record
                        )
                    )
                else:
                    # Insert new statistics
                    cursor.execute(
                        "INSERT INTO TrafficStatistics (traffic_light_id, peak_hours_intervals, normal_hours_intervals,"
                        "light_hours_intervals, mean_vehicle_count, mean_pedestrian_count, time_min, time_max) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
                        (
                            traffic_light_id,
                            json.dumps(stat['peak_hours_intervals']),
                            json.dumps(stat['normal_hours_intervals']),
                            json.dumps(stat['light_hours_intervals']),
                            stat['mean_vehicle_count'],
                            stat['mean_pedestrian_count'],
                            stat['time_min'],
                            stat['time_max']
                        )
                    )

            conn.commit()

        except Exception as e:
            conn.rollback()
            print(f"Error updating statistics: {e}")

        finally:
            cursor.close()
            return_connection_to_pool(conn)


# Start the thread for updating statistics periodically
update_statistics()

# @app.route('/statistics/<int:traffic_light_id>', methods=['GET'])
# def statistics(traffic_light_id):
#     with lock:
#         # Filter data for the specified traffic light
#         traffic_light_data = df[df['traffic_light_id'] == traffic_light_id]
#
#         # Check if there are records available for the specified traffic light ID
#         if len(traffic_light_data) == 0:
#             return jsonify(
#                 {'message': f'No statistics available for traffic light {traffic_light_id}. Insufficient data.'})
#
#         # Calculate statistics
#         stats = calculate_statistics(traffic_light_data)
#
#         # Return the statistics
#         return jsonify(stats)

@app.route('/statistics/<int:traffic_light_id>', methods=['GET'])
def get_statistics(traffic_light_id):
    with lock:
        if traffic_light_id in traffic_statistics_cache:
            # Retrieve statistics from cache
            statistics = traffic_statistics_cache[traffic_light_id]
            return jsonify(statistics)
        else:
            return jsonify({'message': f'Statistics not available for traffic light {traffic_light_id}'}), 404

# @app.route('/add_data', methods=['POST'])
# def add_data():
#     data = request.json
#     global df
#     with lock:
#         # Create a DataFrame from the JSON data and specify the index explicitly
#         new_data = pd.DataFrame(data, index=range(len(data)))
#         df = pd.concat([df, new_data], ignore_index=True)
#     return jsonify({'message': 'Data added successfully'}), 200

@app.route('/add_data', methods=['POST'])
def add_data():
    data = request.json
    conn = get_connection_from_pool()
    cursor = conn.cursor()

    try:
        for record in data:
            # Insert new data into the TrafficRecords table
            print(record)
            cursor.execute(
                "INSERT INTO TrafficRecords (traffic_light_id, time, vehicle_count, pedestrian_count) "
                "VALUES (%s, %s, %s, %s);",
                (record['traffic_light_id'], record['time'], record['vehicle_count'], record['pedestrian_count'])
            )
            conn.commit()

            # Update cache with the new record
            time_str = record['time']
            traffic_record = {
                "time": time_str,
                "vehicle_count": record['vehicle_count'],
                "pedestrian_count": record['pedestrian_count'],
                "traffic_light_id": record['traffic_light_id']
            }
            traffic_records_cache.append(traffic_record)

        # Refresh DataFrame with updated cache
        global df
        new_data = pd.DataFrame(data, index=range(len(data)))
        df = pd.concat([df, new_data], ignore_index=True)
        print("Updated cache ", traffic_records_cache)
        print(df)
        return jsonify({'message': 'Data added successfully'}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Failed to add data: {str(e)}'}), 500

    finally:
        cursor.close()
        return_connection_to_pool(conn)


if __name__ == '__main__':
    app.run(debug=True)
