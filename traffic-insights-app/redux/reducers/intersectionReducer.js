import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  intersections: {},
};

const intersection = createSlice({
    name: "intersection",
    initialState
});

export default intersection.reducer;
