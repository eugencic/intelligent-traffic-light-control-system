create:
	python3 -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. --pyi_out=. proto/traffic_regulation.proto

clean-generated-files:
	del -f traffic_regulation_pb2.py traffic_regulation_pb2.pyi traffic_regulation_pb2_grpc.py # windows
	#rm -f traffic_control_pb2.py traffic_control_pb2.pyi traffic_control_pb2_grpc.py #linux

.PHONY: all clean-generated-files

delete:
	clean-generated-files

requirements:
	pip freeze > requirements.txt
