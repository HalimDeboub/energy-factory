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

interface InsightsMetrics {
  co2_saved_kg: number;
  current_consumption_kwh: number;
  solar_efficiency_percent: number;
  period: string;
  timestamp: string;
}

interface InsightsMetricsResponse {
  status: string;
  metrics: InsightsMetrics;
}

interface EnergyDataPoint {
  time: string;
  consommation: number;
  nucleaire?: number;
  eolien?: number;
  solaire?: number;
  hydraulique?: number;
  gaz?: number;
  taux_co2?: number;
}

interface EnergyHistoryResponse {
  status: string;
  data: EnergyDataPoint[];
  period: string;
}

interface EnergyMix {
  nucleaire: number;
  eolien: number;
  solaire: number;
  hydraulique: number;
  gaz: number;
  total_production: number;
  consommation: number;
  taux_co2: number;
  timestamp: string;
}

interface EnergyMixResponse {
  status: string;
  mix: EnergyMix;
}

export const energyApi = createApi({
  reducerPath: "energyApi",
  baseQuery: fetchBaseQuery({
    baseUrl: "http://localhost:9000",
  }),
  tagTypes: ["Energy", "Health", "Insights"],
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
    // GET /insights/metrics - Get aggregated insights metrics
    getInsightsMetrics: builder.query<InsightsMetricsResponse, string | void>({
      query: (period = "today") => `/insights/metrics?period=${period}`,
      providesTags: ["Insights"],
    }),

    // GET /insights/history - Get historical energy data for graphs
    getEnergyHistory: builder.query<
      EnergyHistoryResponse,
      { period?: string; interval?: string }
    >({
      query: ({ period = "24h", interval = "1h" }) =>
        `/insights/history?period=${period}&interval=${interval}`,
      providesTags: ["Insights"],
    }),

    // GET /insights/energy-mix - Get current energy mix breakdown
    getEnergyMix: builder.query<EnergyMixResponse, void>({
      query: () => "/insights/energy-mix",
      providesTags: ["Insights"],
    }),
  }),
});

export const {
  useGetHealthQuery,
  useAnalyzeEnergyMutation,
  useGetEnergyHistoryQuery,
  useGetEnergyMixQuery,
  useGetInsightsMetricsQuery,
} = energyApi;
