package core

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

func GetPrediction(intersectionID int) (PredictionResponse, error) {
	currentTime := time.Now()
	predictionsURL := fmt.Sprintf("http://localhost:8000/get_predictions/%d?hour=%d&minute=%d",
		intersectionID, currentTime.Hour(), currentTime.Minute())

	resp, err := http.Get(predictionsURL)
	if err != nil {
		return PredictionResponse{}, err
	}
	defer resp.Body.Close()

	var prediction PredictionResponse
	if err := json.NewDecoder(resp.Body).Decode(&prediction); err != nil {
		return PredictionResponse{}, err
	}

	return prediction, nil
}
