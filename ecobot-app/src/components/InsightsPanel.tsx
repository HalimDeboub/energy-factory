import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Cloud, Zap, Sun } from "lucide-react";

const energyData = [
  { time: "00:00", usage: 45 },
  { time: "04:00", usage: 30 },
  { time: "08:00", usage: 65 },
  { time: "12:00", usage: 80 },
  { time: "16:00", usage: 75 },
  { time: "20:00", usage: 90 },
  { time: "23:59", usage: 55 },
];

export function InsightsPanel() {
  return (
    <div className="w-80 bg-white border-l border-gray-200 p-6 overflow-y-auto">
      <h2 className="text-xl mb-6 text-gray-800">Insights</h2>

      {/* CO₂ Saved */}
      <div className="mb-6 p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border border-green-200">
        <div className="flex items-center gap-2 mb-2">
          <Cloud className="size-5 text-green-600" />
          <h3 className="text-sm text-gray-700">CO₂ Saved</h3>
        </div>
        <p className="text-3xl text-green-700">120 kg</p>
        <p className="text-xs text-gray-600 mt-1">This month</p>
      </div>

      {/* Energy Usage Graph */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="size-5 text-yellow-600" />
          <h3 className="text-sm text-gray-700">Energy Usage</h3>
        </div>
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={energyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="time" 
              tick={{ fontSize: 10 }}
              stroke="#9ca3af"
            />
            <YAxis 
              tick={{ fontSize: 10 }}
              stroke="#9ca3af"
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '0.5rem'
              }}
            />
            <Line 
              type="monotone" 
              dataKey="usage" 
              stroke="#eab308" 
              strokeWidth={2}
              dot={{ fill: '#eab308', r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
        <p className="text-xs text-gray-600 mt-2">Daily consumption (kWh)</p>
      </div>

      {/* Solar Output */}
      <div className="p-4 bg-gradient-to-br from-amber-50 to-yellow-50 rounded-lg border border-amber-200">
        <div className="flex items-center gap-2 mb-2">
          <Sun className="size-5 text-amber-600" />
          <h3 className="text-sm text-gray-700">Solar Output</h3>
        </div>
        <p className="text-3xl text-amber-700">75%</p>
        <p className="text-xs text-gray-600 mt-1">Efficiency today</p>
        <div className="mt-3 bg-gray-200 rounded-full h-2">
          <div className="bg-amber-500 h-2 rounded-full" style={{ width: "75%" }}></div>
        </div>
      </div>
    </div>
  );
}
