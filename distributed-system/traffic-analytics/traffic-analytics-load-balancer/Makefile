create:
	python3 -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. --pyi_out=. proto/traffic_analytics.proto

clean-generated-files:
	del -f traffic_analytics_pb2.py traffic_analytics_pb2.pyi traffic_analytics_pb2_grpc.py # windows
	#rm -f traffic_analytics_pb2.py traffic_analytics_pb2.pyi traffic_analytics_pb2_grpc.py #linux

.PHONY: all clean-generated-files

delete: clean-generated-files

requirements:
	pip freeze > requirements.txt