# Gateway

## Endpoints:

- Add traffic record for an intersection:

  ```
  POST "http://localhost:5000/gateway/add_traffic_record"
  [{
        "time": "2000-01-01T01:01:01",
        "vehicle_count": 1,
        "pedestrian_count": 1,
        "traffic_light_id": 1
  }]
  ```
  
- Get traffic intersection information:

  ```
  GET "http://localhost:5000/gateway/get_intersection_info"
  ```
  