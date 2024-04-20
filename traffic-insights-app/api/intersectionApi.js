import axios from "axios";

const API_BASE_URL = "http://192.168.0.2:9000";
// const API_BASE_URL = "http://10.0.2.2:9000";

export const fetchIntersectionInfo = async (id) => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/get_intersection_info?id=${id}`
    );
    
    return response.data;
  } catch (error) {
    console.error("Error fetching intersection information:", error);
    throw error;
  }
};
