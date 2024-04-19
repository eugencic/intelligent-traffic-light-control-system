# Traffic Regulation Service

## Endpoints:

- Add traffic record for an intersection:

  ```
  POST "http://localhost:7000/add_traffic_record"
  [{
        "time": "2000-01-01T01:01:01",
        "vehicle_count": 1,
        "pedestrian_count": 1,
        "traffic_light_id": 1
  }]
  ```
  
- Get traffic rules of a traffic intersection:

  ```
  GET "http://localhost:7000/get_traffic_rules/1"
  ```
