import time

from app.utils import *


def update_traffic_light_rules(intersection_id):
    while True:
        try:
            traffic_stats = traffic_intersection_data.get(intersection_id)
            if not traffic_stats:
                continue

            current_period = get_current_time_period(traffic_stats)

            if emergency_rules.get(intersection_id, False):
                green_duration = 30
                red_duration = 20
            else:
                green_duration, red_duration = recommend_traffic_light_duration(current_period)

            traffic_light_rules[intersection_id] = {"green_duration": green_duration, "red_duration": red_duration}

            print(
                f"Traffic Light Rules Updated - Intersection {intersection_id}: Green: {green_duration} seconds, Red: {red_duration} seconds\n")

        except Exception as e:
            print(f"Error updating traffic light rules for Intersection {intersection_id}: {str(e)}")

        time.sleep(10)
