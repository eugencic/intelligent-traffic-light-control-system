import { combineReducers } from "redux";
import intersectionReducer from "./intersectionReducer";

const rootReducer = combineReducers({
  intersections: intersectionReducer,
});

export default rootReducer;
