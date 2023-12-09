package main

import (
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	ta "gateway/gen/traffic_analytics"
	tr "gateway/gen/traffic_regulation"
	"github.com/golang/glog"
	muxRuntime "github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"google.golang.org/grpc"
	"io"
	"log"
	"net/http"
	"os"
	"runtime"
	"time"
)

type Service struct {
	Name string `json:"name"`
	Host string `json:"host"`
	Port int    `json:"port"`
}

var (
	gatewayName                  = "Gateway"
	gatewayHost                  = "localhost"
	gatewayPort                  = 6060
	serviceDiscoveryName         = "service-discovery"
	serviceDiscoveryEndpoint     = "http://service-discovery:9090"
	trafficAnalyticsServiceName  = "traffic-analytics-load-balancer"
	trafficRegulationServiceName = "traffic-regulation-load-balancer"
)

var logger = log.New(os.Stdout, "", log.LstdFlags)

var startTime time.Time

var (
	requestsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_requests_total",
			Help: "Total number of requests handled by the gateway.",
		},
		[]string{"method", "status"},
	)
)

func init() {
	startTime = time.Now()

	prometheus.MustRegister(requestsTotal)
}

func formatMemoryInMB(bytes uint64) string {
	const megabyte = 1024 * 1024
	return fmt.Sprintf("%.2f MB", float64(bytes)/float64(megabyte))
}

func statusHandler(w http.ResponseWriter, r *http.Request) {
	status := 200
	if responseStatus, ok := w.(interface{ Status() int }); ok {
		status = responseStatus.Status()
	}
	requestsTotal.WithLabelValues(r.Method, fmt.Sprintf("%d", status)).Inc()

	uptime := time.Since(startTime).Minutes()

	dependentServices := []string{
		serviceDiscoveryName,
		trafficAnalyticsServiceName,
		trafficRegulationServiceName,
	}

	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)

	statusInfo := map[string]interface{}{
		"Consumed memory":      formatMemoryInMB(memStats.Sys),
		"Number of Goroutines": runtime.NumGoroutine(),
		"Dependent services":   dependentServices,
		"Uptime":               fmt.Sprintf("%.2f minutes", uptime),
	}

	w.Header().Set("Content-Type", "application/json")

	jsonBytes, err := json.Marshal(statusInfo)
	if err != nil {
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(jsonBytes)
}

func serviceDiscoveryStatusHandler(w http.ResponseWriter, r *http.Request) {
	status := 200
	if responseStatus, ok := w.(interface{ Status() int }); ok {
		status = responseStatus.Status()
	}
	requestsTotal.WithLabelValues(r.Method, fmt.Sprintf("%d", status)).Inc()

	resp, err := http.Get(serviceDiscoveryEndpoint + "/get_service_discovery_status")
	if err != nil {
		http.Error(w, "Service discovery is not reachable", http.StatusServiceUnavailable)
		return
	}

	defer func(Body io.ReadCloser) {
		err := Body.Close()
		if err != nil {

		}
	}(resp.Body)

	for k, v := range resp.Header {
		w.Header()[k] = v
	}
	w.WriteHeader(resp.StatusCode)

	_, err = io.Copy(w, resp.Body)
	if err != nil {
		http.Error(w, "Error copying response from Service Discovery", http.StatusInternalServerError)
		return
	}
}

func registerWithServiceDiscovery() {
	serviceInfo := Service{
		Name: gatewayName,
		Host: gatewayHost,
		Port: gatewayPort,
	}

	data, err := json.Marshal(serviceInfo)
	if err != nil {
		log.Fatalf("Failed to convert service information in JSON format: %v", err)
	}

	resp, err := http.Post(serviceDiscoveryEndpoint+"/register_service", "application/json", bytes.NewReader(data))
	if err != nil {
		log.Fatalf("Failed to register the gateway with service discovery: %v", err)
	}

	defer func(Body io.ReadCloser) {
		err := Body.Close()
		if err != nil {
		}
	}(resp.Body)

	if resp.StatusCode != http.StatusCreated {
		log.Fatalf("Failed to register the gateway with service discovery: HTTP %d", resp.StatusCode)
	}

	fmt.Printf("%s registered with service discovery\n", gatewayName)
}

func getServiceInfo(serviceName string) (string, int, error) {
	resp, err := http.Get(serviceDiscoveryEndpoint + "/get_service_data?name=" + serviceName)
	if err != nil {
		return "", 0, err
	}

	defer func(Body io.ReadCloser) {
		err := Body.Close()
		if err != nil {
		}
	}(resp.Body)

	if resp.StatusCode != http.StatusOK {
		return "", 0, fmt.Errorf("service not found")
	}

	var service Service
	if err := json.NewDecoder(resp.Body).Decode(&service); err != nil {
		return "", 0, err
	}

	return service.Host, service.Port, nil
}

func logRequestMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		logger.Printf("Request: %s %s", r.Method, r.URL.Path)

		statusCode := 200
		if responseStatus, ok := w.(interface{ Status() int }); ok {
			statusCode = responseStatus.Status()
		}
		requestsTotal.WithLabelValues(r.Method, fmt.Sprintf("%d", statusCode)).Inc()

		next.ServeHTTP(w, r)

		if status, ok := w.(interface {
			Status() int
		}); ok {
			if status.Status() < 200 || status.Status() >= 300 {
				logger.Printf("Response Error: %d", status.Status())
			}
		}
	})
}

func run() error {
	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	trafficAnalyticsHost, trafficAnalyticsPort, err := getServiceInfo(trafficAnalyticsServiceName)
	if err != nil {
		log.Fatalf("Failed to retrieve information about the traffic analytics service: %v", err)
	}

	trafficRegulationHost, trafficRegulationPort, err := getServiceInfo(trafficRegulationServiceName)
	if err != nil {
		log.Fatalf("Failed to retrieve information about the traffic regulation service: %v", err)
	}

	trafficAnalyticsServiceEndpoint := flag.String("traffic-analytics-service-endpoint", fmt.Sprintf("%s:%d", trafficAnalyticsHost, trafficAnalyticsPort), "traffic analytics service endpoint")
	trafficRegulationServiceEndpoint := flag.String("traffic-regulation-service-endpoint", fmt.Sprintf("%s:%d", trafficRegulationHost, trafficRegulationPort), "traffic regulation service endpoint")

	flag.Parse()

	grpcMux := muxRuntime.NewServeMux()

	opts := []grpc.DialOption{grpc.WithInsecure()}

	err = ta.RegisterTrafficAnalyticsHandlerFromEndpoint(ctx, grpcMux, *trafficAnalyticsServiceEndpoint, opts)
	if err != nil {
		log.Fatalln("Cannot register traffic analytics handler server.")
	} else {
		fmt.Println("Traffic analytics service registered.")
	}

	err = tr.RegisterTrafficRegulationHandlerFromEndpoint(ctx, grpcMux, *trafficRegulationServiceEndpoint, opts)
	if err != nil {
		log.Fatalln("Cannot register traffic regulation handler server.")
	} else {
		fmt.Println("Traffic regulation service registered.")
	}

	mux := http.NewServeMux()

	mux.HandleFunc("/get_service_discovery_status", serviceDiscoveryStatusHandler)

	mux.HandleFunc("/get_gateway_status", statusHandler)

	mux.Handle("/metrics", promhttp.Handler())

	mux.Handle("/", logRequestMiddleware(grpcMux))

	fmt.Println("Gateway listening on port 6060...")
	return http.ListenAndServe(":6060", mux)
}

func main() {
	flag.Parse()
	defer glog.Flush()

	registerWithServiceDiscovery()

	if err := run(); err != nil {
		glog.Fatal(err)
	}
}
