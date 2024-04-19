package core

import (
	"encoding/json"
	"fmt"
	"net/http"
)

func GetStatistics(intersectionID int) (StatisticsResponse, error) {
	statisticsURL := fmt.Sprintf("http://localhost:8000/get_statistics/%d", intersectionID)
	resp, err := http.Get(statisticsURL)
	if err != nil {
		return StatisticsResponse{}, err
	}
	defer resp.Body.Close()

	var stats StatisticsResponse
	if err := json.NewDecoder(resp.Body).Decode(&stats); err != nil {
		return StatisticsResponse{}, err
	}

	return stats, nil
}
