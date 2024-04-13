package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"runtime"
	"sync"
	"time"
)

type Service struct {
	Name string `json:"name"`
	Host string `json:"host"`
	Port int    `json:"port"`
}

var (
	servicesMu sync.Mutex
	services   = make(map[string]Service)
)

var startTime time.Time

func init() {
	startTime = time.Now()
}

func formatMemoryInMB(bytes uint64) string {
	const megabyte = 1024 * 1024
	return fmt.Sprintf("%.2f MB", float64(bytes)/float64(megabyte))
}

func statusHandler(w http.ResponseWriter, r *http.Request) {
	uptime := time.Since(startTime).Minutes()

	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)

	statusInfo := map[string]interface{}{
		"Consumed memory":      formatMemoryInMB(memStats.Sys),
		"Number of Goroutines": runtime.NumGoroutine(),
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

func registerService(w http.ResponseWriter, r *http.Request) {
	var service Service
	if err := json.NewDecoder(r.Body).Decode(&service); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	servicesMu.Lock()

	if existingService, found := services[service.Name]; found {
		fmt.Printf("Replacing existing service: %s at %s:%d with %s:%d\n", existingService.Name, existingService.Host, existingService.Port, service.Host, service.Port)
	}

	services[service.Name] = service
	servicesMu.Unlock()

	fmt.Printf("Registered service: %s at %s:%d\n", service.Name, service.Host, service.Port)
	w.WriteHeader(http.StatusCreated)
}

func getService(w http.ResponseWriter, r *http.Request) {
	serviceName := r.URL.Query().Get("name")

	servicesMu.Lock()
	service, found := services[serviceName]
	servicesMu.Unlock()

	if !found {
		http.NotFound(w, r)
		return
	}

	err := json.NewEncoder(w).Encode(service)
	if err != nil {
		return
	}
}

func main() {
	http.HandleFunc("/get_service_discovery_status", statusHandler)
	http.HandleFunc("/register_service", registerService)
	http.HandleFunc("/get_service_data", getService)

	fmt.Println("Service discovery listening on port 9090...")
	log.Fatal(http.ListenAndServe(":9090", nil))
}
