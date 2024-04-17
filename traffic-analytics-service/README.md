# Traffic Analytics Service

## Endpoints:

- Add traffic record for an intersection:

  ```
  POST "http://localhost:8000/add_traffic_record"
  [{
        "time": "2000-01-01T01:01:01",
        "vehicle_count": 1,
        "pedestrian_count": 1,
        "traffic_light_id": 1
  }]
  ```
  
- Get statistics of a traffic intersection:

  ```
  GET "http://localhost:8000/get_statistics/1"
  ```
  
- Get predictions of a traffic intersection on a specified time:

  ```
  GET "http://localhost:8000/get_predictions/1?hour=12&minute=10"
  ```
  