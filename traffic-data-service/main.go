package main

import (
	"fmt"
	"net/http"
	"traffic-data-service/core"
)

func main() {
	http.HandleFunc("/get_intersection_info", core.GetIntersectionInfoHandler)

	fmt.Println("Server is listening on port 6000...")
	if err := http.ListenAndServe(":6000", nil); err != nil {
		fmt.Printf("Error starting core: %s\n", err)
	}
}
