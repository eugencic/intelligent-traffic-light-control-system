import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  intersections: {},
};

const intersectionSlice = createSlice({
    name: "intersection",
    initialState
});

export default intersectionSlice.reducer;
