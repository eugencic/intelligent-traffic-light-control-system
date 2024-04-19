import time

from app.core.utils import *


def update_traffic_light_rules(intersection_id):
    while True:
        try:
            traffic_stats = traffic_intersection_data.get(intersection_id)
            if not traffic_stats:
                continue

            current_period = get_current_time_period(traffic_stats)

            if emergency_rules.get(intersection_id, False):
                green_duration = 50
                red_duration = 20

                print(
                    f"Traffic Light Rules Updated - Emergency Rules - Intersection {intersection_id}: "
                    f"Green: {green_duration} seconds, Red: {red_duration} seconds\n"
                )
            else:
                green_duration, red_duration = recommend_traffic_light_duration(current_period)
                print(
                    f"Traffic Light Rules Updated - Recommended Rules - Intersection {intersection_id}: "
                    f"Green: {green_duration} seconds, Red: {red_duration} seconds\n"
                )

            traffic_light_rules[intersection_id] = {"green_duration": green_duration, "red_duration": red_duration}
        except Exception as e:
            print(f"Error updating traffic light rules for Intersection {intersection_id}: {str(e)}")

        time.sleep(20)
