import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Download, Calendar } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";

const monthlyData = [
  { month: "Jan", consumption: 450, solar: 320, savings: 130 },
  { month: "Feb", consumption: 420, solar: 340, savings: 150 },
  { month: "Mar", consumption: 380, solar: 380, savings: 180 },
  { month: "Apr", consumption: 350, solar: 400, savings: 200 },
  { month: "May", consumption: 340, solar: 420, savings: 210 },
  { month: "Jun", consumption: 330, solar: 450, savings: 230 },
];

export function Reports() {
  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-3xl text-gray-800 mb-2">Energy Reports</h2>
          <p className="text-gray-600">Detailed analysis of your energy consumption and savings</p>
        </div>
        <Button className="bg-green-600 hover:bg-green-700">
          <Download className="size-4 mr-2" />
          Export Report
        </Button>
      </div>

      {/* Monthly Overview */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Monthly Energy Overview</CardTitle>
          <CardDescription>Consumption vs. Solar Generation (kWh)</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '0.5rem'
                }}
              />
              <Legend />
              <Bar dataKey="consumption" fill="#ef4444" name="Consumption" />
              <Bar dataKey="solar" fill="#22c55e" name="Solar Generated" />
              <Bar dataKey="savings" fill="#3b82f6" name="Net Savings" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-gray-600">Total Consumption</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl text-gray-900 mb-2">2,270 kWh</p>
            <p className="text-sm text-gray-600">Last 6 months</p>
            <div className="mt-4 flex items-center gap-2 text-sm text-green-600">
              <Calendar className="size-4" />
              <span>↓ 12% from previous period</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-gray-600">Solar Generated</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl text-gray-900 mb-2">2,310 kWh</p>
            <p className="text-sm text-gray-600">Last 6 months</p>
            <div className="mt-4 flex items-center gap-2 text-sm text-green-600">
              <Calendar className="size-4" />
              <span>↑ 8% from previous period</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-gray-600">CO₂ Offset</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl text-gray-900 mb-2">1,155 kg</p>
            <p className="text-sm text-gray-600">Last 6 months</p>
            <div className="mt-4 flex items-center gap-2 text-sm text-green-600">
              <Calendar className="size-4" />
              <span>Equivalent to 50 trees planted</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
