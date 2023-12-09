import grpc
from concurrent import futures
import threading
from threading import Timer
import requests
import time
# from cachetools import TTLCache
import traffic_regulation_pb2
import traffic_regulation_pb2_grpc

service_discovery_endpoint = "http://service-discovery:9090"
load_balancer_name = "traffic-regulation-load-balancer"
load_balancer_port = 8000
number_of_replicas = 3
replica_addresses = []
current_replica_index = 0
lock = threading.Lock()
service_status = 0


def register_load_balancer(service_name, service_host, service_port):
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
            print(f"Registered {service_name} with service discovery")
        else:
            print(f"Failed to register {service_name} with service discovery: {response.status_code}")
    except Exception as e:
        print(f"Error while registering {service_name}: {str(e)}")


def get_service_info(service_name):
    try:
        response = requests.get(f"{service_discovery_endpoint}/get_service_data?name={service_name}")
        if response.status_code == 200:
            response = response.json()
            response = [response["name"], response["host"], response["port"]]
            return response
        else:
            print(f"Failed to fetch replica addresses: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error while fetching replica addresses: {str(e)}")
        return []


def get_next_replica():
    global current_replica_index
    with lock:
        current_replica_index = (current_replica_index + 1) % len(replica_addresses)
        return current_replica_index


# cache = TTLCache(maxsize=1000, ttl=300)


class LoadBalancerCircuitBreaker:
    def __init__(self, error_threshold, reroute_threshold, time_window, timeout):
        self.error_threshold = error_threshold
        self.reroute_threshold = reroute_threshold
        self.time_window = time_window
        self.timeout = timeout
        self.replica_statuses = {}
        self.replica_errors = {}
        self.replica_reroutes = {}
        self.health_check_locks = {}
        self.timer = Timer(self.timeout, self.cleanup_all_errors)

    def start_timer(self):
        self.timer.start()

    def cleanup_all_errors(self):
        for replica_number in self.replica_errors:
            now = time.time()
            self.replica_errors[replica_number] = [error for error in self.replica_errors[replica_number] if
                                                   now - error <= self.time_window]
        self.timer = Timer(self.timeout, self.cleanup_all_errors)
        self.timer.start()

    def cleanup_old_errors(self, replica_number):
        now = time.time()
        self.replica_errors[replica_number] = [error for error in self.replica_errors[replica_number] if
                                               now - error <= self.time_window]

    def is_replica_open(self, replica_number):
        replica_state = self.replica_statuses.get(replica_number, 'closed') == 'open'
        return replica_state

    def find_next_closed_replica(self):
        for _ in range(number_of_replicas):
            next_replica_index = get_next_replica()
            next_replica_number = next_replica_index + 1
            if not self.is_replica_open(next_replica_number):
                return next_replica_index
        return None

    def is_health_check_in_progress(self, replica_number):
        return self.health_check_locks.get(replica_number, threading.Lock()).locked()

    def acquire_health_check_lock(self, replica_number):
        if replica_number not in self.health_check_locks:
            self.health_check_locks[replica_number] = threading.Lock()
        self.health_check_locks[replica_number].acquire()

    def release_health_check_lock(self, replica_number):
        self.health_check_locks[replica_number].release()

    def health_check_thread(self, replica_number):
        try:
            if self.is_health_check_in_progress(replica_number):
                print(f"Health check is already in progress for replica nr.{replica_number}")
                return
            self.acquire_health_check_lock(replica_number)
            self.health_check(replica_number)
        finally:
            self.release_health_check_lock(replica_number)

    def health_check(self, replica_number):
        current_replica_address = replica_addresses[replica_number - 1]
        print(f"The circuit breaker is tripped. Starting health check for replica nr.{replica_number}")
        try:
            channel = grpc.insecure_channel(current_replica_address)
            stub = traffic_regulation_pb2_grpc.TrafficRegulationStub(channel)
            errors = 0
            for _ in range(self.error_threshold - 1):
                try:
                    stub.TrafficRegulationServiceStatus(traffic_regulation_pb2.TrafficRegulationServiceStatusRequest(),
                                                        timeout=2)
                    print(f"Health check request succeeded for replica nr.{replica_number}")
                except grpc.RpcError as e:
                    print(f"Health check request failed for replica nr.{replica_number}")
                    errors += 1
                    self.replica_errors[replica_number].append(time.time())
            if len(self.replica_errors[replica_number]) >= self.error_threshold:
                print(f"Replica nr.{replica_number} has reached the threshold")
                print(f"Service at replica nr.{replica_number} is problematic. The circuit breaker is open")
                self.cleanup_old_errors(replica_number)
                self.replica_statuses[replica_number] = 'open'
            else:
                print(f"At least one health check request passed for replica nr.{replica_number}")
                print(f"Service at replica nr.{replica_number} is healthy. The circuit breaker is closed")
                self.replica_statuses[replica_number] = 'closed'
        except Exception as e:
            print(f"Error during health check for replica nr.{current_replica_address}: {str(e)}")

    def __call__(self, func):
        def wrapper(request, context, method):
            global service_status
            global current_replica_index
            if service_status == 1:
                response = traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(
                    message=f"Internal Server Error")
                return response
            current_replica_index = get_next_replica()
            replica_number = current_replica_index + 1
            # print(f"Checking circuit breaker for replica nr.{replica_number}")
            if self.is_replica_open(replica_number):
                print(f"Circuit breaker is open on replica nr.{replica_number}. Redirecting the request...")
                if replica_number not in self.replica_reroutes:
                    self.replica_reroutes[replica_number] = []
                self.replica_errors[replica_number].append(time.time())
                next_closed_replica_index = self.find_next_closed_replica()
                if next_closed_replica_index is not None:
                    current_replica_index = next_closed_replica_index
                else:
                    print("All replicas are open")
                    service_status = 1
                    context.set_code(grpc.StatusCode.INTERNAL)
                    context.set_details(f"Internal Server Error")
                    response = traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(
                        message=f"Internal Server Error")
                    return response
            try:
                # if method in ["GetLastWeekControlLogs"] and service_status != 1:
                #     cache_key = (method, request.intersection_id)
                #     cached_data = cache.get(cache_key)
                #     if cached_data is not None:
                #         print("Cache is present...")
                #         return cached_data
                response = func(request, context, method)
                print(f"Successful request at replica nr.{current_replica_index + 1}")
                # if method in ["GetLastWeekControlLogs"]:
                #     print("Storing cache...")
                #     cache[cache_key] = response
                return response
            except grpc.RpcError as e:
                replica_number = current_replica_index + 1
                if replica_number not in self.replica_errors:
                    self.replica_errors[replica_number] = []
                self.replica_errors[replica_number].append(time.time())
                print(f"Unsuccessful request at replica nr.{replica_number}")
                self.replica_statuses[replica_number] = 'open'
                if not self.is_health_check_in_progress(replica_number):
                    threading.Thread(target=self.health_check_thread, args=(replica_number,)).start()
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Request failed at replica nr.{replica_number}")
                response = traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(
                    message=f"Request failed at replica nr.{replica_number}")
                return response
        return wrapper


circuit_breaker = LoadBalancerCircuitBreaker(error_threshold=3, reroute_threshold=3, time_window=35, timeout=30)
circuit_breaker.start_timer()


@circuit_breaker
def forward_request(request, context, method):
    global current_replica_index
    global service_status
    channel = grpc.insecure_channel(replica_addresses[current_replica_index])
    stub = traffic_regulation_pb2_grpc.TrafficRegulationStub(channel)
    if method == "ReceiveDataForLogs":
        response = stub.ReceiveDataForLogs(request, timeout=2)
    elif method == "AddDataRegulation":
        response = stub.AddDataRegulation(request, timeout=2)
    elif method == "DeleteDataRegulation":
        response = stub.DeleteDataRegulation(request, timeout=2)
    elif method == "GetTodayControlLogs":
        response = stub.GetTodayControlLogs(request, timeout=2)
    elif method == "GetLastWeekControlLogs":
        response = stub.GetLastWeekControlLogs(request, timeout=2)
    elif method == "TrafficRegulationServiceStatus":
        response = stub.TrafficRegulationServiceStatus(request, timeout=2)
    else:
        context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
        context.set_details(f"Invalid method: {method}")
        response = traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(
            message=f"Invalid method: {method}")
    return response


def collect_status_from_replicas():
    responses = []
    for replica_address in replica_addresses:
        channel = grpc.insecure_channel(replica_address)
        stub = traffic_regulation_pb2_grpc.TrafficRegulationStub(channel)
        try:
            response = stub.TrafficRegulationServiceStatus(traffic_regulation_pb2.TrafficRegulationServiceStatusRequest(),
                                                           timeout=2)
            responses.append(response.message)
        except (Exception,) as e:
            message = f"{replica_address}: unhealthy"
            responses.append(message)
    return responses


def merge_status_responses(responses):
    merged_status = ", ".join(response for response in responses)
    return merged_status


class LoadBalancerServicer(traffic_regulation_pb2_grpc.TrafficRegulationServicer):
    def __init__(self):
        pass

    def ReceiveDataForLogs(self, request, context):
        if service_status == 1:
            print("Service is not working")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal Server Error")
            response = traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(
                message=f"Internal Server Error")
            return response
        response = forward_request(request, context, "ReceiveDataForLogs")
        return response

    def AddDataRegulation(self, request, context):
        if service_status == 1:
            print("Service is not working")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal Server Error")
            response = traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(
                message=f"Internal Server Error")
            return response
        response = forward_request(request, context, "AddDataRegulation")
        return response

    def DeleteDataRegulation(self, request, context):
        if service_status == 1:
            print("Service is not working")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal Server Error")
            response = traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(
                message=f"Internal Server Error")
            return response
        response = forward_request(request, context, "DeleteDataRegulation")
        return response

    def GetTodayControlLogs(self, request, context):
        if service_status == 1:
            print("Service is not working")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal Server Error")
            response = traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(
                message=f"Internal Server Error")
            return response
        response = forward_request(request, context, "GetTodayControlLogs")
        return response

    def GetLastWeekControlLogs(self, request, context):
        if service_status == 1:
            print("Service is not working")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal Server Error")
            response = traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(
                message=f"Internal Server Error")
            return response
        response = forward_request(request, context, "GetLastWeekControlLogs")
        return response

    def TrafficRegulationServiceStatus(self, request, context):
        if service_status == 1:
            print("Service is not working")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal Server Error")
            response = traffic_regulation_pb2.TrafficDataForLogsReceiveResponse(
                message=f"Internal Server Error")
            return response
        responses = collect_status_from_replicas()
        merged_response = merge_status_responses(responses)
        unhealthy_service = "unhealthy"
        if unhealthy_service in str(merged_response):
            context.set_code(grpc.StatusCode.OK)
            response = traffic_regulation_pb2.TrafficRegulationServiceStatusResponse(
                message=f"One or more services experience troubles. Statuses: {str(merged_response)}")
            return response
        else:
            context.set_code(grpc.StatusCode.OK)
            response = traffic_regulation_pb2.TrafficRegulationServiceStatusResponse(
                message=f"All service replicas are healthy. Statuses: {str(merged_response)}")
            return response


def start():
    register_load_balancer(load_balancer_name, load_balancer_name, load_balancer_port)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    traffic_regulation_pb2_grpc.add_TrafficRegulationServicer_to_server(LoadBalancerServicer(), server)
    server.add_insecure_port(f"0.0.0.0:{load_balancer_port}")
    server.start()
    print(f"{load_balancer_name} listening on port {load_balancer_port}...")
    print("Waiting for the replicas to start...")
    try:
        for i in range(number_of_replicas):
            replica = get_service_info(f"traffic-regulation-service-{i + 1}")
            replica = "" + str(replica[1]) + ":" + str(replica[2])
            print(f"{replica} registered.")
            replica_addresses.append(replica)
    except Exception as e:
        print(f"Error getting info of all services: {str(e)}")
        server.stop(0)
    server.wait_for_termination()


if __name__ == '__main__':
    start()
