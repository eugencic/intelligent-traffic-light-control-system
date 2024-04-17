import requests
from flask import Flask, jsonify, request
from datetime import datetime
import threading
import time


app = Flask(__name__)

lock_traffic = threading.Lock()
lock_light_durations = threading.Lock()
lock_emergency_rules = threading.Lock()

traffic_intersections = {
    1: {
        "light_hours_intervals": [
            ["2024-03-16T08:00:00", "2024-03-16T08:10:00"]
        ],
        "mean_pedestrian_count": 6.2,
        "mean_vehicle_count": 15.0,
        "normal_hours_intervals": [
            ["2024-03-16T08:30:00", "2024-03-16T08:40:00"]
        ],
        "peak_hours_intervals": [],
        "time_max": "2024-03-16T08:40:00",
        "time_min": "2024-03-16T08:00:00"
    },
    2: {
        "light_hours_intervals": [],
        "mean_pedestrian_count": 10.0,
        "mean_vehicle_count": 30.4,
        "normal_hours_intervals": [],
        "peak_hours_intervals": [
            ["2024-03-16T08:50:00", "2024-03-16T09:30:00"]
        ],
        "time_max": "2024-03-16T09:30:00",
        "time_min": "2024-03-16T08:50:00"
    }
}

traffic_light_durations = {}
emergency_rules = {}


def update_statistics():
    while True:
        try:
            for intersection_id in traffic_intersections:
                url = f"http://127.0.0.1:8000/get_statistics/{intersection_id}"
                response = requests.get(url)

                if response.status_code == 200:
                    updated_stats = response.json()
                    print("New statistics:", intersection_id, updated_stats)
                    with lock_traffic:
                        traffic_intersections[intersection_id] = updated_stats

                    # print(f"Updated statistics for Intersection {intersection_id}")
                else:
                    print(f"Failed to fetch statistics for Intersection {intersection_id}")

        except Exception as e:
            print(f"Error updating statistics: {str(e)}")

        time.sleep(15)


def update_traffic_light_rules(intersection_id):
    global traffic_light_durations

    while True:
        try:
            traffic_stats = traffic_intersections.get(intersection_id)
            if not traffic_stats:
                continue

            current_period = get_current_time_period(traffic_stats)

            if emergency_rules.get(intersection_id, False):

                green_duration = 30
                red_duration = 20
            else:
                green_duration, red_duration = recommend_traffic_light_duration(traffic_stats, current_period)

            traffic_light_durations[intersection_id] = {"green_duration": green_duration, "red_duration": red_duration}

            print(
                f"Traffic Light Rules Updated - Intersection {intersection_id}: Green: {green_duration} seconds, Red: {red_duration} seconds\n")

        except Exception as e:
            print(f"Error updating traffic light rules for Intersection {intersection_id}: {str(e)}")

        time.sleep(10)


def get_current_time_period(intersection_data):
    current_datetime = datetime.now()

    light_intervals = [(datetime.strptime(start, "%Y-%m-%dT%H:%M:%S"), datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")) for
                       start, end in intersection_data["light_hours_intervals"]]
    normal_intervals = [(datetime.strptime(start, "%Y-%m-%dT%H:%M:%S"), datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")) for
                        start, end in intersection_data["normal_hours_intervals"]]
    peak_intervals = [(datetime.strptime(start, "%Y-%m-%dT%H:%M:%S"), datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")) for
                      start, end in intersection_data["peak_hours_intervals"]]

    if any(start <= current_datetime <= end for start, end in peak_intervals):
        return "peak"
    elif any(start <= current_datetime <= end for start, end in normal_intervals):
        return "normal"
    elif any(start <= current_datetime <= end for start, end in light_intervals):
        return "light"
    else:
        return "normal"


def recommend_traffic_light_duration(traffic_stats, current_period):
    if current_period == "peak":
        green_duration = 60
        red_duration = 30
    elif current_period == "light":
        green_duration = 20
        red_duration = 20
    else:
        green_duration = 30
        red_duration = 15

    return green_duration, red_duration


def process_real_time_data(data):
    try:
        time = data["time"]
        vehicle_count = data["vehicle_count"]
        pedestrian_count = data["pedestrian_count"]
        traffic_light_id = data["traffic_light_id"]

        with lock_emergency_rules:
            if (vehicle_count > 2 * traffic_intersections[traffic_light_id]["mean_vehicle_count"]) or (
                    pedestrian_count > 2 * traffic_intersections[traffic_light_id]["mean_pedestrian_count"]):
                with lock_light_durations:
                    emergency_rules[traffic_light_id] = True
                    green_duration = 30
                    red_duration = 20
            else:
                with lock_light_durations:
                    emergency_rules[traffic_light_id] = False
                    current_stats = traffic_intersections[traffic_light_id]
                    current_period = get_current_time_period(current_stats)
                    green_duration, red_duration = recommend_traffic_light_duration(current_stats, current_period)

                with lock_light_durations:
                    traffic_light_durations[traffic_light_id] = {"green_duration": green_duration,
                                                                 "red_duration": red_duration}

        print(f"Traffic Light Rules Updated Based on Real Time Data - Intersection {traffic_light_id}: Green: {green_duration} seconds, Red: {red_duration} seconds\n")

    except Exception as e:
        print(f"Error processing real-time traffic data: {str(e)}")


@app.route("/update_traffic_data", methods=["POST"])
def update_traffic_data():
    try:
        data_list = request.get_json()
        if not isinstance(data_list, list) or len(data_list) == 0:
            return jsonify({"error": "Invalid data format. Expected a non-empty list of traffic data."}), 400

        data = data_list[0]
        print(data)

        required_keys = ['time', 'vehicle_count', 'pedestrian_count', 'traffic_light_id']
        if not all(key in data for key in required_keys):
            print(f"Missing keys in data: {set(required_keys) - set(data.keys())}")  # Debugging: Print missing keys
            return jsonify({"error": "Invalid data format. Missing required keys."}), 400

        process_real_time_data(data)

        return jsonify({"message": "Traffic data processed successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/traffic_intersection/<int:intersection_id>/recommend_light_durations", methods=["GET"])
def get_recommendations(intersection_id):
    try:
        traffic_stats = traffic_intersections.get(intersection_id)
        if not traffic_stats:
            return jsonify({"error": "Intersection not found"}), 404

        if intersection_id not in traffic_light_durations:
            return jsonify({"error": "Traffic light durations not available yet"}), 404

        light_durations = traffic_light_durations[intersection_id]
        return jsonify(light_durations), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    stats_update_thread = threading.Thread(target=update_statistics)
    stats_update_thread.daemon = True
    stats_update_thread.start()

    for intersection_id in traffic_intersections:
        update_thread = threading.Thread(target=update_traffic_light_rules, args=(intersection_id,))
        update_thread.daemon = True
        update_thread.start()

    app.run(host="0.0.0.0", port=7000, debug=True)
