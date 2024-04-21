import axios from "axios";

const API_TRAFFIC_DATA_URL = "http://192.168.0.2:8000";
const API_TRAFFIC_INFO_URL = "http://192.168.0.2:9000";

export const fetchIntersectionData = async () => {
  try {
    const response = await axios.get(
      `${API_TRAFFIC_DATA_URL}/get_traffic_lights`
    );

    return response.data;
  } catch (error) {
    console.error("Error fetching intersection information:", error);
    throw error;
  }
};

export const fetchIntersectionInfo = async (id) => {
  try {
    const response = await axios.get(
      `${API_TRAFFIC_INFO_URL}/get_intersection_info?id=${id}`
    );
    
    return response.data;
  } catch (error) {
    console.error("Error fetching intersection information:", error);
    throw error;
  }
};
