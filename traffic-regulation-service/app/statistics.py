import requests
import threading
import time

from app.cache import *

lock = threading.Lock()


def update_statistics():
    while True:
        try:
            for intersection_id in traffic_intersection_data:
                url = f"{traffic_analytics_service_address}/get_statistics/{intersection_id}"
                response = requests.get(url)

                if response.status_code == 200:
                    updated_stats = response.json()
                    # print("New statistics:", intersection_id, updated_stats)
                    with lock:
                        traffic_intersection_data[intersection_id] = updated_stats

                    # print(f"Updated statistics for Intersection {intersection_id}")
                else:
                    print(f"Failed to fetch statistics for Intersection {intersection_id}")

        except Exception as e:
            print(f"Error updating statistics: {str(e)}")

        time.sleep(15)
