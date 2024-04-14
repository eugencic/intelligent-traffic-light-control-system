from flask import Flask, jsonify
from datetime import datetime
import threading
import time

app = Flask(__name__)

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


def update_traffic_light_rules(intersection_id):
    global traffic_light_durations

    while True:
        try:
            traffic_stats = traffic_intersections.get(intersection_id)
            if not traffic_stats:
                continue

            current_period = get_current_time_period(traffic_stats)

            green_duration, red_duration = recommend_traffic_light_duration(traffic_stats, current_period)

            traffic_light_durations[intersection_id] = {"green_duration": green_duration, "red_duration": red_duration}

            print(
                f"Traffic Light Rules Updated - Intersection {intersection_id}: Green: {green_duration} seconds, Red: {red_duration} seconds")

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
        green_duration = 45
        red_duration = 20
    else:
        green_duration = 30
        red_duration = 15

    return green_duration, red_duration


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
    for intersection_id in traffic_intersections:
        update_thread = threading.Thread(target=update_traffic_light_rules, args=(intersection_id,))
        update_thread.daemon = True
        update_thread.start()

    app.run(debug=True)
