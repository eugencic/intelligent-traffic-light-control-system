# import threading
# from flask import Flask, jsonify
# import pandas as pd
# from datetime import datetime
#
# app = Flask(__name__)
# lock = threading.Lock()
#
# # Sample data
# sample_data = [
#     {"time": "2024-03-16T08:00:00", "vehicle_count": 10, "pedestrian_count": 5, "traffic_light_id": 1},
#     {"time": "2024-03-16T08:10:00", "vehicle_count": 15, "pedestrian_count": 7, "traffic_light_id": 1},
#     {"time": "2024-03-16T08:20:00", "vehicle_count": 12, "pedestrian_count": 4, "traffic_light_id": 1},
#     {"time": "2024-03-16T08:30:00", "vehicle_count": 18, "pedestrian_count": 9, "traffic_light_id": 1},
#     {"time": "2024-03-16T08:40:00", "vehicle_count": 20, "pedestrian_count": 6, "traffic_light_id": 1},
#     {"time": "2024-03-16T08:50:00", "vehicle_count": 22, "pedestrian_count": 8, "traffic_light_id": 2},
#     {"time": "2024-03-16T09:00:00", "vehicle_count": 30, "pedestrian_count": 10, "traffic_light_id": 2},
#     {"time": "2024-03-16T09:10:00", "vehicle_count": 35, "pedestrian_count": 12, "traffic_light_id": 2},
#     {"time": "2024-03-16T09:20:00", "vehicle_count": 25, "pedestrian_count": 5, "traffic_light_id": 2},
#     {"time": "2024-03-16T09:30:00", "vehicle_count": 40, "pedestrian_count": 15, "traffic_light_id": 2},
# ]
#
# # Convert to DataFrame
# df = pd.DataFrame(sample_data)
#
#
# # Function to update statistics
# def update_statistics():
#     global df
#     with lock:
#         # Group by traffic_light_id and calculate statistics
#         stats = df.groupby('traffic_light_id').agg({
#             'vehicle_count': ['mean', 'std'],
#             'pedestrian_count': ['mean', 'std'],
#             'time': ['min', 'max']
#         })
#         print("Updated statistics:")
#         print(stats)
#
#     # Schedule the next update after 5 seconds
#     threading.Timer(5, update_statistics).start()
#
#
# # Initialize the update_statistics function
# update_statistics()
#
#
# def categorize_intervals(traffic_light_data):
#     # Define thresholds for peak, light, and normal hours
#     peak_vehicle_threshold = 30
#     peak_pedestrian_threshold = 10
#     normal_vehicle_threshold = 20
#     normal_pedestrian_threshold = 5
#
#     # Initialize lists to store time intervals for peak, light, and normal hours
#     peak_hours_intervals = []
#     light_hours_intervals = []
#     normal_hours_intervals = []
#
#     # Initialize accumulators for vehicle and pedestrian counts
#     total_vehicle_count = 0
#     total_pedestrian_count = 0
#
#     # Initialize variables to track the start and end times of each interval
#     current_interval_start = None
#     current_interval_end = None
#
#     # Iterate over each record to calculate statistics
#     for index, row in traffic_light_data.iterrows():
#         vehicle_count = row['vehicle_count']
#         pedestrian_count = row['pedestrian_count']
#         current_time = datetime.strptime(row['time'], '%Y-%m-%dT%H:%M:%S')
#
#         # Update total counts
#         total_vehicle_count += vehicle_count
#         total_pedestrian_count += pedestrian_count
#
#         # Check if the current interval is peak, light, or normal hours
#         if vehicle_count >= peak_vehicle_threshold or pedestrian_count >= peak_pedestrian_threshold:
#             if current_interval_start is None:
#                 current_interval_start = current_time
#             current_interval_end = current_time
#         elif vehicle_count >= normal_vehicle_threshold or pedestrian_count >= normal_pedestrian_threshold:
#             if current_interval_start is None:
#                 current_interval_start = current_time
#             current_interval_end = current_time
#         else:
#             if current_interval_start is not None:
#                 # Store the current interval and reset the interval variables
#                 interval_range = (current_interval_start, current_interval_end)
#                 if vehicle_count >= peak_vehicle_threshold or pedestrian_count >= peak_pedestrian_threshold:
#                     peak_hours_intervals.append(interval_range)
#                 elif vehicle_count >= normal_vehicle_threshold or pedestrian_count >= normal_pedestrian_threshold:
#                     normal_hours_intervals.append(interval_range)
#                 else:
#                     light_hours_intervals.append(interval_range)
#                 current_interval_start = None
#                 current_interval_end = None
#
#     # Handle the case where there's only one record
#     if current_interval_start is not None:
#         interval_range = (current_interval_start, current_interval_end)
#         if vehicle_count >= peak_vehicle_threshold or pedestrian_count >= peak_pedestrian_threshold:
#             peak_hours_intervals.append(interval_range)
#         elif vehicle_count >= normal_vehicle_threshold or pedestrian_count >= normal_pedestrian_threshold:
#             normal_hours_intervals.append(interval_range)
#         else:
#             light_hours_intervals.append(interval_range)
#
#     # Calculate mean vehicle and pedestrian counts
#     mean_vehicle_count = total_vehicle_count / len(traffic_light_data)
#     mean_pedestrian_count = total_pedestrian_count / len(traffic_light_data)
#
#     # Get minimum and maximum times
#     min_time = traffic_light_data['time'].min()
#     max_time = traffic_light_data['time'].max()
#
#     return {
#         'peak_hours_intervals': [(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')) for
#                                  start, end in peak_hours_intervals],
#         'normal_hours_intervals': [(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')) for
#                                    start, end in normal_hours_intervals],
#         'light_hours_intervals': [(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')) for
#                                   start, end in light_hours_intervals],
#         'mean_vehicle_count': mean_vehicle_count,
#         'mean_pedestrian_count': mean_pedestrian_count,
#         'time_min': min_time,
#         'time_max': max_time
#     }
#
#
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
#         # Get statistics for the traffic light
#         stats = categorize_intervals(traffic_light_data)
#
#         return jsonify(stats)
#
#
# if __name__ == '__main__':
#     app.run(debug=True)

import threading
from flask import Flask, jsonify, request
import pandas as pd
from datetime import datetime

app = Flask(__name__)
lock = threading.Lock()

# Sample data
sample_data = [
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

# Convert to DataFrame
df = pd.DataFrame(sample_data)
print(df)

def calculate_statistics(traffic_light_data):
    global df

    # Define thresholds for peak, light, and normal hours
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
        'peak_hours_intervals': [(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')) for start, end in peak_hours_intervals],
        'normal_hours_intervals': [(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')) for start, end in normal_hours_intervals],
        'light_hours_intervals': [(start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')) for start, end in light_hours_intervals],
        'mean_vehicle_count': mean_vehicle_count,
        'mean_pedestrian_count': mean_pedestrian_count,
        'time_min': min_time,
        'time_max': max_time
    }


def update_statistics():
    global df
    threading.Timer(10, update_statistics).start()
    with lock:
        # Group by traffic_light_id and calculate statistics
        stats = df.groupby('traffic_light_id').apply(calculate_statistics)
        print("Updated statistics:")
        for idx, stat in stats.items():
            print(f"Traffic Light ID {idx}:")
            print(stat)
            print()


# Start the thread for updating statistics
update_statistics()


@app.route('/statistics/<int:traffic_light_id>', methods=['GET'])
def statistics(traffic_light_id):
    with lock:
        # Filter data for the specified traffic light
        traffic_light_data = df[df['traffic_light_id'] == traffic_light_id]

        # Check if there are records available for the specified traffic light ID
        if len(traffic_light_data) == 0:
            return jsonify({'message': f'No statistics available for traffic light {traffic_light_id}. Insufficient data.'})

        # Calculate statistics
        stats = calculate_statistics(traffic_light_data)

        # Return the statistics
        return jsonify(stats)


@app.route('/add_data', methods=['POST'])
def add_data():
    data = request.json
    global df
    with lock:
        # Create a DataFrame from the JSON data and specify the index explicitly
        new_data = pd.DataFrame(data, index=range(len(data)))
        df = pd.concat([df, new_data], ignore_index=True)
    return jsonify({'message': 'Data added successfully'}), 200




if __name__ == '__main__':
    app.run(debug=True)
