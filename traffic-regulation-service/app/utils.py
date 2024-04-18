from datetime import datetime
import threading

from app.cache import *

lock = threading.Lock()


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


def recommend_traffic_light_duration(current_period):
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
        vehicle_count = data["vehicle_count"]
        pedestrian_count = data["pedestrian_count"]
        traffic_light_id = data["traffic_light_id"]

        with lock:
            if (vehicle_count > 2 * traffic_intersection_data[traffic_light_id]["mean_vehicle_count"]) or (
                    pedestrian_count > 2 * traffic_intersection_data[traffic_light_id]["mean_pedestrian_count"]):
                with lock:
                    emergency_rules[traffic_light_id] = True
                    green_duration = 30
                    red_duration = 20
            else:
                with lock:
                    emergency_rules[traffic_light_id] = False
                    current_stats = traffic_intersection_data[traffic_light_id]
                    current_period = get_current_time_period(current_stats)
                    green_duration, red_duration = recommend_traffic_light_duration(current_period)

                with lock:
                    traffic_light_rules[traffic_light_id] = {"green_duration": green_duration,
                                                             "red_duration": red_duration}

        print(f"Traffic Light Rules Updated Based on Real Time Data - Intersection {traffic_light_id}: "
              f"Green: {green_duration} seconds, Red: {red_duration} seconds\n")

    except Exception as e:
        print(f"Error processing real-time traffic data: {str(e)}")
