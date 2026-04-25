import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Cloud, Zap, Sun, Loader2 } from "lucide-react";
import {
  useGetEnergyHistoryQuery,
  useGetInsightsMetricsQuery,
} from "@/store/api/energyApi";

export function InsightsPanel() {
  // Fetch insights data from API
  const { data: metricsData, isLoading: metricsLoading } =
    useGetInsightsMetricsQuery("today");
  const { data: historyData, isLoading: historyLoading } =
    useGetEnergyHistoryQuery({
      period: "24h",
      interval: "1h",
    });

  const metrics = metricsData?.metrics;
  const energyData = historyData?.data || [];

  return (
    <div className="p-6 overflow-y-auto bg-white border-l border-gray-200 w-80">
      <h2 className="mb-6 text-xl text-gray-800">Insights</h2>

      {/* CO₂ Saved */}
      <div className="p-4 mb-6 border border-green-200 rounded-lg bg-gradient-to-br from-green-50 to-emerald-50">
        <div className="flex items-center gap-2 mb-2">
          <Cloud className="text-green-600 size-5" />
          <h3 className="text-sm text-gray-700">CO₂ Saved</h3>
        </div>
        {metricsLoading ? (
          <Loader2 className="text-green-600 size-8 animate-spin" />
        ) : (
          <>
            <p className="text-3xl text-green-700">
              {metrics?.co2_saved_kg.toFixed(0) || 0} kg
            </p>
            <p className="mt-1 text-xs text-gray-600">
              {metrics?.period === "today"
                ? "Today"
                : metrics?.period === "this_week"
                  ? "This week"
                  : "This month"}
            </p>
          </>
        )}
      </div>

      {/* Energy Usage Graph */}
      <div className="p-4 mb-6 border border-gray-200 rounded-lg bg-gray-50">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="text-yellow-600 size-5" />
          <h3 className="text-sm text-gray-700">Energy Usage</h3>
        </div>
        {historyLoading ? (
          <div className="h-[150px] flex items-center justify-center">
            <Loader2 className="text-yellow-600 size-8 animate-spin" />
          </div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={energyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 10 }}
                  stroke="#9ca3af"
                />
                <YAxis tick={{ fontSize: 10 }} stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "1px solid #e5e7eb",
                    borderRadius: "0.5rem",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="consommation"
                  stroke="#eab308"
                  strokeWidth={2}
                  dot={{ fill: "#eab308", r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
            <p className="mt-2 text-xs text-gray-600">
              Daily consumption (kWh)
            </p>
          </>
        )}
      </div>

      {/* Solar Output */}
      <div className="p-4 border rounded-lg bg-gradient-to-br from-amber-50 to-yellow-50 border-amber-200">
        <div className="flex items-center gap-2 mb-2">
          <Sun className="size-5 text-amber-600" />
          <h3 className="text-sm text-gray-700">Solar Output</h3>
        </div>
        {metricsLoading ? (
          <Loader2 className="size-8 text-amber-600 animate-spin" />
        ) : (
          <>
            <p className="text-3xl text-amber-700">
              {metrics?.solar_efficiency_percent.toFixed(0) || 0}%
            </p>
            <p className="mt-1 text-xs text-gray-600">Efficiency today</p>
            <div className="h-2 mt-3 bg-gray-200 rounded-full">
              <div
                className="h-2 transition-all duration-500 rounded-full bg-amber-500"
                style={{ width: `${metrics?.solar_efficiency_percent || 0}%` }}
              ></div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
