import React, { useEffect, useState, useReducer, Fragment } from "react";
import "./App.css";
import Data from "./Data";
import Reducer from "./reducres/Trafficlight";

function App() {
  const [trafficlights] = useReducer(Reducer, Data);
  const [trafficlightIndex, setTrafficlightIndex] = useState(0);
  const [redDuration, setRedDuration] = useState(20); // Initial values
  const [greenDuration, setGreenDuration] = useState(30); // Initial values
  const [timeRemaining, setTimeRemaining] = useState(redDuration);

  useEffect(() => {
    const fetchTrafficRules = async () => {
      try {
        const response = await fetch(
          "http://localhost:7000/get_traffic_rules/1"
        );
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Fetched traffic rules:", data);

        // Update durations if they are different from the current ones
        if (
          data.red_duration !== redDuration ||
          data.green_duration !== greenDuration
        ) {
          setRedDuration(data.red_duration);
          setGreenDuration(data.green_duration);
          // If the current traffic light is green, update time remaining
          if (trafficlightIndex === 1) {
            setTimeRemaining(data.green_duration);
          }
        }
      } catch (error) {
        console.error("Error fetching traffic rules:", error);
      }
    };

    // Fetch traffic rules every 20 seconds
    const interval = setInterval(fetchTrafficRules, 5000);

    return () => clearInterval(interval);
  }, [redDuration, greenDuration, trafficlightIndex]);

  useEffect(() => {
    const timer = setTimeout(() => {
      const nextIndex = (trafficlightIndex + 1) % trafficlights.length;
      setTrafficlightIndex(nextIndex);

      let nextDuration = redDuration;
      if (nextIndex === 1) {
        nextDuration = greenDuration;
      }
      setTimeRemaining(nextDuration);
    }, timeRemaining * 1000);

    return () => {
      clearTimeout(timer);
    };
  }, [
    trafficlightIndex,
    redDuration,
    greenDuration,
    trafficlights,
    timeRemaining,
  ]);

  return (
    <Fragment>
      {trafficlights.length > 0 && (
        <div className="container">
          <div className="trafficlight-box">
            {trafficlights.map((trafficlight) => (
              <div key={trafficlight.id} className="trafficlight-container">
                <p
                  id="trafficlight"
                  style={{
                    backgroundColor: trafficlight.light,
                    opacity: trafficlightIndex === trafficlight.id ? 1 : 0.3,
                    boxShadow:
                      trafficlightIndex === trafficlight.id
                        ? "1px 1px 10px rgba(204, 204, 204, 0.5), -1px -1px 10px rgba(204, 204, 204, 0.5)"
                        : null,
                  }}
                ></p>
                <p className="timer">
                  {trafficlightIndex === trafficlight.id &&
                    `${timeRemaining} s`}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </Fragment>
  );
}

export default App;
