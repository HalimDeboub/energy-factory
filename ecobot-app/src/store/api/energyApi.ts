import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

interface HealthResponse {
  status: string;
  timestamp?: string;
}

interface EnergyAnalysisRequest {
  query: string;
  keep_alive?: number;
}

interface EnergyAnalysisResponse {
  status: string;
  analysis: string;
  message?: string;
  data?: {
    production_MW?: number;
    consumption_MW?: number;
    nuclear_MW?: number;
    wind_MW?: number;
    solar_MW?: number;
    hydro_MW?: number;
    gas_MW?: number;
    carbon_intensity?: number;
    timestamp?: string;
  };
}

export const energyApi = createApi({
  reducerPath: "energyApi",
  baseQuery: fetchBaseQuery({
    baseUrl: "http://localhost:9000",
  }),
  tagTypes: ["Energy", "Health"],
  endpoints: (builder) => ({
    // GET /health
    getHealth: builder.query<HealthResponse, void>({
      query: () => "/health",
      providesTags: ["Health"],
    }),

    // POST /analyze-energy
    analyzeEnergy: builder.mutation<
      EnergyAnalysisResponse,
      EnergyAnalysisRequest
    >({
      query: (body) => ({
        url: "/analyze-energy",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Energy"],
    }),
  }),
});

export const { useGetHealthQuery, useAnalyzeEnergyMutation } = energyApi;
