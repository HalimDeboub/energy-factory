import { TrendingDown, Lightbulb, Battery, Home } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Link } from "react-router";

export function Dashboard() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl text-gray-800 mb-2">Welcome back!</h2>
        <p className="text-gray-600">Here's your energy transition overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-gray-600 flex items-center gap-2">
              <TrendingDown className="size-4 text-green-600" />
              Energy Reduction
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl text-gray-900">23%</p>
            <p className="text-xs text-gray-500 mt-1">vs. last month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-gray-600 flex items-center gap-2">
              <Lightbulb className="size-4 text-yellow-600" />
              Active Tips
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl text-gray-900">12</p>
            <p className="text-xs text-gray-500 mt-1">recommendations</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-gray-600 flex items-center gap-2">
              <Battery className="size-4 text-blue-600" />
              Solar Capacity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl text-gray-900">5.2 kW</p>
            <p className="text-xs text-gray-500 mt-1">installed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-gray-600 flex items-center gap-2">
              <Home className="size-4 text-purple-600" />
              Home Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl text-gray-900">B+</p>
            <p className="text-xs text-gray-500 mt-1">efficiency rating</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Start a Conversation</CardTitle>
            <CardDescription>
              Ask EcoBot about energy-saving tips, renewable energy options, or get personalized recommendations.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link to="/chat">
              <Button className="bg-green-600 hover:bg-green-700">
                Open Chat Assistant
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Insights</CardTitle>
            <CardDescription>
              Your home consumed 15% less energy this week compared to the average household.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start gap-2">
                <span className="text-green-600">•</span>
                <span>Peak usage between 6-9 PM</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-600">•</span>
                <span>Solar panels generated 42 kWh today</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-600">•</span>
                <span>LED upgrade saved 120 kWh this month</span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
