package core

type StatisticsResponse struct {
	LightHoursIntervals  [][]string `json:"light_hours_intervals"`
	MeanPedestrianCount  float64    `json:"mean_pedestrian_count"`
	MeanVehicleCount     float64    `json:"mean_vehicle_count"`
	NormalHoursIntervals [][]string `json:"normal_hours_intervals"`
	PeakHoursIntervals   [][]string `json:"peak_hours_intervals"`
	TimeMax              string     `json:"time_max"`
	TimeMin              string     `json:"time_min"`
}

type PredictionResponse struct {
	Hour                  int     `json:"hour"`
	Minute                int     `json:"minute"`
	PredictedVehicleCount float64 `json:"predicted_vehicle_count"`
	TrafficLightID        int     `json:"traffic_light_id"`
}

type IntersectionInfoResponse struct {
	Statistics StatisticsResponse `json:"statistics"`
	Prediction PredictionResponse `json:"prediction"`
}
