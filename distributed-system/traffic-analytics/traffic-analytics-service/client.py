import grpc
import traffic_analytics_pb2
import traffic_analytics_pb2_grpc


def receive_data_for_analytics():
    with grpc.insecure_channel('localhost:7071') as channel:
        stub = traffic_analytics_pb2_grpc.TrafficAnalyticsStub(channel)
        request = traffic_analytics_pb2.TrafficDataForAnalytics(
            intersection_id=5,
            signal_status_1=9,
            vehicle_count=50,
            incident=False,
            date="10.10.2023",
            time="19:11"
        )
        response = stub.ReceiveDataForAnalytics(request)
        print(response.message)


def get_today_statistics(intersection_id):
    with grpc.insecure_channel('localhost:7071') as channel:
        stub = traffic_analytics_pb2_grpc.TrafficAnalyticsStub(channel)
        request = traffic_analytics_pb2.IntersectionRequestForAnalytics(intersection_id=intersection_id)
        response = stub.GetTodayStatistics(request)
        print("Today's statistics: ")
        print("Intersection id:", response.intersection_id)
        print("Timestamp:", response.timestamp)
        print("Average vehicle count:", response.average_vehicle_count)
        print("Peak Hours:", response.peak_hours)
        print("Average incidents:", response.average_incidents)


def get_last_week_statistics(intersection_id):
    with grpc.insecure_channel('localhost:7071') as channel:
        stub = traffic_analytics_pb2_grpc.TrafficAnalyticsStub(channel)
        request = traffic_analytics_pb2.IntersectionRequestForAnalytics(intersection_id=intersection_id)
        response = stub.GetLastWeekStatistics(request)
        print("Last week's statistics: ")
        print(response)
        print("Intersection id:", response.intersection_id)
        print("Timestamp:", response.timestamp)
        print("Average vehicle count:", response.average_vehicle_count)
        print("Peak hours:", response.peak_hours)
        print("Incidents:", response.average_incidents)


def get_next_week_predictions(intersection_id):
    with grpc.insecure_channel('localhost:7071') as channel:
        stub = traffic_analytics_pb2_grpc.TrafficAnalyticsStub(channel)
        request = traffic_analytics_pb2.IntersectionRequestForAnalytics(intersection_id=intersection_id)
        response = stub.GetNextWeekPredictions(request)
        print("Next week's predictions: ")
        print(response)
        print("Intersection id:", response.intersection_id)
        print("Timestamp:", response.timestamp)
        print("Average vehicle count:", response.average_vehicle_count)
        print("Peak hours:", response.peak_hours)
        print("Incidents:", response.average_incidents)


def get_service_status():
    with grpc.insecure_channel('localhost:7071') as channel:
        stub = traffic_analytics_pb2_grpc.TrafficAnalyticsStub(channel)
        request = traffic_analytics_pb2.TrafficAnalyticsServiceStatusRequest()
        response = stub.TrafficAnalyticsServiceStatus(request)
        print(response.message)


if __name__ == '__main__':
    # receive_data_for_analytics()
    # get_today_statistics(5)
    # get_last_week_statistics(5)
    # get_next_week_predictions(5)
    get_service_status()
