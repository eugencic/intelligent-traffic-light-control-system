import React, { useEffect, useState, useLayoutEffect } from "react";
import {
  Dimensions,
  SafeAreaView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useNavigation } from "@react-navigation/native";

import { fetchIntersectionInfo } from "../api/intersectionApi";

const windowWidth = Dimensions.get("window").width;

const DetailsScreen = ({ route }) => {
  const { intersectionId } = route.params;
  const navigation = useNavigation();
  const [intersectionData, setIntersectionData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState("");

  useLayoutEffect(() => {
    navigation.setOptions({
      headerShown: false,
    });
  }, [navigation]);

  useEffect(() => {
    const fetchIntersectionData = async () => {
      try {
        const response = await fetchIntersectionInfo(intersectionId.id);
        setIntersectionData(response);
        setIsLoading(false);
      } catch (error) {
        console.error("Error fetching intersection data:", error);
        setIsLoading(false);
        alert(
          "Failed to fetch intersection data. Please check your network connection."
        );
      }
    };

    fetchIntersectionData();

    // Update current time every second
    const intervalId = setInterval(() => {
      const now = new Date();
      const hours = now.getHours().toString().padStart(2, "0");
      const minutes = now.getMinutes().toString().padStart(2, "0");
      setCurrentTime(`${hours}:${minutes}`);
    }, 1000);

    return () => {
      clearInterval(intervalId);
    };
  }, [intersectionId, navigation]);

  const renderStatistics = () => {
    const { statistics } = intersectionData;

    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Statistics</Text>
        <Text style={styles.label}>
          Mean Vehicle Count: {statistics.mean_vehicle_count}
        </Text>
        <Text style={styles.label}>
          Mean Pedestrian Count: {statistics.mean_pedestrian_count}
        </Text>
        {renderIntervals(
          "Peak Hours Intervals",
          statistics.peak_hours_intervals
        )}
        {renderIntervals(
          "Light Hours Intervals",
          statistics.light_hours_intervals
        )}
        {renderIntervals(
          "Normal Hours Intervals",
          statistics.normal_hours_intervals
        )}
      </View>
    );
  };

  const renderIntervals = (title, intervals) => {
    if (intervals.length > 0) {
      return (
        <>
          <Text style={styles.label}>{title}:</Text>
          {intervals.map((interval, index) => (
            <Text key={index} style={styles.value}>
              {formatInterval(interval)}
            </Text>
          ))}
        </>
      );
    }
    return null;
  };

  const formatInterval = (interval) => {
    const startTime = interval[0].split("T")[1].substring(0, 5);
    const endTime = interval[1].split("T")[1].substring(0, 5);

    if (startTime === endTime) {
      return startTime;
    } else {
      return `${startTime} to ${endTime}`;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {isLoading ? (
          <Text>Loading...</Text>
        ) : intersectionData ? (
          <>
            <Text
              style={styles.title}
            >{`Intersection Nr.${intersectionId.id}`}</Text>
            {renderStatistics()}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Tomorrow's Predictions</Text>
              <Text style={styles.label}>
                Time: {currentTime}{" "}
              </Text>
              <Text style={styles.label}>
                Vehicle Count:{" "}
                {intersectionData.prediction.predicted_vehicle_count}
              </Text>
            </View>
            <TouchableOpacity
              style={styles.button}
              onPress={() => navigation.goBack()}
            >
              <Text style={styles.buttonText}>Back to Map</Text>
            </TouchableOpacity>
          </>
        ) : (
          <Text>No data available for this intersection.</Text>
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#ECEFF1",
  },
  content: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    width: "100%",
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 20,
  },
  section: {
    backgroundColor: "#FFFFFF",
    padding: 20,
    borderRadius: 10,
    marginBottom: 20,
    width: "100%",
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "bold",
    marginBottom: 10,
  },
  label: {
    fontSize: 16,
    fontWeight: "bold",
    marginBottom: 5,
  },
  value: {
    fontSize: 16,
    marginBottom: 5,
  },
  button: {
    backgroundColor: "#234635",
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 25,
    marginTop: 20,
  },
  buttonText: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#FFFFFF",
  },
});

export default DetailsScreen;
