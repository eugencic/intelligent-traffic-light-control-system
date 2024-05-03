# traffic_analytics_service_address = "http://localhost:8000"
traffic_analytics_service_address = "http://traffic-analytics-service:8000"

traffic_intersection_data = {
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
    },
    3: {
        "light_hours_intervals": [],
        "mean_pedestrian_count": 10.0,
        "mean_vehicle_count": 20.6,
        "normal_hours_intervals": [
            [
                "2024-03-16T09:50:00",
                "2024-03-16T09:50:00"
            ]
        ],
        "peak_hours_intervals": [
            [
                "2024-03-16T10:00:00",
                "2024-03-16T10:30:00"
            ]
        ],
        "time_max": "2024-03-16T10:30:00",
        "time_min": "2024-03-16T09:50:00"
    }
}

traffic_light_rules = {}
emergency_rules = {}
