import grpc
from concurrent.futures import ThreadPoolExecutor, wait
from flask import Flask, request, jsonify, Response
import requests
from prometheus_client import Counter, generate_latest, REGISTRY
import traffic_analytics_pb2
import traffic_analytics_pb2_grpc
import traffic_regulation_pb2
import traffic_regulation_pb2_grpc

app = Flask(__name__)

service_discovery_endpoint = "http://service-discovery:9090"
coordinator_name = "coordinator"
coordinator_port = 6061
requests_counter = Counter('coordinator_requests_total', 'Requests')


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
            print(f"Registered {service_name} with service discovery.")
        else:
            print(f"Failed to register {service_name} with service discovery: {response.status_code}")
    except Exception as e:
        print(f"Error while registering {service_name}: {str(e)}")


def get_service_info(service_name):
    try:
        response = requests.get(f"{service_discovery_endpoint}/get_service_data?name={service_name}")
        if response.status_code == 200:
            response = response.json()
            response = ("" + str(response["name"]) + ":" + str(response["port"]))
            return response
        else:
            print(f"Failed to fetch replica addresses: {response.status_code}")
            return
    except Exception as e:
        print(f"Error while fetching replica addresses: {str(e)}")
        return


def add_traffic_data_analytics(intersection_id, message):
    channel = grpc.insecure_channel(traffic_analytics_service_address)
    stub = traffic_analytics_pb2_grpc.TrafficAnalyticsStub(channel)
    request = traffic_analytics_pb2.AddDataAnalyticsRequest(
        intersection_id=intersection_id,
        message=message
    )
    response = stub.AddDataAnalytics(request)
    return response


def add_traffic_data_regulation(intersection_id, message):
    channel = grpc.insecure_channel(traffic_regulation_service_address)
    stub = traffic_regulation_pb2_grpc.TrafficRegulationStub(channel)
    request = traffic_regulation_pb2.AddDataRegulationRequest(
        intersection_id=intersection_id,
        message=message
    )
    response = stub.AddDataRegulation(request)
    return response


def undo_traffic_data_analytics(intersection_id):
    channel = grpc.insecure_channel(traffic_analytics_service_address)
    stub = traffic_analytics_pb2_grpc.TrafficAnalyticsStub(channel)
    request = traffic_analytics_pb2.DeleteDataAnalyticsRequest(
        intersection_id=intersection_id
    )
    response = stub.DeleteDataAnalytics(request)
    return response


def undo_traffic_data_regulation(intersection_id):
    channel = grpc.insecure_channel(traffic_regulation_service_address)
    stub = traffic_regulation_pb2_grpc.TrafficRegulationStub(channel)
    request = traffic_regulation_pb2.DeleteDataRegulationRequest(
        intersection_id=intersection_id
    )
    response = stub.DeleteDataRegulation(request)
    return response


def saga_coordinator(intersection_id, message):
    try:
        print("Step 1: Add data to Traffic Analytics")
        app.logger.info("Step 1: Add data to Traffic Analytics")
        with ThreadPoolExecutor() as executor:
            future_analytics = executor.submit(add_traffic_data_analytics, intersection_id, message)
        print("Step 2: Add data to Traffic Regulation")
        app.logger.info("Step 2: Add data to Traffic Regulation")
        with ThreadPoolExecutor() as executor:
            future_regulations = executor.submit(add_traffic_data_regulation, intersection_id, message)
        wait([future_analytics, future_regulations])
        print("Steps completed. Proceeding to compensating actions if needed.")
        app.logger.info("Steps completed. Proceeding to compensating actions if needed.")
        future_analytics.result()
        future_regulations.result()
        print("No need for compensating actions.")
        app.logger.info("No need for compensating actions.")
        return 200
    except Exception as e:
        print("Error during saga coordination:", str(e))
        app.logger.info("Error during saga coordination.")
        print("Compensation: Undo changes made by previous steps...")
        app.logger.info("Compensation: Undo changes made by previous steps...")
        with ThreadPoolExecutor() as compensator_executor:
            future_analytics = compensator_executor.submit(undo_traffic_data_analytics, intersection_id)
            future_regulations = compensator_executor.submit(undo_traffic_data_regulation, intersection_id)
            wait([future_analytics, future_regulations])
            print("Compensating actions completed.")
            app.logger.info("Compensating actions completed.")
            return 500


@app.route('/metrics')
def metrics():
    return Response(generate_latest(REGISTRY), content_type='text/plain')


@app.route('/add_data', methods=['POST'])
def add_data():
    requests_counter.inc()
    try:
        data = request.json
        intersection_id = data.get('intersection_id')
        message = data.get('message')
        print("Initiating saga...")
        app.logger.info("Initiating saga...")
        response = saga_coordinator(intersection_id, message)
        if response == 500:
            return jsonify({"message": "Internal Server Error"}), 500
        return jsonify({"message": "Data added successfully"}), 200
    except (Exception,) as e:
        return jsonify({"message": "Internal Server Error"}), 500


if __name__ == '__main__':
    register_load_balancer(coordinator_name, coordinator_name, coordinator_port)
    traffic_analytics_service_address = get_service_info("traffic-analytics-load-balancer")
    traffic_regulation_service_address = get_service_info("traffic-regulation-load-balancer")
    print(f"{traffic_analytics_service_address} registered.")
    print(f"{traffic_regulation_service_address} registered.")
    app.run(host='0.0.0.0', port=6061, debug=True)
