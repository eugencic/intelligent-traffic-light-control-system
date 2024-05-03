from datetime import datetime
import threading

from core.cache import *

lock = threading.Lock()


def get_current_time_period(intersection_data):
    current_datetime = datetime.now()

    light_intervals = [(datetime.strptime(start, "%Y-%m-%dT%H:%M:%S"), datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")) for
                       start, end in intersection_data["light_hours_intervals"]]

    for start, end in light_intervals:
        if start <= current_datetime <= end:
            return "light"

    normal_intervals = [(datetime.strptime(start, "%Y-%m-%dT%H:%M:%S"), datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")) for
                        start, end in intersection_data.get("normal_hours_intervals", [])]

    for start, end in normal_intervals:
        if start <= current_datetime <= end:
            return "normal"

    peak_intervals = [(datetime.strptime(start, "%Y-%m-%dT%H:%M:%S"), datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")) for
                      start, end in intersection_data.get("peak_hours_intervals", [])]

    for start, end in peak_intervals:
        if start <= current_datetime <= end:
            return "peak"

    return "normal"


def recommend_traffic_light_duration(current_period):
    if current_period == "peak":
        green_duration = 40
        red_duration = 20
    elif current_period == "light":
        green_duration = 20
        red_duration = 20
    else:
        green_duration = 30
        red_duration = 20

    return green_duration, red_duration


def process_real_time_data(data):
    try:
        vehicle_count = data["vehicle_count"]
        pedestrian_count = data["pedestrian_count"]
        traffic_light_id = data["traffic_light_id"]

        with lock:
            if (vehicle_count > 2 * traffic_intersection_data[traffic_light_id]["mean_vehicle_count"]) or (
                    pedestrian_count > 2 * traffic_intersection_data[traffic_light_id]["mean_pedestrian_count"]):
                emergency_rules[traffic_light_id] = True
            else:
                emergency_rules[traffic_light_id] = False
                current_stats = traffic_intersection_data[traffic_light_id]
                current_period = get_current_time_period(current_stats)
                green_duration, red_duration = recommend_traffic_light_duration(current_period)

                traffic_light_rules[traffic_light_id] = {"green_duration": green_duration,
                                                         "red_duration": red_duration}

        print(f"New Real Time Data - Intersection {traffic_light_id}\n")

    except Exception as e:
        print(f"Error processing real-time traffic data: {str(e)}")
