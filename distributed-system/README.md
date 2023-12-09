# Intelligent Traffic Light Control System

> **Performed by:** Eugeniu Popa, FAF-202

## Run the application

Before running the application, make sure [Docker](https://www.docker.com/) is installed.  
Type this command in the root folder.

```bash
$ docker compose up --build
```

### System architecture

![Diagram](https://github.com/eugencic/distributed-application-programming/blob/main/docs/system_architecture_diagram.png)

### Data management:

Also check the [Postman collection](https://github.com/eugencic/distributed-application-programming/blob/main/docs).

  - Get status of the gateway:

    ```
    GET http://localhost:6060/get_gateway_status
    ```

  - Get status of the service discovery:

    ```
    GET http://localhost:6060/get_service_discovery_status
    ```

  - Get status of the traffic analytics service:

    ```
    GET http://localhost:6060/get_traffic_analytics_service_status
    ```

  - Send data for analytics (should be accessed first to add some data; the date when the container was created will be considered today's date):

    ```
    POST http://localhost:6060/receive_data_for_analytics
    {
      "intersection_id": 1,
      "signal_status_1": 1,
      "vehicle_count": 5,
      "incident": true,
      "date": "2023-12-07",
      "time": "07:10"
    }
    ```

  - Get today statistics:

    ```
    POST http://localhost:6060/today_statistics
    {
      "intersection_id": 1
    }
    ```

  - Get last week statistics:

    ```
    POST http://localhost:6060/last_week_statistics
    {
      "intersection_id": 1
    }
    ```

  - Get next week predictions:

    ```
    POST http://localhost:6060/next_week_predictions
    {
      "intersection_id": 1
    }
    ```

  - Get status of the traffic regulation service:

    ```
    GET http://localhost:6060/get_traffic_regulation_service_status
    ```

  - Send data for logs (should be accessed first to add some data; the date when the container was created will be considered today's date; in order to make logs, signal_status_1 has to be 1 and vehicle_count > 30, or signal_status_1 has to be 2 and vehicle_count < 5):

    ```
    POST http://localhost:6060/receive_data_for_logs 
    {
      "intersection_id": 1,
      "signal_status_1": 1,
      "vehicle_count": 31,
      "incident": true,
      "date": "2023-12-07",
      "time": "07:10"
    }
    ```

  - Get today control logs:

    ```
    POST http://localhost:6060/today_control_logs
    {
      "intersection_id": 1
    }
    ```

  - Get last week control logs:

    ```
    POST http://localhost:6060/last_week_control_logs
    {
      "intersection_id": 1
    }
    ```

  - Send data for saga transaction:

    ```
    POST http://localhost:6061/add_data
    {
      "intersection_id": 1,
      "message": "Sample message"
    }
    ```

### Technology stack and communication patterns:

- Gateway, service discovery: `Go`
- Traffic analytics and regulation services, load balancers, coordinator: `Python`
- Databases: `PostgreSQL`
- Communication patterns: `REST`, `RPC`
