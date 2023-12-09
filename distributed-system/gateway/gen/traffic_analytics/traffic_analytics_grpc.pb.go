// Code generated by protoc-gen-go-grpc. DO NOT EDIT.
// versions:
// - protoc-gen-go-grpc v1.3.0
// - protoc             v4.24.4
// source: traffic_analytics.proto

package __

import (
	context "context"
	grpc "google.golang.org/grpc"
	codes "google.golang.org/grpc/codes"
	status "google.golang.org/grpc/status"
)

// This is a compile-time assertion to ensure that this generated file
// is compatible with the grpc package it is being compiled against.
// Requires gRPC-Go v1.32.0 or later.
const _ = grpc.SupportPackageIsVersion7

const (
	TrafficAnalytics_ReceiveDataForAnalytics_FullMethodName       = "/analytics.TrafficAnalytics/ReceiveDataForAnalytics"
	TrafficAnalytics_GetTodayStatistics_FullMethodName            = "/analytics.TrafficAnalytics/GetTodayStatistics"
	TrafficAnalytics_GetLastWeekStatistics_FullMethodName         = "/analytics.TrafficAnalytics/GetLastWeekStatistics"
	TrafficAnalytics_GetNextWeekPredictions_FullMethodName        = "/analytics.TrafficAnalytics/GetNextWeekPredictions"
	TrafficAnalytics_TrafficAnalyticsServiceStatus_FullMethodName = "/analytics.TrafficAnalytics/TrafficAnalyticsServiceStatus"
)

// TrafficAnalyticsClient is the client API for TrafficAnalytics service.
//
// For semantics around ctx use and closing/ending streaming RPCs, please refer to https://pkg.go.dev/google.golang.org/grpc/?tab=doc#ClientConn.NewStream.
type TrafficAnalyticsClient interface {
	ReceiveDataForAnalytics(ctx context.Context, in *TrafficDataForAnalytics, opts ...grpc.CallOption) (*TrafficDataForAnalyticsReceiveResponse, error)
	GetTodayStatistics(ctx context.Context, in *IntersectionRequestForAnalytics, opts ...grpc.CallOption) (*TrafficAnalyticsResponse, error)
	GetLastWeekStatistics(ctx context.Context, in *IntersectionRequestForAnalytics, opts ...grpc.CallOption) (*TrafficAnalyticsResponse, error)
	GetNextWeekPredictions(ctx context.Context, in *IntersectionRequestForAnalytics, opts ...grpc.CallOption) (*TrafficAnalyticsResponse, error)
	TrafficAnalyticsServiceStatus(ctx context.Context, in *TrafficAnalyticsServiceStatusRequest, opts ...grpc.CallOption) (*TrafficAnalyticsServiceStatusResponse, error)
}

type trafficAnalyticsClient struct {
	cc grpc.ClientConnInterface
}

func NewTrafficAnalyticsClient(cc grpc.ClientConnInterface) TrafficAnalyticsClient {
	return &trafficAnalyticsClient{cc}
}

func (c *trafficAnalyticsClient) ReceiveDataForAnalytics(ctx context.Context, in *TrafficDataForAnalytics, opts ...grpc.CallOption) (*TrafficDataForAnalyticsReceiveResponse, error) {
	out := new(TrafficDataForAnalyticsReceiveResponse)
	err := c.cc.Invoke(ctx, TrafficAnalytics_ReceiveDataForAnalytics_FullMethodName, in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *trafficAnalyticsClient) GetTodayStatistics(ctx context.Context, in *IntersectionRequestForAnalytics, opts ...grpc.CallOption) (*TrafficAnalyticsResponse, error) {
	out := new(TrafficAnalyticsResponse)
	err := c.cc.Invoke(ctx, TrafficAnalytics_GetTodayStatistics_FullMethodName, in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *trafficAnalyticsClient) GetLastWeekStatistics(ctx context.Context, in *IntersectionRequestForAnalytics, opts ...grpc.CallOption) (*TrafficAnalyticsResponse, error) {
	out := new(TrafficAnalyticsResponse)
	err := c.cc.Invoke(ctx, TrafficAnalytics_GetLastWeekStatistics_FullMethodName, in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *trafficAnalyticsClient) GetNextWeekPredictions(ctx context.Context, in *IntersectionRequestForAnalytics, opts ...grpc.CallOption) (*TrafficAnalyticsResponse, error) {
	out := new(TrafficAnalyticsResponse)
	err := c.cc.Invoke(ctx, TrafficAnalytics_GetNextWeekPredictions_FullMethodName, in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *trafficAnalyticsClient) TrafficAnalyticsServiceStatus(ctx context.Context, in *TrafficAnalyticsServiceStatusRequest, opts ...grpc.CallOption) (*TrafficAnalyticsServiceStatusResponse, error) {
	out := new(TrafficAnalyticsServiceStatusResponse)
	err := c.cc.Invoke(ctx, TrafficAnalytics_TrafficAnalyticsServiceStatus_FullMethodName, in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

// TrafficAnalyticsServer is the server API for TrafficAnalytics service.
// All implementations must embed UnimplementedTrafficAnalyticsServer
// for forward compatibility
type TrafficAnalyticsServer interface {
	ReceiveDataForAnalytics(context.Context, *TrafficDataForAnalytics) (*TrafficDataForAnalyticsReceiveResponse, error)
	GetTodayStatistics(context.Context, *IntersectionRequestForAnalytics) (*TrafficAnalyticsResponse, error)
	GetLastWeekStatistics(context.Context, *IntersectionRequestForAnalytics) (*TrafficAnalyticsResponse, error)
	GetNextWeekPredictions(context.Context, *IntersectionRequestForAnalytics) (*TrafficAnalyticsResponse, error)
	TrafficAnalyticsServiceStatus(context.Context, *TrafficAnalyticsServiceStatusRequest) (*TrafficAnalyticsServiceStatusResponse, error)
	mustEmbedUnimplementedTrafficAnalyticsServer()
}

// UnimplementedTrafficAnalyticsServer must be embedded to have forward compatible implementations.
type UnimplementedTrafficAnalyticsServer struct {
}

func (UnimplementedTrafficAnalyticsServer) ReceiveDataForAnalytics(context.Context, *TrafficDataForAnalytics) (*TrafficDataForAnalyticsReceiveResponse, error) {
	return nil, status.Errorf(codes.Unimplemented, "method ReceiveDataForAnalytics not implemented")
}
func (UnimplementedTrafficAnalyticsServer) GetTodayStatistics(context.Context, *IntersectionRequestForAnalytics) (*TrafficAnalyticsResponse, error) {
	return nil, status.Errorf(codes.Unimplemented, "method GetTodayStatistics not implemented")
}
func (UnimplementedTrafficAnalyticsServer) GetLastWeekStatistics(context.Context, *IntersectionRequestForAnalytics) (*TrafficAnalyticsResponse, error) {
	return nil, status.Errorf(codes.Unimplemented, "method GetLastWeekStatistics not implemented")
}
func (UnimplementedTrafficAnalyticsServer) GetNextWeekPredictions(context.Context, *IntersectionRequestForAnalytics) (*TrafficAnalyticsResponse, error) {
	return nil, status.Errorf(codes.Unimplemented, "method GetNextWeekPredictions not implemented")
}
func (UnimplementedTrafficAnalyticsServer) TrafficAnalyticsServiceStatus(context.Context, *TrafficAnalyticsServiceStatusRequest) (*TrafficAnalyticsServiceStatusResponse, error) {
	return nil, status.Errorf(codes.Unimplemented, "method TrafficAnalyticsServiceStatus not implemented")
}
func (UnimplementedTrafficAnalyticsServer) mustEmbedUnimplementedTrafficAnalyticsServer() {}

// UnsafeTrafficAnalyticsServer may be embedded to opt out of forward compatibility for this service.
// Use of this interface is not recommended, as added methods to TrafficAnalyticsServer will
// result in compilation errors.
type UnsafeTrafficAnalyticsServer interface {
	mustEmbedUnimplementedTrafficAnalyticsServer()
}

func RegisterTrafficAnalyticsServer(s grpc.ServiceRegistrar, srv TrafficAnalyticsServer) {
	s.RegisterService(&TrafficAnalytics_ServiceDesc, srv)
}

func _TrafficAnalytics_ReceiveDataForAnalytics_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(TrafficDataForAnalytics)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(TrafficAnalyticsServer).ReceiveDataForAnalytics(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: TrafficAnalytics_ReceiveDataForAnalytics_FullMethodName,
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(TrafficAnalyticsServer).ReceiveDataForAnalytics(ctx, req.(*TrafficDataForAnalytics))
	}
	return interceptor(ctx, in, info, handler)
}

func _TrafficAnalytics_GetTodayStatistics_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(IntersectionRequestForAnalytics)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(TrafficAnalyticsServer).GetTodayStatistics(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: TrafficAnalytics_GetTodayStatistics_FullMethodName,
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(TrafficAnalyticsServer).GetTodayStatistics(ctx, req.(*IntersectionRequestForAnalytics))
	}
	return interceptor(ctx, in, info, handler)
}

func _TrafficAnalytics_GetLastWeekStatistics_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(IntersectionRequestForAnalytics)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(TrafficAnalyticsServer).GetLastWeekStatistics(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: TrafficAnalytics_GetLastWeekStatistics_FullMethodName,
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(TrafficAnalyticsServer).GetLastWeekStatistics(ctx, req.(*IntersectionRequestForAnalytics))
	}
	return interceptor(ctx, in, info, handler)
}

func _TrafficAnalytics_GetNextWeekPredictions_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(IntersectionRequestForAnalytics)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(TrafficAnalyticsServer).GetNextWeekPredictions(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: TrafficAnalytics_GetNextWeekPredictions_FullMethodName,
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(TrafficAnalyticsServer).GetNextWeekPredictions(ctx, req.(*IntersectionRequestForAnalytics))
	}
	return interceptor(ctx, in, info, handler)
}

func _TrafficAnalytics_TrafficAnalyticsServiceStatus_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(TrafficAnalyticsServiceStatusRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(TrafficAnalyticsServer).TrafficAnalyticsServiceStatus(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: TrafficAnalytics_TrafficAnalyticsServiceStatus_FullMethodName,
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(TrafficAnalyticsServer).TrafficAnalyticsServiceStatus(ctx, req.(*TrafficAnalyticsServiceStatusRequest))
	}
	return interceptor(ctx, in, info, handler)
}

// TrafficAnalytics_ServiceDesc is the grpc.ServiceDesc for TrafficAnalytics service.
// It's only intended for direct use with grpc.RegisterService,
// and not to be introspected or modified (even as a copy)
var TrafficAnalytics_ServiceDesc = grpc.ServiceDesc{
	ServiceName: "analytics.TrafficAnalytics",
	HandlerType: (*TrafficAnalyticsServer)(nil),
	Methods: []grpc.MethodDesc{
		{
			MethodName: "ReceiveDataForAnalytics",
			Handler:    _TrafficAnalytics_ReceiveDataForAnalytics_Handler,
		},
		{
			MethodName: "GetTodayStatistics",
			Handler:    _TrafficAnalytics_GetTodayStatistics_Handler,
		},
		{
			MethodName: "GetLastWeekStatistics",
			Handler:    _TrafficAnalytics_GetLastWeekStatistics_Handler,
		},
		{
			MethodName: "GetNextWeekPredictions",
			Handler:    _TrafficAnalytics_GetNextWeekPredictions_Handler,
		},
		{
			MethodName: "TrafficAnalyticsServiceStatus",
			Handler:    _TrafficAnalytics_TrafficAnalyticsServiceStatus_Handler,
		},
	},
	Streams:  []grpc.StreamDesc{},
	Metadata: "traffic_analytics.proto",
}
