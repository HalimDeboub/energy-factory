import { configureStore } from "@reduxjs/toolkit";
import { energyApi } from "../api/energyApi";

export const store = configureStore({
  reducer: {
    [energyApi.reducerPath]: energyApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(energyApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
