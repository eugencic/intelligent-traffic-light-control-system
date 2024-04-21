import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { NavigationContainer } from "@react-navigation/native";
import { Provider } from "react-redux";

import MapScreen from "./screens/MapScreen";
import DetailsScreen from "./screens/DetailsScreen";
import SettingsScreen from "./screens/SettingsScreen";

import MapActive from "./assets/resources/icons/MapActive";
import MapInactive from "./assets/resources/icons/MapInactive";
import SettingsActive from "./assets/resources/icons/SettingsActive";
import SettingsInactive from "./assets/resources/icons/SettingsInactive";

import store from "./redux/store";

const Tab = createBottomTabNavigator();

const Stack = createNativeStackNavigator();
const MapStack = () => {
  return (
    <Stack.Navigator initialRouteName="MapScreen">
      <Stack.Screen name="MapScreen" component={MapScreen} />
      <Stack.Screen name="DetailsScreen" component={DetailsScreen} />
    </Stack.Navigator>
  );
};

const SettingsStack = () => {
  return (
    <Stack.Navigator initialRouteName="SettingsScreen">
      <Stack.Screen name="SettingsScreen" component={SettingsScreen} />
    </Stack.Navigator>
  );
};

function MyTabs() {
  return (
    <Tab.Navigator
      initialRouteName="Map"
      screenOptions={{
        tabBarActiveTintColor: "#234635",
        headerShown: false,
      }}
      options={{ headerTitle: "false" }}
    >
      <Tab.Screen
        name="Map"
        component={MapStack}
        options={{
          tabBarLabel: "Maps",
          tabBarIcon: ({ focused }) =>
            focused ? <MapActive></MapActive> : <MapInactive></MapInactive>,
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsStack}
        options={{
          tabBarLabel: "Settings",
          tabBarIcon: ({ focused }) =>
            focused ? (
              <SettingsActive></SettingsActive>
            ) : (
              <SettingsInactive></SettingsInactive>
            ),
        }}
      />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <Provider store={store}>
      <NavigationContainer>
        <MyTabs />
      </NavigationContainer>
    </Provider>
  );
}
