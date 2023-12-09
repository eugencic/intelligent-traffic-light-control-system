import grpc
import traffic_regulation_pb2
import traffic_regulation_pb2_grpc


def receive_data_for_logs():
    with grpc.insecure_channel('localhost:8000') as channel:
        stub = traffic_regulation_pb2_grpc.TrafficRegulationStub(channel)
        request = traffic_regulation_pb2.TrafficDataForLogs(
            intersection_id=5,
            signal_status_1=1,
            vehicle_count=12,
            incident=False,
            date="12.10.2023",
            time="19:11"
        )
        response = stub.ReceiveDataForLogs(request)
        print(response.message)


def get_today_control_logs(intersection_id):
    with grpc.insecure_channel('localhost:8000') as channel:
        stub = traffic_regulation_pb2_grpc.TrafficRegulationStub(channel)
        request = traffic_regulation_pb2.IntersectionRequestForLogs(intersection_id=intersection_id)
        response = stub.GetTodayControlLogs(request)
        print("Today's control logs: ")
        print("Intersection id:", response.intersection_id)
        print("Logs:", response.logs)


def get_last_week_control_logs(intersection_id):
    with grpc.insecure_channel('localhost:8000') as channel:
        stub = traffic_regulation_pb2_grpc.TrafficRegulationStub(channel)
        request = traffic_regulation_pb2.IntersectionRequestForLogs(intersection_id=intersection_id)
        response = stub.GetLastWeekControlLogs(request)
        print("Last week's control logs: ")
        print("Intersection id:", response.intersection_id)
        print("Logs:", response.logs)


def get_service_status():
    with grpc.insecure_channel('localhost:8000') as channel:
        stub = traffic_regulation_pb2_grpc.TrafficRegulationStub(channel)
        request = traffic_regulation_pb2.TrafficRegulationServiceStatusRequest()
        response = stub.TrafficRegulationServiceStatus(request)
        print(response.message)


if __name__ == '__main__':
    # receive_data_for_logs()
    # get_today_control_logs(5)
    # get_last_week_control_logs(5)
    get_service_status()
