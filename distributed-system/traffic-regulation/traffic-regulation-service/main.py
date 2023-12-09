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
import traffic_regulation_pb2
import traffic_regulation_pb2_grpc

requests_counter = Counter('t_reg_requests_total', 'Requests', ['endpoint', 'message'])
timeouts_counter = Counter('t_reg_timeouts_total', 'Timeouts')
success_counter = Counter('t_reg_successful_requests_total', 'Successful Requests')
error_counter = Counter('t_reg_errors_total', 'Errors')
database_state = Enum('t_reg_database_state', 'Database State', states=['connected', 'not connected'])
register_state = Enum('t_reg_register_state', 'Register State', states=['registered', 'not registered'])


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
    except (Exception,) as e:
        register_state.state('not registered')
        print(f"Error while registering {service_name}: {str(e)}")


create_traffic_data_table_query = """
CREATE TABLE IF NOT EXISTS traffic_data (
    id serial PRIMARY KEY,
    intersection_id integer,
    date date,
    time time without time zone,
    signal_status character varying(255),
    vehicle_count integer,
    incident boolean
);
"""

create_traffic_logs_table_query = """
CREATE TABLE IF NOT EXISTS traffic_logs (
    log_id serial PRIMARY KEY,
    intersection_id integer,
    date date,
    log_messages text[],
    CONSTRAINT unique_intersection_date UNIQUE (intersection_id, date)
);
"""

create_data_regulation_table_query = """
CREATE TABLE IF NOT EXISTS data_regulation (
    id serial PRIMARY KEY,
    intersection_id integer,
    message text
);
"""

try:
    conn = psycopg2.connect(
        dbname='traffic-regulation-db',
        user='postgres',
        password='397777',
        host='traffic-regulation-database',
        # host='localhost',
        # port='5434'
    )
    database_state.state('connected')
    print("Connection to the traffic regulation database is successful")
    cursor = conn.cursor()
    cursor.execute(create_traffic_data_table_query)
    conn.commit()
    cursor.execute(create_traffic_logs_table_query)
    conn.commit()
    cursor.execute(create_data_regulation_table_query)
    conn.commit()
    print("All necessary tables are created")
    cursor.close()
    conn.close()
except (Exception,) as e:
    database_state.state('not connected')
    print(f"Error connecting to the traffic regulation database")

db_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dbname='traffic-regulation-db',
    user='postgres',
    password='397777',
    host='traffic-regulation-database',
    # host='localhost',
    # port='5434'
)
print("Connection pool created")

CRITICAL_LOAD_THRESHOLD = 60


class TrafficRegulationServicer(traffic_regulation_pb2_grpc.TrafficRegulationServicer):
    def __init__(self):
        self.request_count = 0
        self.reset_interval = 1
        self.reset_thread = threading.Thread(target=self.reset_counter, daemon=True)
        self.lock = threading.Lock()

    def increment_request_count(self):
        with self.lock:
            self.request_count += 1

    def check_critical_load(self):
        if self.request_count >= CRITICAL_LOAD_THRESHOLD:
            print(f"ALERT! Critical load exceeded: {self.request_count} requests per second")

    def reset_counter(self):
        while True:
            time.sleep(self.reset_interval)
            with self.lock:
                self.request_count = 0

    def start_reset_thread(self):
        self.reset_thread.start()

    def ReceiveDataForLogs(self, request, context):
        self.increment_request_count()
        self.check_critical_load()
        requests_counter.labels('receive_data_for_logs', 'New request for receiving data').inc()
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
            return traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(message="Request timed out")
        try:
            conn = db_pool.getconn()
            with conn.cursor() as cursor:
                # time.sleep(3)
                if timeout_event.is_set():
                    timeouts_counter.inc()
                    print("Request timed out")
                    context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
                    context.set_details("Request timed out")
                    return traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(message="Request timed out")
                insert_query = """
                    INSERT INTO traffic_data (intersection_id, date, time, signal_status, vehicle_count, incident)
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
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT log_messages FROM traffic_logs
                    WHERE intersection_id = %s AND date = %s
                    """,
                    (request.intersection_id, request.date),
                )
                existing_logs = cursor.fetchone()
                if existing_logs is not None:
                    existing_log_messages = existing_logs[0]
                else:
                    existing_log_messages = []
                if request.signal_status_1 == 1 and request.vehicle_count > 30:
                    request.signal_status_1 = 2
                    log_message = (f"Traffic light at intersection nr.{request.intersection_id} changed to 'green' due "
                                   f"to high vehicle count")
                    print(log_message)
                    existing_log_messages.append(log_message)
                if request.signal_status_1 == 2 and request.vehicle_count < 5:
                    request.signal_status_1 = 1
                    log_message = (f"Traffic light at intersection nr.{request.intersection_id} changed to 'red' due "
                                   f"to low vehicle count")
                    print(log_message)
                    existing_log_messages.append(log_message)
                cursor.execute(
                    """
                    INSERT INTO traffic_logs (intersection_id, date, log_messages)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (intersection_id, date)
                    DO UPDATE
                    SET log_messages = %s
                    """,
                    (request.intersection_id, request.date, existing_log_messages,
                     existing_log_messages),
                )
                conn.commit()
                timer_thread.cancel()
            response = traffic_regulation_pb2.TrafficDataForLogsReceiveResponse()
            success_counter.inc()
            response.message = f"Traffic data for intersection nr.{request.intersection_id} received successfully"
            db_pool.putconn(conn)
        except (Exception,) as e:
            error_counter.inc()
            context.set_code(grpc.StatusCode.INTERNAL)
            response = traffic_regulation_pb2.TrafficDataForLogsReceiveResponse()
            response.message = f"Error saving traffic data: {str(e)}"
        except grpc.RpcError as e:
            error_counter.inc()
            print(f"RPC error: {str(e)}")
            context.set_code(e)
            context.set_details(str(e))
            response = traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(message=str(e))
        return response

    def AddDataRegulation(self, request, context):
        self.increment_request_count()
        self.check_critical_load()
        requests_counter.labels('add_data_regulation', 'New request to add data').inc()
        print("New request to add data")
        try:
            conn = db_pool.getconn()
            with conn.cursor() as cursor:
                select_query = "SELECT * FROM data_regulation WHERE intersection_id = %s"
                cursor.execute(select_query, (request.intersection_id,))
                existing_row = cursor.fetchone()
                if existing_row:
                    update_query = """
                        UPDATE data_regulation
                        SET message = %s
                        WHERE intersection_id = %s
                    """
                    cursor.execute(update_query, (request.message, request.intersection_id))
                else:
                    insert_query = """
                        INSERT INTO data_regulation (intersection_id, message)
                        VALUES (%s, %s)
                    """
                    cursor.execute(insert_query, (request.intersection_id, request.message))
                conn.commit()
            success_counter.inc()
            response = traffic_regulation_pb2.AddDataRegulationResponse()
            response.message = f"Data regulation added for intersection nr.{request.intersection_id}"
            db_pool.putconn(conn)
        except (Exception,) as e:
            error_counter.inc()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error adding data regulation: {str(e)}")
            response = traffic_regulation_pb2.AddDataRegulationResponse()
            response.message = f"Error adding data regulation: {str(e)}"
        except grpc.RpcError as e:
            error_counter.inc()
            print(f"RPC error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            response = traffic_regulation_pb2.AddDataRegulationResponse(message=str(e))
        return response

    def DeleteDataRegulation(self, request, context):
        self.increment_request_count()
        self.check_critical_load()
        requests_counter.labels('delete_data_regulation', 'New request to delete data').inc()
        print("New request to delete data")
        try:
            conn = db_pool.getconn()
            with conn.cursor() as cursor:
                delete_query = """
                    DELETE FROM data_regulation
                    WHERE intersection_id = %s
                    """
                cursor.execute(delete_query, (request.intersection_id,))
                conn.commit()
            success_counter.inc()
            response = traffic_regulation_pb2.DeleteDataRegulationResponse()
            response.message = f"Data regulation deleted for intersection nr.{request.intersection_id}"
            db_pool.putconn(conn)
        except (Exception,) as e:
            error_counter.inc()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error deleting data regulation: {str(e)}")
            response = traffic_regulation_pb2.DeleteDataRegulationResponse()
            response.message = f"Error deleting data regulation: {str(e)}"
        except grpc.RpcError as e:
            error_counter.inc()
            print(f"RPC error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            response = traffic_regulation_pb2.DeleteDataRegulationResponse(message=str(e))
        return response

    def GetTodayControlLogs(self, request, context):
        self.increment_request_count()
        self.check_critical_load()
        requests_counter.labels('today_control_logs', 'New request for daily control logs').inc()
        print("New request for daily control logs")
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
            return traffic_regulation_pb2.TrafficRegulationResponse(logs=["Request timed out"])
        try:
            conn = db_pool.getconn()
            with conn.cursor() as cursor:
                query = """
                SELECT log_messages FROM traffic_logs
                WHERE intersection_id = %s
                AND date = %s
                """
                cursor.execute(query, (request.intersection_id, datetime.now().strftime('%Y-%m-%d')))
                results = cursor.fetchall()
                print("Retrieved data:", results)
                conn.commit()
                timer_thread.cancel()
            success_counter.inc()
            response = traffic_regulation_pb2.TrafficRegulationResponse()
            response.intersection_id = request.intersection_id
            response.logs.extend([str(result[0]) for result in results])
            db_pool.putconn(conn)
        except (Exception,) as e:
            error_counter.inc()
            context.set_code(grpc.StatusCode.INTERNAL)
            print(f"Error: {str(e)}")
            response = traffic_regulation_pb2.TrafficRegulationResponse(logs=["Error: " + str(e)])
        except grpc.RpcError as e:
            error_counter.inc()
            print(f"RPC error: {str(e)}")
            context.set_code(e)
            context.set_details(str(e))
            response = traffic_regulation_pb2.TrafficRegulationResponse(logs=["RPC error: " + str(e)])
        return response

    def GetLastWeekControlLogs(self, request, context):
        self.increment_request_count()
        self.check_critical_load()
        requests_counter.labels('last_week_control_logs', 'New request for weekly control logs').inc()
        print("New request for weekly control logs")
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
            return traffic_regulation_pb2.TrafficRegulationResponse(logs=["Request timed out"])
        try:
            conn = db_pool.getconn()
            with conn.cursor() as cursor:
                end_date = datetime.now().date()
                start_date = end_date - relativedelta(weeks=1)
                query = """
                SELECT log_messages FROM traffic_logs
                WHERE intersection_id = %s
                AND date >= %s 
                AND date <= %s
                """
                cursor.execute(query, (
                    request.intersection_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
                ))
                results = cursor.fetchall()
                print("Retrieved data:", results)
                conn.commit()
                timer_thread.cancel()
            success_counter.inc()
            response = traffic_regulation_pb2.TrafficRegulationResponse()
            response.intersection_id = request.intersection_id
            logs = []
            for result in results:
                log_messages = result[0]
                for log_message in log_messages:
                    logs.append(log_message)
            response.logs.extend(logs)
            db_pool.putconn(conn)
        except (Exception,) as e:
            error_counter.inc()
            context.set_code(grpc.StatusCode.INTERNAL)
            print(f"Error: {str(e)}")
            response = traffic_regulation_pb2.TrafficRegulationResponse(logs=["Error: " + str(e)])
        except grpc.RpcError as e:
            error_counter.inc()
            print(f"RPC error: {str(e)}")
            context.set_code(e)
            context.set_details(str(e))
            response = traffic_regulation_pb2.TrafficRegulationResponse(logs=["RPC error: " + str(e)])
        return response

    def TrafficRegulationServiceStatus(self, request, context):
        self.increment_request_count()
        self.check_critical_load()
        print("New request for service status")
        timeout_seconds = 2
        timeout_event = threading.Event()
        service_name = os.environ.get("SERVICE_NAME", "traffic-regulation-service-1")
        service_port = int(os.environ.get("SERVICE_PORT", 8081))

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
            return traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(
                message="Request timed out")
        try:
            conn = psycopg2.connect(
                dbname='traffic-regulation-db',
                user='postgres',
                password='397777',
                host='traffic-regulation-database',
                # host='localhost',
                # port='5434'
            )
            context.set_code(grpc.StatusCode.OK)
            context.set_details(f"{service_name}:{service_port} is healthy")
            database_state.state('connected')
            success_counter.inc()
            response = traffic_regulation_pb2.TrafficRegulationServiceStatusResponse(message=f"{service_name}:"
                                                                                             f"{service_port}: healthy")
            conn.close()
            return response
        except (Exception,) as e:
            error_counter.inc()
            database_state.state('not connected')
            context.set_code(grpc.StatusCode.OK)
            context.set_details(f"{service_name}:{service_port} is unhealthy")
            response = traffic_regulation_pb2.TrafficRegulationServiceStatusResponse(message=f"{service_name}:"
                                                                                             f"{service_port}: unhealthy")
            return response
        except grpc.RpcError as e:
            error_counter.inc()
            database_state.state('not connected')
            context.set_code(grpc.StatusCode.OK)
            context.set_details(f"{service_name}:{service_port} is unhealthy")
            response = traffic_regulation_pb2.TrafficRegulationServiceStatusResponse(message=f"{service_name}:"
                                                                                             f"{service_port}: unhealthy")
            return response


def start(service_name, service_port, service_discovery_endpoint, prometheus_port):
    register_service(service_name, service_name, service_port, service_discovery_endpoint)
    start_http_server(prometheus_port)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service = TrafficRegulationServicer()
    service.start_reset_thread()
    traffic_regulation_pb2_grpc.add_TrafficRegulationServicer_to_server(service, server)
    server.add_insecure_port(f"0.0.0.0:{service_port}")
    server.start()
    print(f"{service_name} listening on port {service_port}...")
    server.wait_for_termination()
    service.reset_thread.join()


if __name__ == '__main__':
    start(
        os.environ.get("SERVICE_NAME", "traffic-regulation-service-1"),
        int(os.environ.get("SERVICE_PORT", 8081)),
        os.environ.get("SERVICE_DISCOVERY_ENDPOINT", "http://service-discovery:9090"),
        int(os.environ.get("PROMETHEUS_PORT", 8001))
    )
