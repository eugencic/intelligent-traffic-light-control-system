import requests
import threading
import time

from app.core.cache import *

lock = threading.Lock()


def update_statistics():
    while True:
        try:
            for intersection_id in traffic_intersection_data:
                url = f"{traffic_analytics_service_address}/get_statistics/{intersection_id}"
                response = requests.get(url)

                if response.status_code == 200:
                    updated_stats = response.json()

                    with lock:
                        traffic_intersection_data[intersection_id] = updated_stats
                else:
                    print(f"Failed to fetch statistics for Intersection {intersection_id}")

            print("Updating Statistics...\n")
        except Exception as e:
            print(f"Error updating statistics: {str(e)}")

        time.sleep(20)
