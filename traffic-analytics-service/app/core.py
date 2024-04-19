import json
import numpy as np
import pandas as pd
import psycopg2
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import threading

from app.database.db import get_connection_from_pool, return_connection_to_pool

lock = threading.Lock()

traffic_records_cache = []
traffic_statistics_cache = {}
models_by_intersection = {}

df = pd.DataFrame()


def update_cache():
    global traffic_records_cache

    conn = get_connection_from_pool()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT time, vehicle_count, pedestrian_count, traffic_light_id FROM TrafficRecords;")
        records = cursor.fetchall()

        traffic_records_cache.clear()

        for record in records:
            time_str = record[0].isoformat()
            vehicle_count = record[1]
            pedestrian_count = record[2]
            traffic_light_id = record[3]

            traffic_record = {
                "time": time_str,
                "vehicle_count": vehicle_count,
                "pedestrian_count": pedestrian_count,
                "traffic_light_id": traffic_light_id
            }

            traffic_records_cache.append(traffic_record)

    except psycopg2.Error as e:
        print(f"Error fetching traffic records: {e}")
    finally:
        cursor.close()
        return_connection_to_pool(conn)


def init_frame():
    global df
    df = pd.DataFrame(traffic_records_cache)


def update_frame(data):
    global df
    new_data = pd.DataFrame(data, index=range(len(data)))
    df = pd.concat([df, new_data], ignore_index=True)


def return_frame():
    global df
    return df


def calculate_statistics(traffic_light_data):
    peak_vehicle_threshold = 20
    peak_pedestrian_threshold = 10
    normal_vehicle_threshold = 10
    normal_pedestrian_threshold = 5

    traffic_light_data.sort_values(by='time', inplace=True)
    traffic_light_data['time'] = pd.to_datetime(traffic_light_data['time'])

    peak_hours_intervals = []
    normal_hours_intervals = []
    light_hours_intervals = []

    total_vehicle_count = 0
    total_pedestrian_count = 0

    for i in range(len(traffic_light_data)):
        row = traffic_light_data.iloc[i]
        vehicle_count = row['vehicle_count']
        pedestrian_count = row['pedestrian_count']
        current_time = row['time']

        total_vehicle_count += vehicle_count
        total_pedestrian_count += pedestrian_count

        if vehicle_count >= peak_vehicle_threshold or pedestrian_count >= peak_pedestrian_threshold:
            current_interval = peak_hours_intervals
        elif vehicle_count >= normal_vehicle_threshold or pedestrian_count >= normal_pedestrian_threshold:
            current_interval = normal_hours_intervals
        else:
            current_interval = light_hours_intervals

        if current_interval:
            last_start_time, last_end_time = current_interval[-1]
            if current_time == last_end_time + pd.Timedelta(minutes=10):
                current_interval[-1][1] = current_time
            else:
                current_interval.append([current_time, current_time])
        else:
            current_interval.append([current_time, current_time])

    num_records = len(traffic_light_data)
    mean_vehicle_count = total_vehicle_count / num_records if num_records > 0 else 0
    mean_pedestrian_count = total_pedestrian_count / num_records if num_records > 0 else 0

    peak_hours_intervals_str = [[start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')] for start, end in peak_hours_intervals]
    normal_hours_intervals_str = [[start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')] for start, end in normal_hours_intervals]
    light_hours_intervals_str = [[start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')] for start, end in light_hours_intervals]

    min_time = traffic_light_data['time'].min().strftime('%Y-%m-%dT%H:%M:%S')
    max_time = traffic_light_data['time'].max().strftime('%Y-%m-%dT%H:%M:%S')

    return {
        'peak_hours_intervals': peak_hours_intervals_str,
        'normal_hours_intervals': normal_hours_intervals_str,
        'light_hours_intervals': light_hours_intervals_str,
        'mean_vehicle_count': mean_vehicle_count,
        'mean_pedestrian_count': mean_pedestrian_count,
        'time_min': min_time,
        'time_max': max_time
    }


def update_statistics():
    global df, traffic_statistics_cache

    threading.Timer(20, update_statistics).start()

    with lock:
        stats = df.groupby('traffic_light_id').apply(calculate_statistics)
        traffic_statistics_cache.update(stats)

        conn = get_connection_from_pool()
        cursor = conn.cursor()

        try:
            for traffic_light_id, stat in stats.items():
                cursor.execute(
                    "SELECT id FROM TrafficStatistics WHERE traffic_light_id = %s;", (traffic_light_id,)
                )
                result = cursor.fetchone()

                if result:
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
                            result[0]
                        )
                    )
                else:
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

            print("Updating Statistics...\n")
        except Exception as e:
            conn.rollback()
            print(f"Error updating statistics: {e}")
        finally:
            cursor.close()
            return_connection_to_pool(conn)


def extract_hour_minute(df):
    df_copy = df.copy()

    df_copy['time'] = pd.to_datetime(df_copy['time'])

    df_copy['hour'] = df_copy['time'].dt.hour
    df_copy['minute'] = df_copy['time'].dt.minute

    return df_copy


def train_models_by_intersection(df):
    models = {}

    df_copy = extract_hour_minute(df)

    grouped_data = df_copy.groupby('traffic_light_id')

    for traffic_light_id, data in grouped_data:
        X = data[['hour', 'minute']].values
        y = data['vehicle_count'].values

        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        models[traffic_light_id] = model

    return models


def update_models():
    global models_by_intersection, df

    new_models = train_models_by_intersection(df)

    with lock:
        models_by_intersection = new_models

    print("Updating Predictions...\n")

    threading.Timer(20, update_models).start()


def predict_vehicle_count(hour, minute, traffic_light_id):
    global models_by_intersection

    model = models_by_intersection.get(traffic_light_id)

    if model is None:
        return None

    X_pred = np.array([[hour, minute]])

    predicted_count = model.predict(X_pred)

    return predicted_count[0]
