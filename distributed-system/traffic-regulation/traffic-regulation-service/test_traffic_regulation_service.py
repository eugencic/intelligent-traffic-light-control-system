import unittest
import grpc
import traffic_regulation_pb2
import traffic_regulation_pb2_grpc


class TrafficRegulationServiceTests(unittest.TestCase):
    def test_receive_data_for_logs(self):
        with grpc.insecure_channel('localhost:8081') as channel:
            stub = traffic_regulation_pb2_grpc.TrafficRegulationStub(channel)
            request = traffic_regulation_pb2.TrafficDataForLogs(
                intersection_id=5,
                signal_status_1=1,
                vehicle_count=12,
                incident=False,
                date="22.10.2023",
                time="19:11"
            )
            response = stub.ReceiveDataForLogs(request)
            self.assertTrue(response.message.startswith("Traffic data for intersection nr.5 received successfully"))

    def test_get_today_control_logs(self):
        with grpc.insecure_channel('localhost:8081') as channel:
            stub = traffic_regulation_pb2_grpc.TrafficRegulationStub(channel)
            request = traffic_regulation_pb2.IntersectionRequestForLogs(intersection_id=5)
            response = stub.GetTodayControlLogs(request)
            self.assertEqual(response.intersection_id, 5)

    def test_get_last_week_control_logs(self):
        with grpc.insecure_channel('localhost:8081') as channel:
            stub = traffic_regulation_pb2_grpc.TrafficRegulationStub(channel)
            request = traffic_regulation_pb2.IntersectionRequestForLogs(intersection_id=5)
            response = stub.GetLastWeekControlLogs(request)
            self.assertEqual(response.intersection_id, 5)

    def test_get_service_status(self):
        with grpc.insecure_channel('localhost:8081') as channel:
            stub = traffic_regulation_pb2_grpc.TrafficRegulationStub(channel)
            request = traffic_regulation_pb2.TrafficRegulationServiceStatusRequest()
            response = stub.TrafficRegulationServiceStatus(request)
            self.assertTrue(response.message.startswith("traffic-regulation-service-1: healthy"))


if __name__ == '__main__':
    unittest.main()
