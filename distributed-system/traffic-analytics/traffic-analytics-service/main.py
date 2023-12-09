import grpc
from concurrent import futures
import psycopg2.pool
from dateutil.relativedelta import relativedelta
from datetime import datetime
import threading
import requests
import time
import os
from prometheus_client import start_http_server, Counter, Enum
import traffic_analytics_pb2
import traffic_analytics_pb2_grpc


requests_counter = Counter('t_an_requests_total', 'Requests', ['endpoint', 'message'])
timeouts_counter = Counter('t_an_timeouts_total', 'Timeouts')
success_counter = Counter('t_an_successful_requests_total', 'Successful Requests')
error_counter = Counter('t_an_errors_total', 'Errors')
database_state = Enum('t_an_database_state', 'Database State', states=['connected', 'not connected'])
register_state = Enum('t_an_register_state', 'Register State', states=['registered', 'not registered'])


def register_service(service_name, service_host, service_port, service_discovery_endpoint):
    service_data = {
        "name": service_name,
        "host": service_host,
        "port": service_port,
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            f"{service_discovery_endpoint}/register_service",
            json=service_data,
            headers=headers,
        )
        if response.status_code == 201:
            register_state.state('registered')
            print(f"Registered {service_name} with service discovery")
        else:
            register_state.state('not registered')
            print(f"Failed to register {service_name} with service discovery: {response.status_code}")
    except Exception as e:
        register_state.state('not registered')
        print(f"Error while registering {service_name}: {str(e)}")


create_traffic_data_table_query = """
CREATE TABLE IF NOT EXISTS traffic_data (
    id SERIAL PRIMARY KEY,
    intersection_id integer,
    date date,
    time time without time zone,
    signal_status_1 character varying(255),
    vehicle_count integer,
    incident boolean
);
"""

create_traffic_analytics_table_query = """
CREATE TABLE IF NOT EXISTS traffic_analytics (
    intersection_id integer,
    date date,
    average_vehicle_count double precision,
    average_incidents double precision,
    analytics_type character varying(10),
    CONSTRAINT unique_intersection_date_type UNIQUE (intersection_id, date, analytics_type)
);
"""

create_data_analytics_table_query = """
CREATE TABLE IF NOT EXISTS data_analytics (
    id serial PRIMARY KEY,
    intersection_id integer,
    message text
);
"""

try:
    conn = psycopg2.connect(
        dbname='traffic-analytics-db',
        user='postgres',
        password='397777',
        host='traffic-analytics-database',
        # host='localhost',
        # port='5433'
    )
    database_state.state('connected')
    print("Connection to the traffic analytics database is successful")
    cursor = conn.cursor()
    cursor.execute(create_traffic_data_table_query)
    conn.commit()
    cursor.execute(create_traffic_analytics_table_query)
    conn.commit()
    cursor.execute(create_data_analytics_table_query)
    conn.commit()
    print("All necessary tables are created")
    cursor.close()
    conn.close()
except (Exception,) as e:
    database_state.state('not connected')
    print(f"Error connecting to the traffic analytics database")

db_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dbname='traffic-analytics-db',
    user='postgres',
    password='397777',
    host='traffic-analytics-database',
    # host='localhost',
    # port='5433'
)
print("Connection pool created")

CRITICAL_LOAD_THRESHOLD = 60


class TrafficAnalyticsServicer(traffic_analytics_pb2_grpc.TrafficAnalyticsServicer):
    def __init__(self):
        self.request_count = 0
        self.reset_interval = 1
        self.reset_thread = threading.Thread(target=self.reset_counter, daemon=True)
        self.lock = threading.Lock()

    def increment_request_count(self):
        with self.lock:
            self.request_count += 1

    def check_critical_load(self):
        if self.request_count > CRITICAL_LOAD_THRESHOLD:
            print(f"ALERT! Critical load exceeded: {self.request_count} requests per second")

    def reset_counter(self):
        while True:
            time.sleep(self.reset_interval)
            with self.lock:
                self.request_count = 0

    def start_reset_thread(self):
        self.reset_thread.start()

    def ReceiveDataForAnalytics(self, request, context):
        self.increment_request_count()
        self.check_critical_load()
        requests_counter.labels('receive_data_for_analytics', 'New request for receiving data').inc()
        print("New request for receiving data")
        timeout_seconds = 2
        timeout_event = threading.Event()

        def timeout_handler():
            timeout_event.set()

        timer_thread = threading.Timer(timeout_seconds, timeout_handler)
        timer_thread.start()
        # time.sleep(3)
        if timeout_event.is_set():
            timeouts_counter.inc()
            print("Request timed out")
            context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
            context.set_details("Request timed out")
            return traffic_analytics_pb2.TrafficDataForAnalyticsReceiveResponse(message="Request timed out")
        try:
            conn = db_pool.getconn()
            with conn.cursor() as cursor:
                # time.sleep(3)
                if timeout_event.is_set():
                    timeouts_counter.inc()
                    print("Request timed out")
                    context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
                    context.set_details("Request timed out")
                    return traffic_analytics_pb2.TrafficDataForAnalyticsReceiveResponse(message="Request timed out")
                insert_query = """
                    INSERT INTO traffic_data (intersection_id, date, time, signal_status_1, vehicle_count, incident)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                cursor.execute(insert_query, (
                    request.intersection_id,
                    request.date,
                    request.time,
                    request.signal_status_1,
                    request.vehicle_count,
                    request.incident,
                ))
                conn.commit()
                timer_thread.cancel()
            response = traffic_analytics_pb2.TrafficDataForAnalyticsReceiveResponse()
            success_counter.inc()
            response.message = f"Traffic data for intersection nr.{request.intersection_id} received successfully"
            db_pool.putconn(conn)
        except (Exception,) as e:
            error_counter.inc()
            context.set_code(grpc.StatusCode.INTERNAL)
            response = traffic_analytics_pb2.TrafficDataForAnalyticsReceiveResponse()
            response.message = f"Error saving traffic data: {str(e)}"
        except grpc.RpcError as e:
            error_counter.inc()
            print(f"RPC error: {str(e)}")
            context.set_code(e)
            context.set_details(str(e))
            response = traffic_analytics_pb2.TrafficDataForAnalyticsReceiveResponse(message=str(e))
        return response

    def AddDataAnalytics(self, request, context):
        self.increment_request_count()
        self.check_critical_load()
        requests_counter.labels('add_data_analytics', 'New request to add data').inc()
        print("New request to add data")
        try:
            conn = db_pool.getconn()
            with conn.cursor() as cursor:
                select_query = "SELECT * FROM data_analytics WHERE intersection_id = %s"
                cursor.execute(select_query, (request.intersection_id,))
                existing_row = cursor.fetchone()
                if existing_row:
                    update_query = """
                        UPDATE data_analytics
                        SET message = %s
                        WHERE intersection_id = %s
                    """
                    cursor.execute(update_query, (request.message, request.intersection_id))
                else:
                    insert_query = """
                        INSERT INTO data_analytics (intersection_id, message)
                        VALUES (%s, %s)
                    """
                    cursor.execute(insert_query, (request.intersection_id, request.message))
                conn.commit()
            success_counter.inc()
            response = traffic_analytics_pb2.AddDataAnalyticsResponse()
            response.message = f"Data analytics added for intersection nr.{request.intersection_id}"
            db_pool.putconn(conn)
        except (Exception,) as e:
            error_counter.inc()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error adding data analytics: {str(e)}")
            response = traffic_analytics_pb2.AddDataAnalyticsResponse()
            response.message = f"Error adding data analytics: {str(e)}"
        except grpc.RpcError as e:
            error_counter.inc()
            print(f"RPC error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            response = traffic_analytics_pb2.AddDataAnalyticsResponse(message=str(e))
        return response

    def DeleteDataAnalytics(self, request, context):
        self.increment_request_count()
        self.check_critical_load()
        requests_counter.labels('delete_data_analytics', 'New request to delete data').inc()
        print("New request to delete data")
        try:
            conn = db_pool.getconn()
            with conn.cursor() as cursor:
                delete_query = """
                    DELETE FROM data_analytics
                    WHERE intersection_id = %s
                    """
                cursor.execute(delete_query, (request.intersection_id,))
                conn.commit()
            success_counter.inc()
            response = traffic_analytics_pb2.DeleteDataAnalyticsResponse()
            response.message = f"Data analytics deleted for intersection nr.{request.intersection_id}"
            db_pool.putconn(conn)
        except (Exception,) as e:
            error_counter.inc()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error deleting data analytics: {str(e)}")
            response = traffic_analytics_pb2.DeleteDataAnalyticsResponse()
            response.message = f"Error deleting data analytics: {str(e)}"
        except grpc.RpcError as e:
            error_counter.inc()
            print(f"RPC error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            response = traffic_analytics_pb2.DeleteDataAnalyticsResponse(message=str(e))
        return response

    def GetTodayStatistics(self, request, context):
        self.increment_request_count()
        self.check_critical_load()
        requests_counter.labels('today_statistics', 'New request for today statistics').inc()
        print("New request for daily statistics")
        timeout_seconds = 2
        timeout_event = threading.Event()

        def timeout_handler():
            timeout_event.set()

        timer_thread = threading.Timer(timeout_seconds, timeout_handler)
        timer_thread.start()
        # time.sleep(3)
        if timeout_event.is_set():
            timeouts_counter.inc()
            print("Request timed out")
            context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
            context.set_details("Request timed out")
            return traffic_analytics_pb2.TrafficDataForAnalyticsReceiveResponse(message="Request timed out")
        try:
            conn = db_pool.getconn()
            with conn.cursor() as cursor:
                query = """
                SELECT vehicle_count, time, incident from traffic_data
                WHERE intersection_id = %s
                AND date = %s
                """
                cursor.execute(query, (request.intersection_id, datetime.now().strftime('%Y-%m-%d')))
                results = cursor.fetchall()
                print("Retrieved data:", results)
                times = [result[1] for result in results]
                if not times:
                    response = traffic_analytics_pb2.TrafficAnalyticsResponse()
                    response.intersection_id = request.intersection_id
                    response.timestamp = datetime.now().isoformat()
                    response.average_vehicle_count = 0
                    response.peak_hours = 'No data available'
                    response.average_incidents = 0
                    return response
                total_vehicle_count = 0
                total_incidents = 0
                for result in results:
                    total_vehicle_count += result[0]
                    if result[2]:
                        total_incidents += 1
                    sorted_times = sorted(times)
                peak_start = sorted_times[0].strftime("%I:%M %p")
                peak_end = sorted_times[-1].strftime("%I:%M %p")
                peak_hours = f"{peak_start} - {peak_end}"
                average_vehicle_count = round(total_vehicle_count / len(results), 3) if len(results) > 0 else 0.0
                average_incidents = round(total_incidents / len(results), 3) if len(results) > 0 else 0.0
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO traffic_analytics (
                    intersection_id, 
                    date, 
                    average_vehicle_count, 
                    average_incidents, 
                    analytics_type
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (intersection_id, date, analytics_type)
                    DO UPDATE SET
                      average_vehicle_count = EXCLUDED.average_vehicle_count,
                      average_incidents = EXCLUDED.average_incidents;
                """
                try:
                    cursor.execute(query, (
                        request.intersection_id,
                        datetime.now().strftime("%Y-%m-%d"),
                        average_vehicle_count,
                        average_incidents,
                        'Daily'
                    ))
                    conn.commit()
                    timer_thread.cancel()
                except Exception as e:
                    error_counter.inc()
                    print("Error inserting data into traffic_analytics:", e)
            response = traffic_analytics_pb2.TrafficAnalyticsResponse()
            response.intersection_id = request.intersection_id
            response.timestamp = datetime.now().isoformat()
            response.average_vehicle_count = average_vehicle_count
            response.peak_hours = peak_hours
            response.average_incidents = average_incidents
            db_pool.putconn(conn)
            return response
        except (Exception,) as e:
            error_counter.inc()
            context.set_code(grpc.StatusCode.INTERNAL)
            print(f"Error: {str(e)}")
            response = traffic_analytics_pb2.TrafficAnalyticsResponse()
            response.intersection_id = 0
            response.timestamp = '0'
            response.average_vehicle_count = 0
            response.peak_hours = '0'
            response.average_incidents = 0
            return response
        except grpc.RpcError as e:
            error_counter.inc()
            print(f"RPC error: {str(e)}")
            context.set_code(e)
            context.set_details(str(e))
            response = traffic_analytics_pb2.TrafficDataForAnalyticsReceiveResponse(message=str(e))
            return response

    def GetLastWeekStatistics(self, request, context):
        self.increment_request_count()
        self.check_critical_load()
        requests_counter.labels('last_week_statistics', 'New request for last week statistics').inc()
        print("New request for weekly statistics")
        timeout_seconds = 2
        timeout_event = threading.Event()

        def timeout_handler():
            timeout_event.set()

        timer_thread = threading.Timer(timeout_seconds, timeout_handler)
        timer_thread.start()
        # time.sleep(3)
        if timeout_event.is_set():
            timeouts_counter.inc()
            print("Request timed out")
            context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
            context.set_details("Request timed out")
            return traffic_analytics_pb2.TrafficDataForAnalyticsReceiveResponse(message="Request timed out")
        try:
            conn = db_pool.getconn()
            with conn.cursor() as cursor:
                end_date = datetime.now().date()
                start_date = end_date - relativedelta(weeks=1)
                insert_date = end_date
                query = """
                SELECT vehicle_count, time, incident from traffic_data
                WHERE intersection_id = %s
                AND date >= %s 
                AND date <= %s
                """
                cursor.execute(query, (
                    request.intersection_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
                ))
                results = cursor.fetchall()
                print("Retrieved data for the last week:", results)
                times = [result[1] for result in results]
                if not times:
                    response = traffic_analytics_pb2.TrafficAnalyticsResponse()
                    response.intersection_id = request.intersection_id
                    response.timestamp = datetime.now().isoformat()
                    response.average_vehicle_count = 0
                    response.peak_hours = 'No data available'
                    response.average_incidents = 0
                    return response
                total_vehicle_count = 0
                total_incidents = 0
                for result in results:
                    total_vehicle_count += result[0]
                    if result[2]:
                        total_incidents += 1
                    sorted_times = sorted(times)
                peak_start = sorted_times[0].strftime("%I:%M %p")
                peak_end = sorted_times[-1].strftime("%I:%M %p")
                peak_hours = f"{peak_start} - {peak_end}"
                average_vehicle_count = round(total_vehicle_count / len(results), 3) if len(results) > 0 else 0.0
                average_incidents = round(total_incidents / len(results), 3) if len(results) > 0 else 0.0
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO traffic_analytics (
                        intersection_id, 
                        date, 
                        average_vehicle_count, 
                        average_incidents, 
                        analytics_type
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (intersection_id, date, analytics_type)
                    DO UPDATE SET
                        average_vehicle_count = EXCLUDED.average_vehicle_count,
                        average_incidents = EXCLUDED.average_incidents;
                """
                try:
                    cursor.execute(query, (
                        request.intersection_id,
                        insert_date.strftime("%Y-%m-%d"),
                        average_vehicle_count,
                        average_incidents,
                        'Weekly'
                    ))
                    conn.commit()
                    timer_thread.cancel()
                except Exception as e:
                    error_counter.inc()
                    print("Error inserting data into traffic_analytics:", e)
            response = traffic_analytics_pb2.TrafficAnalyticsResponse()
            response.intersection_id = request.intersection_id
            response.timestamp = datetime.now().isoformat()
            response.average_vehicle_count = average_vehicle_count
            response.peak_hours = peak_hours
            response.average_incidents = average_incidents
            db_pool.putconn(conn)
            return response
        except (Exception, ) as e:
            error_counter.inc()
            context.set_code(grpc.StatusCode.INTERNAL)
            print(f"Error: {str(e)}")
            response = traffic_analytics_pb2.TrafficAnalyticsResponse()
            response.intersection_id = 0
            response.timestamp = '0'
            response.average_vehicle_count = 0
            response.peak_hours = '0'
            response.average_incidents = 0
            return response
        except grpc.RpcError as e:
            error_counter.inc()
            print(f"RPC error: {str(e)}")
            context.set_code(e)
            context.set_details(str(e))
            response = traffic_analytics_pb2.TrafficDataForAnalyticsReceiveResponse(message=str(e))
            return response

    def GetNextWeekPredictions(self, request, context):
        self.increment_request_count()
        self.check_critical_load()
        requests_counter.labels('next_week_predictions', 'New request for next week predictions').inc()
        print("New request for next week predictions")
        timeout_seconds = 2
        timeout_event = threading.Event()

        def timeout_handler():
            timeout_event.set()

        timer_thread = threading.Timer(timeout_seconds, timeout_handler)
        timer_thread.start()
        # time.sleep(3)
        if timeout_event.is_set():
            timeouts_counter.inc()
            print("Request timed out")
            context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
            context.set_details("Request timed out")
            return traffic_analytics_pb2.TrafficDataForAnalyticsReceiveResponse(message="Request timed out")
        try:
            conn = db_pool.getconn()
            with conn.cursor() as cursor:
                end_date = datetime.now().date()
                start_date = end_date - relativedelta(weeks=1)
                insert_date = end_date
                query = """
                SELECT vehicle_count, time, incident from traffic_data
                WHERE intersection_id = %s
                AND date >= %s 
                AND date <= %s
                """
                cursor.execute(query, (
                    request.intersection_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
                ))
                results = cursor.fetchall()
                print("Retrieved data for the last week for predictions:", results)
                times = [result[1] for result in results]
                if not times:
                    response = traffic_analytics_pb2.TrafficAnalyticsResponse()
                    response.intersection_id = request.intersection_id
                    response.timestamp = datetime.now().isoformat()
                    response.average_vehicle_count = 0
                    response.peak_hours = 'No data available'
                    response.average_incidents = 0
                    return response
                total_vehicle_count = 0
                total_incidents = 0
                for result in results:
                    total_vehicle_count += result[0]
                    if result[2]:
                        total_incidents += 1
                    sorted_times = sorted(times)
                peak_start = sorted_times[0].strftime("%I:%M %p")
                peak_end = sorted_times[-1].strftime("%I:%M %p")
                peak_hours = f"{peak_start} - {peak_end}"
                average_vehicle_count = round(total_vehicle_count / len(results), 3) if len(results) > 0 else 0.0
                average_incidents = round(total_incidents / len(results), 3) if len(results) > 0 else 0.0
                predicted_average_vehicle_count = average_vehicle_count + 10
                predicted_average_incidents = average_incidents + 10
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO traffic_analytics (
                        intersection_id, 
                        date, 
                        average_vehicle_count, 
                        average_incidents, 
                        analytics_type
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (intersection_id, date, analytics_type)
                    DO UPDATE SET
                        average_vehicle_count = EXCLUDED.average_vehicle_count,
                        average_incidents = EXCLUDED.average_incidents;
                """
                try:
                    cursor.execute(query, (
                        request.intersection_id,
                        insert_date.strftime("%Y-%m-%d"),
                        predicted_average_vehicle_count,
                        predicted_average_incidents,
                        'Prediction'
                    ))
                    conn.commit()
                    timer_thread.cancel()
                except Exception as e:
                    error_counter.inc()
                    print("Error inserting data into traffic_analytics:", e)
            response = traffic_analytics_pb2.TrafficAnalyticsResponse()
            response.intersection_id = request.intersection_id
            response.timestamp = datetime.now().isoformat()
            response.average_vehicle_count = predicted_average_vehicle_count
            response.peak_hours = peak_hours
            response.average_incidents = predicted_average_incidents
            db_pool.putconn(conn)
            return response
        except (Exception,) as e:
            error_counter.inc()
            context.set_code(grpc.StatusCode.INTERNAL)
            print(f"Error: {str(e)}")
            response = traffic_analytics_pb2.TrafficAnalyticsResponse()
            response.intersection_id = 0
            response.timestamp = '0'
            response.average_vehicle_count = 0
            response.peak_hours = '0'
            response.average_incidents = 0
            return response
        except grpc.RpcError as e:
            error_counter.inc()
            print(f"RPC error: {str(e)}")
            context.set_code(e)
            context.set_details(str(e))
            response = traffic_analytics_pb2.TrafficDataForAnalyticsReceiveResponse(message=str(e))
            return response

    def TrafficAnalyticsServiceStatus(self, request, context):
        self.increment_request_count()
        self.check_critical_load()
        print("New request for service status")
        timeout_seconds = 2
        timeout_event = threading.Event()
        service_name = os.environ.get("SERVICE_NAME", "traffic-analytics-service-1")
        service_port = int(os.environ.get("SERVICE_PORT", 7071))

        def timeout_handler():
            timeout_event.set()

        timer_thread = threading.Timer(timeout_seconds, timeout_handler)
        timer_thread.start()
        # time.sleep(3)
        if timeout_event.is_set():
            timeouts_counter.inc()
            print("Request timed out")
            context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
            context.set_details("Request timed out")
            return traffic_analytics_pb2.TrafficDataForAnalyticsReceiveResponse(
                message="Request timed out")
        try:
            conn = psycopg2.connect(
                dbname='traffic-analytics-db',
                user='postgres',
                password='397777',
                host='traffic-analytics-database'
                # host='localhost',
                # port='5433'
            )
            context.set_code(grpc.StatusCode.OK)
            context.set_details(f"{service_name}:{service_port} is healthy")
            database_state.state('connected')
            success_counter.inc()
            response = traffic_analytics_pb2.TrafficAnalyticsServiceStatusResponse(message=f"{service_name}:"
                                                                                           f"{service_port}: healthy")
            conn.close()
            return response
        except (Exception,) as e:
            error_counter.inc()
            database_state.state('not connected')
            context.set_code(grpc.StatusCode.OK)
            context.set_details(f"{service_name}:{service_port} is unhealthy")
            response = traffic_analytics_pb2.TrafficAnalyticsServiceStatusResponse(message=f"{service_name}:"
                                                                                           f"{service_port}: unhealthy")
            return response
        except grpc.RpcError as e:
            error_counter.inc()
            database_state.state('not connected')
            context.set_code(grpc.StatusCode.OK)
            context.set_details(f"{service_name}:{service_port} is unhealthy")
            response = traffic_analytics_pb2.TrafficAnalyticsServiceStatusResponse(message=f"{service_name}:"
                                                                                           f"{service_port}: unhealthy")
            return response


def start(service_name, service_port, service_discovery_endpoint, prometheus_port):
    register_service(service_name, service_name, service_port, service_discovery_endpoint)
    start_http_server(prometheus_port)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service = TrafficAnalyticsServicer()
    service.start_reset_thread()
    traffic_analytics_pb2_grpc.add_TrafficAnalyticsServicer_to_server(service, server)
    server.add_insecure_port(f"0.0.0.0:{service_port}")
    server.start()
    print(f"{service_name} listening on port {service_port}...")
    server.wait_for_termination()
    service.reset_thread.join()


if __name__ == '__main__':
    start(
        os.environ.get("SERVICE_NAME", "traffic-analytics-service-1"),
        int(os.environ.get("SERVICE_PORT", 7071)),
        os.environ.get("SERVICE_DISCOVERY_ENDPOINT", "http://service-discovery:9090"),
        int(os.environ.get("PROMETHEUS_PORT", 7001))
    )
