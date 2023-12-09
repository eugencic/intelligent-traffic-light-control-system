create:
	protoc --proto_path=proto \
	--go_out=gen/traffic_analytics --go_opt paths=source_relative \
	--go-grpc_out gen/traffic_analytics --go-grpc_opt paths=source_relative \
	--grpc-gateway_out gen/traffic_analytics --grpc-gateway_opt=paths=source_relative \
    proto/traffic_analytics.proto

	protoc --proto_path=proto \
    --go_out=gen/traffic_regulation --go_opt paths=source_relative \
    --go-grpc_out=gen/traffic_regulation --go-grpc_opt paths=source_relative \
    --grpc-gateway_out=gen/traffic_regulation --grpc-gateway_opt paths=source_relative \
    proto/traffic_regulation.proto

delete:
	del gen\traffic_analytics\*.go # windows
	del gen\traffic_regulation\*.go # windows
	# rm gen/traffic_analytics/*.go # linux
	# rm gen/traffic_control/*.go # linux
