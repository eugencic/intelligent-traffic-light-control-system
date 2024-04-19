package core

import (
	"encoding/json"
	"net/http"
	"strconv"
)

func GetIntersectionInfoHandler(w http.ResponseWriter, r *http.Request) {
	intersectionID := r.URL.Query().Get("id")
	if intersectionID == "" {
		http.Error(w, "Missing intersection ID", http.StatusBadRequest)
		return
	}

	id, err := strconv.Atoi(intersectionID)
	if err != nil {
		http.Error(w, "Invalid intersection ID", http.StatusBadRequest)
		return
	}

	stats, err := GetStatistics(id)
	if err != nil {
		http.Error(w, "Failed to fetch statistics", http.StatusInternalServerError)
		return
	}

	prediction, err := GetPrediction(id)
	if err != nil {
		http.Error(w, "Failed to fetch predictions", http.StatusInternalServerError)
		return
	}

	response := IntersectionInfoResponse{
		Statistics: stats,
		Prediction: prediction,
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, "Failed to encode response to JSON", http.StatusInternalServerError)
		return
	}
}
