import React, { useEffect, useState, useLayoutEffect } from "react";
import {
  View,
  Text,
  SafeAreaView,
  StyleSheet,
  Dimensions,
  TextInput,
  Image,
  Modal,
  TouchableHighlight,
  Platform
} from "react-native";
import * as Location from "expo-location";
import SafeViewAndroid from "../components/SafeViewAndroid";
import MapView, { Marker } from "react-native-maps";
import MagnifyingGlass from "./../assets/resources/icons/MagnifyingGlass";
import { useFonts } from "expo-font";
import { mockupRestaurants, mockupTrafficLights } from "./../database/mockupData";

const windowWidth = Dimensions.get("window").width;

const MapScreen = ({ navigation }) => {
  useLayoutEffect(() => {
    navigation.setOptions({
      headerShown: false,
    });
  }, [navigation]);

  const [currentLocation, setCurrentLocation] = useState(null);
  const [initialRegion, setInitialRegion] = useState(null);
  const [initialAddress, setInitialAdress] = useState(null);
  const [trafficLights, setTrafficLights] = useState([]);
  const [filteredTrafficLights, setFilteredTrafficLights] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [selectedMarker, setSelectedMarker] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedTrafficLight, setSelectedTrafficLight] = useState(null);

  useEffect(() => {
    const getLocation = async () => {
      let { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") {
        console.log("Permission to access location was denied");
        return;
      }

      let location = await Location.getCurrentPositionAsync({});
      setCurrentLocation(location.coords);

      let address = await reverseGeocode(
        location.coords.latitude,
        location.coords.longitude
      );
      setInitialAdress(address);

      setInitialRegion({
        latitude: location.coords.latitude,
        longitude: location.coords.longitude,
        latitudeDelta: 0.005,
        longitudeDelta: 0.005,
      });

      setTrafficLights(mockupTrafficLights);
      setFilteredTrafficLights(mockupTrafficLights);
      setIsLoading(false);
    };

    getLocation();
  }, []);

  const reverseGeocode = async (latitude, longitude) => {
    try {
      let addressResponse = await Location.reverseGeocodeAsync({
        latitude,
        longitude,
      });
      let address = addressResponse[0].name + ", " + addressResponse[0].city;
      return address;
    } catch (error) {
      console.error("Error fetching address:", error);
      return "";
    }
  };

  const degreesToRadians = (degrees) => {
    return (degrees * Math.PI) / 180;
  };

  const getDistanceInKm = (lat1, lon1, lat2, lon2) => {
    const earthRadiusKm = 6371;

    const dLat = degreesToRadians(lat2 - lat1);
    const dLon = degreesToRadians(lon2 - lon1);

    lat1 = degreesToRadians(lat1);
    lat2 = degreesToRadians(lat2);

    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.sin(dLon / 2) * Math.sin(dLon / 2) * Math.cos(lat1) * Math.cos(lat2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return earthRadiusKm * c;
  };

  const renderMarkers = () => {
    return filteredTrafficLights.map((trafficLight) => (
      <Marker
        key={trafficLight.id}
        coordinate={{
          latitude: trafficLight.latitude,
          longitude: trafficLight.longitude,
        }}
        onPress={() => {
          setSelectedMarker(trafficLight.id);
          setSelectedTrafficLight(trafficLight);
          setModalVisible(true);
        }}
      >
        <Image
          source={require("./../assets/resources/images/map-pin.png")}
          style={styles.markerImage}
        />
        {/* {selectedMarker === restaurant.id ? (
          <View style={styles.selectedMarkerContainer}>
            <Image
              source={require("./../assets/resources/images/granier.png")}
              style={styles.selectedMarkerImage}
            />
          </View>
        ) : (
          <Image
            source={require("./../assets/resources/images/map-pin.png")}
            style={styles.markerImage}
          />
        )} */}
      </Marker>
    ));
  };

  const handleSearch = (query) => {
    const filtered = trafficLights.filter((trafficLight) =>
      trafficLight.name.toLowerCase().includes(query.toLowerCase())
    );

    setFilteredTrafficLights(filtered);
    setSearchQuery(query);
  };

  const renderModal = () => {
    if (!selectedTrafficLight) return null;

    const distanceKm = getDistanceInKm(
      currentLocation.latitude,
      currentLocation.longitude,
      selectedTrafficLight.latitude,
      selectedTrafficLight.longitude
    );

    let distanceDisplay =
      distanceKm < 1
        ? `${(distanceKm * 1000).toFixed(0)} m`
        : `${distanceKm.toFixed(2)} km`;

    return (
      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => {
          setModalVisible(false);
        }}
      >
        <TouchableHighlight
          style={styles.backdrop}
          activeOpacity={1}
          underlayColor="#00000000"
          onPress={() => {
            setModalVisible(false);
            setSelectedMarker(null);
            setSelectedTrafficLight(null);
          }}
        >
          <View style={styles.detailsView}>
            <View style={styles.details}>
              <View style={styles.detailsImageContainer}>
                <Image
                  source={require("./../assets/resources/images/traffic-light.png")}
                  style={styles.detailsImage}
                />
              </View>
              <View style={styles.detailsTextContainer}>
                <View>
                  <Text
                    style={[
                      styles.title,
                      {
                        fontSize:
                          Platform.OS === "android"
                            ? windowWidth * 0.05
                            : windowWidth * 0.04,
                      },
                    ]}
                  >
                    {selectedTrafficLight.name}
                  </Text>
                  <Text style={{ flexDirection: "row" }}>
                    <Text
                      style={[
                        styles.description,
                        {
                          fontSize:
                            Platform.OS === "android"
                              ? windowWidth * 0.03
                              : windowWidth * 0.03,
                        },
                        {
                          color:
                            selectedTrafficLight.status === "Open"
                              ? "green"
                              : "red",
                        },
                      ]}
                      numberOfLines={1}
                      adjustsFontSizeToFit
                    >
                      {selectedTrafficLight.status}
                    </Text>
                    <Text
                      style={[
                        styles.description,
                        {
                          fontSize:
                            Platform.OS === "android"
                              ? windowWidth * 0.03
                              : windowWidth * 0.025,
                        },
                      ]}
                    >
                      {" "}
                      • {distanceDisplay} from you
                    </Text>
                  </Text>
                </View>
              </View>
            </View>
            <TouchableHighlight
              style={{ ...styles.openButton, backgroundColor: "#234635" }}
              onPress={() => {
                navigation.navigate("MenuScreen", {
                  intersectionId: selectedTrafficLight,
                  distance: distanceDisplay,
                });
                setModalVisible(false);
                setSelectedMarker(null);
                setSelectedTrafficLight(null);
              }}
            >
              <Text style={styles.textStyle}>See Insights</Text>
            </TouchableHighlight>
          </View>
        </TouchableHighlight>
      </Modal>
    );
  };

  const [loaded] = useFonts({
    Inter: require("./../assets/resources/fonts/Inter-Regular.ttf"),
  });

  if (!loaded) {
    return null;
  }

  return (
    <SafeAreaView style={SafeViewAndroid.AndroidSafeArea}>
      <View style={{ flex: 1 }}>
        <View style={styles.searchContainer}>
          <View style={styles.searchBar}>
            <MagnifyingGlass />
            <TextInput
              style={styles.searchInput}
              placeholder="Type adress or name..."
              value={searchQuery}
              onChangeText={handleSearch}
            />
          </View>
        </View>
        {!isLoading && initialRegion && (
          <MapView
            style={{
              flex: 1,
              width: Dimensions.get("window").width,
              height: Dimensions.get("window").height,
            }}
            initialRegion={initialRegion}
            onLayout={() => {}}
          >
            {currentLocation && (
              <Marker
                pinColor={"grey"}
                coordinate={{
                  latitude: currentLocation.latitude,
                  longitude: currentLocation.longitude,
                }}
                title="Your Location"
                description={initialAddress}
              />
            )}
            {renderMarkers()}
          </MapView>
        )}
      </View>
      {renderModal()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  searchContainer: {
    position: "absolute",
    zIndex: 1,
    width: "100%",
    top: "5%",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 5,
  },
  searchBar: {
    width: "90%",
    flexDirection: "row",
    alignItems: "center",
    padding: 10,
    borderRadius: 50,
    backgroundColor: "white",
  },
  searchInput: {
    flex: 1,
    marginLeft: 10,
    height: 40,
    fontFamily: "Inter",
    fontSize: 15,
  },
  markerImage: {
    width: 35,
    height: 35,
  },
  selectedMarkerContainer: {
    width: 40,
    height: 40,
    borderRadius: 30,
    overflow: "hidden",
    borderWidth: 2,
    borderColor: "green",
  },
  selectedMarkerImage: {
    flex: 1,
    width: null,
    height: null,
  },
  detailsView: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    marginTop: "90%",
    width: "90%",
  },
  details: {
    width: "90%",
    backgroundColor: "white",
    borderRadius: 30,
    padding: 15,
    paddingVertical: 25,
    alignItems: "center",
    flexDirection: "row",
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  detailsTextContainer: {
    margin: "2%",
    marginLeft: "10%",
  },
  dynamicFontSize: {
    fontSize: windowWidth * 0.05,
  },
  title: {
    fontSize: 15,
    fontWeight: "bold",
  },
  description: {
    fontWeight: "bold",
    color: "gray",
  },
  detailsImageContainer: {
    width: 70,
    height: 70,
    borderRadius: 50,
    overflow: "hidden",
    borderWidth: 2,
    marginLeft: "5%",
  },
  detailsImage: {
    flex: 1,
    width: null,
    height: null,
  },
  openButton: {
    backgroundColor: "#234635",
    width: "40%",
    borderRadius: 20,
    padding: 10,
    elevation: 2,
    bottom: "4%",
  },
  backdrop: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  modalContent: {
    width: "90%",
    backgroundColor: "white",
    borderRadius: 30,
    padding: 15,
    paddingVertical: 25,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  textStyle: {
    color: "white",
    fontWeight: "bold",
    textAlign: "center",
  },
  modalText: {
    marginBottom: 15,
    textAlign: "center",
  },
});

export default MapScreen;
