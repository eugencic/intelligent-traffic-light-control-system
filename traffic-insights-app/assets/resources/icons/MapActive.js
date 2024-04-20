import * as React from "react";
import Svg, { Path } from "react-native-svg";
const MapActive = (props) => (
  <Svg
    xmlns="http://www.w3.org/2000/svg"
    width={24}
    height={24}
    fill="none"
    {...props}
  >
    <Path
      fill="#234635"
      d="M12.035 2a8.327 8.327 0 0 0-8.318 8.317c0 2.141 1.659 5.493 4.93 9.961a4.196 4.196 0 0 0 6.776 0c3.271-4.468 4.93-7.82 4.93-9.961A8.326 8.326 0 0 0 12.034 2Zm0 11.632a3.333 3.333 0 1 1 0-6.666 3.333 3.333 0 0 1 0 6.666Z"
    />
  </Svg>
);
export default MapActive;
